use std::sync::{Mutex, MutexGuard};

use pyo3::exceptions::{PyRuntimeError, PyValueError};
use pyo3::prelude::*;
use smart_servo_core::{AngleSample, ServoId, SmartServoController, SmartServoError};
use smart_servo_vendor_fashionstar::{FashionStarController, ServoMonitor};

fn py_bus_err(err: SmartServoError) -> PyErr {
    PyRuntimeError::new_err(err.to_string())
}

fn py_closed_err() -> PyErr {
    PyRuntimeError::new_err("servo bus is closed")
}

fn check_servo_id(servo_id: u8) -> ServoId {
    servo_id
}

fn checked_interval(interval_ms: u32, multi_turn: bool) -> PyResult<u32> {
    let max = if multi_turn {
        4_096_000
    } else {
        u16::MAX as u32
    };
    if interval_ms > max {
        return Err(PyValueError::new_err(format!(
            "interval_ms must be in range 0..{}",
            max
        )));
    }
    Ok(interval_ms)
}

fn finite_angle(angle_deg: f32) -> PyResult<f32> {
    if !angle_deg.is_finite() {
        return Err(PyValueError::new_err("angle_deg must be finite"));
    }
    Ok(angle_deg)
}

#[pyclass(
    name = "ServoMonitor",
    module = "motorbridge_smart_servo",
    frozen,
    skip_from_py_object
)]
#[derive(Debug, Clone, Copy)]
pub struct PyServoMonitor {
    #[pyo3(get)]
    pub id: u8,
    #[pyo3(get)]
    pub voltage_mv: u16,
    #[pyo3(get)]
    pub current_ma: u16,
    #[pyo3(get)]
    pub power_mw: u16,
    #[pyo3(get)]
    pub temp_raw: u16,
    #[pyo3(get)]
    pub status: u8,
    #[pyo3(get)]
    pub angle_deg: f32,
    #[pyo3(get)]
    pub turn: i16,
    #[pyo3(get)]
    pub reliable: bool,
}

impl From<ServoMonitor> for PyServoMonitor {
    fn from(m: ServoMonitor) -> Self {
        Self {
            id: m.id,
            voltage_mv: m.voltage_mv,
            current_ma: m.current_ma,
            power_mw: m.power_mw,
            temp_raw: m.temp_raw,
            status: m.status,
            angle_deg: m.angle_deg,
            turn: m.turn,
            reliable: m.reliable,
        }
    }
}

#[pymethods]
impl PyServoMonitor {
    fn __repr__(&self) -> String {
        format!(
            "ServoMonitor(id={}, angle_deg={:.3}, voltage_mv={}, \
             current_ma={}, power_mw={}, temp_raw={}, status={:#04x}, turn={}, reliable={})",
            self.id,
            self.angle_deg,
            self.voltage_mv,
            self.current_ma,
            self.power_mw,
            self.temp_raw,
            self.status,
            self.turn,
            self.reliable,
        )
    }
}

#[pyclass(
    name = "AngleSample",
    module = "motorbridge_smart_servo",
    frozen,
    skip_from_py_object
)]
#[derive(Debug, Clone, Copy)]
pub struct PyAngleSample {
    #[pyo3(get)]
    raw_deg: f32,
    #[pyo3(get)]
    filtered_deg: f32,
    #[pyo3(get)]
    reliable: bool,
}

impl From<AngleSample> for PyAngleSample {
    fn from(sample: AngleSample) -> Self {
        Self {
            raw_deg: sample.raw_deg,
            filtered_deg: sample.filtered_deg,
            reliable: sample.reliable,
        }
    }
}

#[pymethods]
impl PyAngleSample {
    fn __repr__(&self) -> String {
        format!(
            "AngleSample(raw_deg={:.3}, filtered_deg={:.3}, reliable={})",
            self.raw_deg, self.filtered_deg, self.reliable
        )
    }
}

#[pyclass(name = "FashionStarServo", module = "motorbridge_smart_servo._native")]
pub struct PyFashionStarServo {
    inner: Mutex<Option<FashionStarController>>,
}

impl PyFashionStarServo {
    fn controller(&self) -> PyResult<MutexGuard<'_, Option<FashionStarController>>> {
        self.inner
            .lock()
            .map_err(|_| PyRuntimeError::new_err("servo bus lock poisoned"))
    }

    fn with_controller<T>(
        &self,
        f: impl FnOnce(&mut FashionStarController) -> PyResult<T>,
    ) -> PyResult<T> {
        let mut guard = self.controller()?;
        let controller = guard.as_mut().ok_or_else(py_closed_err)?;
        f(controller)
    }
}

#[pymethods]
impl PyFashionStarServo {
    #[new]
    #[pyo3(signature = (port, baudrate = 1_000_000))]
    fn new(port: String, baudrate: u32) -> PyResult<Self> {
        let controller = FashionStarController::open(port, baudrate).map_err(py_bus_err)?;
        Ok(Self {
            inner: Mutex::new(Some(controller)),
        })
    }

    #[getter]
    fn is_open(&self) -> PyResult<bool> {
        Ok(self.controller()?.is_some())
    }

    fn close(&self) -> PyResult<()> {
        *self.controller()? = None;
        Ok(())
    }

    fn ping(&self, py: Python<'_>, servo_id: u8) -> PyResult<bool> {
        let servo_id = check_servo_id(servo_id);
        py.detach(|| {
            self.with_controller(|controller| controller.ping(servo_id).map_err(py_bus_err))
        })
    }

    #[pyo3(signature = (max_id = 253))]
    fn scan(&self, py: Python<'_>, max_id: u8) -> PyResult<Vec<u8>> {
        py.detach(|| {
            let mut online = Vec::new();
            self.with_controller(|controller| {
                for servo_id in 0..=max_id {
                    if controller.ping(servo_id).map_err(py_bus_err)? {
                        online.push(servo_id);
                    }
                }
                Ok(online)
            })
        })
    }

    #[pyo3(signature = (servo_id, multi_turn = true))]
    fn read_angle(
        &self,
        py: Python<'_>,
        servo_id: u8,
        multi_turn: bool,
    ) -> PyResult<PyAngleSample> {
        let servo_id = check_servo_id(servo_id);
        py.detach(|| {
            self.with_controller(
                |controller| match controller.read_angle(servo_id, multi_turn) {
                    Ok(sample) => Ok(sample.into()),
                    Err(SmartServoError::Timeout) => controller
                        .filter_timeout_sample(servo_id)
                        .map(PyAngleSample::from)
                        .ok_or_else(|| py_bus_err(SmartServoError::Timeout)),
                    Err(err) => Err(py_bus_err(err)),
                },
            )
        })
    }

    #[pyo3(signature = (servo_id, multi_turn = true))]
    fn read_raw_angle(&self, py: Python<'_>, servo_id: u8, multi_turn: bool) -> PyResult<f32> {
        Ok(self.read_angle(py, servo_id, multi_turn)?.raw_deg)
    }

    #[pyo3(signature = (servo_id, multi_turn = true))]
    fn read_filtered_angle(&self, py: Python<'_>, servo_id: u8, multi_turn: bool) -> PyResult<f32> {
        Ok(self.read_angle(py, servo_id, multi_turn)?.filtered_deg)
    }

    #[pyo3(signature = (servo_id, angle_deg, multi_turn = false, interval_ms = 0))]
    fn set_angle(
        &self,
        py: Python<'_>,
        servo_id: u8,
        angle_deg: f32,
        multi_turn: bool,
        interval_ms: u32,
    ) -> PyResult<()> {
        let servo_id = check_servo_id(servo_id);
        let angle_deg = finite_angle(angle_deg)?;
        let interval_ms = checked_interval(interval_ms, multi_turn)?;
        py.detach(|| {
            self.with_controller(|controller| {
                controller
                    .set_angle(servo_id, angle_deg, multi_turn, Some(interval_ms))
                    .map_err(py_bus_err)
            })
        })
    }

    #[pyo3(signature = (servo_id))]
    fn reset_multi_turn(&self, py: Python<'_>, servo_id: u8) -> PyResult<()> {
        let servo_id = check_servo_id(servo_id);
        py.detach(|| self.with_controller(|c| c.reset_multi_turn(servo_id).map_err(py_bus_err)))
    }

    #[pyo3(signature = (servo_id))]
    fn set_origin_point(&self, py: Python<'_>, servo_id: u8) -> PyResult<()> {
        let servo_id = check_servo_id(servo_id);
        py.detach(|| self.with_controller(|c| c.set_origin_point(servo_id).map_err(py_bus_err)))
    }

    #[pyo3(signature = (servo_id, power))]
    fn set_damping(&self, py: Python<'_>, servo_id: u8, power: u16) -> PyResult<()> {
        if servo_id > 253 {
            return Err(PyValueError::new_err("servo_id must be in range 0..253"));
        }
        py.detach(|| self.with_controller(|c| c.set_damping(servo_id, power).map_err(py_bus_err)))
    }

    #[pyo3(signature = (servo_id, mode, power))]
    fn set_stop_mode(&self, py: Python<'_>, servo_id: u8, mode: u8, power: u16) -> PyResult<()> {
        let servo_id = check_servo_id(servo_id);
        py.detach(|| {
            self.with_controller(|c| c.set_stop_mode(servo_id, mode, power).map_err(py_bus_err))
        })
    }

    #[pyo3(signature = (servo_id, angle_deg, multi_turn = false, interval_ms = 0))]
    fn move_to(
        &self,
        py: Python<'_>,
        servo_id: u8,
        angle_deg: f32,
        multi_turn: bool,
        interval_ms: u32,
    ) -> PyResult<()> {
        self.set_angle(py, servo_id, angle_deg, multi_turn, interval_ms)
    }

    /// Set zero-jump confirmation count; return previous value.
    #[pyo3(signature = (samples))]
    fn set_zero_confirm_samples(&self, samples: u16) -> PyResult<u16> {
        if samples == 0 {
            return Err(pyo3::exceptions::PyValueError::new_err("samples must be positive"));
        }
        self.with_controller(|c| Ok(c.set_zero_confirm_samples(samples)))
    }

    #[pyo3(signature = (threshold))]
    fn set_loss_threshold(&self, threshold: u32) -> PyResult<()> {
        self.with_controller(|c| {
            c.set_loss_threshold(threshold);
            Ok(())
        })
    }

    /// Send one sync-monitor command to all `servo_ids` at once.
    ///
    /// Returns a `dict[int, ServoMonitor | None]`:
    /// - `ServoMonitor` for each servo that responded.
    /// - `None` for each servo that did not respond this cycle.
    ///
    /// Raises `RuntimeError` if any servo's consecutive miss count hits the
    /// configured threshold.
    #[pyo3(signature = (servo_ids))]
    fn sync_monitor(&self, py: Python<'_>, servo_ids: Vec<u8>) -> PyResult<Py<PyAny>> {
        let result =
            py.detach(|| self.with_controller(|c| c.sync_monitor(&servo_ids).map_err(py_bus_err)))?;
        let dict = pyo3::types::PyDict::new(py);
        for (id, opt) in result {
            match opt {
                Some(m) => dict.set_item(id, Py::new(py, PyServoMonitor::from(m))?)?,
                None => dict.set_item(id, py.None())?,
            }
        }
        Ok(dict.unbind().into())
    }
}

#[pymodule]
fn _native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyAngleSample>()?;
    m.add_class::<PyServoMonitor>()?;
    m.add_class::<PyFashionStarServo>()?;
    Ok(())
}
