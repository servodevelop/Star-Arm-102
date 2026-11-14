use std::collections::HashMap;
use std::time::Duration;

use smart_servo_core::{
    AngleReliability, AngleSample, LossTracker, Result, SerialBus, SerialBusConfig, ServoId,
    SmartServoController, SmartServoError,
};

use crate::protocol;
pub use crate::protocol::ServoMonitor;

pub struct FashionStarController {
    bus: SerialBus,
    filters: HashMap<ServoId, AngleReliability>,
    zero_confirm_samples: u16,
    loss_tracker: LossTracker,
    last_monitors: HashMap<ServoId, ServoMonitor>,
}

impl FashionStarController {
    pub fn open(port: impl Into<String>, baudrate: u32) -> Result<Self> {
        Ok(Self {
            bus: SerialBus::open(SerialBusConfig::new(port, baudrate))?,
            filters: HashMap::new(),
            zero_confirm_samples: 30,
            loss_tracker: LossTracker::default(),
            last_monitors: HashMap::new(),
        })
    }

    /// Applies to existing and future filters. Returns the previous setting.
    pub fn set_zero_confirm_samples(&mut self, samples: u16) -> u16 {
        let previous = self.zero_confirm_samples;
        self.zero_confirm_samples = samples.max(1);
        for filter in self.filters.values_mut() {
            filter.config.zero_confirm_samples = self.zero_confirm_samples;
            filter.state.zero_candidate_count = 0;
        }
        previous
    }

    pub fn set_loss_threshold(&mut self, threshold: u32) {
        self.loss_tracker = LossTracker::new(threshold);
    }

    pub fn read_raw_angle(&mut self, id: ServoId, multi_turn: bool) -> Result<f32> {
        self.bus.clear()?;
        self.bus
            .write_all(&protocol::encode_query_angle(id, multi_turn)?)?;
        let data = match self.bus.read_until(true, |buf| {
            !protocol::parse_response_stream(buf).packets.is_empty()
        }) {
            Ok(d) => d,
            Err(SmartServoError::Timeout) => {
                self.loss_tracker.record_miss(id)?;
                return Err(SmartServoError::Timeout);
            }
            Err(e) => return Err(e),
        };
        let report = protocol::parse_response_stream(&data);
        if report.packets.is_empty() {
            if let Some(err) = report.errors.into_iter().next() {
                return Err(err);
            }
        }
        for packet in report.packets {
            if let Ok((reply_id, angle)) = protocol::decode_angle(&packet, multi_turn) {
                if reply_id == id {
                    self.loss_tracker.record_ok(id);
                    return Ok(angle);
                }
            }
        }
        self.loss_tracker.record_miss(id)?;
        Err(SmartServoError::Timeout)
    }

    pub fn query_monitor(&mut self, id: ServoId) -> Result<ServoMonitor> {
        self.bus.clear()?;
        self.bus.write_all(&protocol::encode_query_monitor(id)?)?;
        let data = match self.bus.read_until(true, |buf| {
            !protocol::parse_response_stream(buf).packets.is_empty()
        }) {
            Ok(d) => d,
            Err(SmartServoError::Timeout) => {
                self.loss_tracker.record_miss(id)?;
                return Err(SmartServoError::Timeout);
            }
            Err(e) => return Err(e),
        };
        let report = protocol::parse_response_stream(&data);
        if report.packets.is_empty() {
            if let Some(err) = report.errors.into_iter().next() {
                return Err(err);
            }
        }
        for packet in report.packets {
            if let Ok(mut sample) = protocol::decode_monitor(&packet) {
                if sample.id == id {
                    let filter = self.filters.entry(id).or_default();
        filter.config.zero_confirm_samples = self.zero_confirm_samples;
                    let (filtered, angle_ok) = filter.filter(sample.angle_deg);
                    sample.angle_deg = filtered;
                    sample.reliable = angle_ok;
                    self.loss_tracker.record_ok(id);
                    self.last_monitors.insert(id, sample);
                    return Ok(sample);
                }
            }
        }
        self.loss_tracker.record_miss(id)?;
        Err(SmartServoError::Timeout)
    }

    /// Send one sync-monitor command (code 25) to query all `ids` at once.
    ///
    /// Uses `idle_gap = false` so that silence between individual servo
    /// responses does not trigger early exit — we wait for all N packets or
    /// the overall timeout.
    pub fn sync_monitor(
        &mut self,
        ids: &[ServoId],
    ) -> Result<HashMap<ServoId, Option<ServoMonitor>>> {
        self.bus.clear()?;
        self.bus.write_all(&protocol::encode_sync_monitor(ids)?)?;
        let expected = ids.len();
        let data = match self.bus.read_until(false, |buf| {
            protocol::parse_response_stream(buf).packets.len() >= expected
        }) {
            Ok(d) => d,
            Err(SmartServoError::Timeout) => {
                for &id in ids {
                    self.loss_tracker.record_miss(id)?;
                }
                // all use last known value, marked unreliable
                let result = ids
                    .iter()
                    .map(|&id| {
                        let held = self.last_monitors.get(&id).map(|m| {
                            let mut stale = *m;
                            stale.reliable = false;
                            stale
                        });
                        (id, held)
                    })
                    .collect();
                return Ok(result);
            }
            Err(e) => return Err(e),
        };

        let report = protocol::parse_response_stream(&data);

        let mut got: HashMap<ServoId, ServoMonitor> = HashMap::new();
        for packet in report.packets {
            if let Ok(mut m) = protocol::decode_monitor(&packet) {
                let filter = self.filters.entry(m.id).or_default();
                filter.config.zero_confirm_samples = self.zero_confirm_samples;
                let (filtered, angle_ok) = filter.filter(m.angle_deg);
                m.angle_deg = filtered;
                m.reliable = angle_ok;
                self.loss_tracker.record_ok(m.id);
                self.last_monitors.insert(m.id, m);
                got.insert(m.id, m);
            }
        }

        let mut result: HashMap<ServoId, Option<ServoMonitor>> = HashMap::new();
        for &id in ids {
            if let Some(m) = got.remove(&id) {
                result.insert(id, Some(m));
            } else {
                self.loss_tracker.record_miss(id)?;
                let held = self.last_monitors.get(&id).map(|m| {
                    let mut stale = *m;
                    stale.reliable = false;
                    stale
                });
                result.insert(id, held);
            }
        }

        Ok(result)
    }

    pub fn read_angle_pair(&mut self, id: ServoId, multi_turn: bool) -> Result<AngleSample> {
        let raw = self.read_raw_angle(id, multi_turn)?;
        let filter = self.filters.entry(id).or_default();
        filter.config.zero_confirm_samples = self.zero_confirm_samples;
        let (filtered, reliable) = filter.filter(raw);
        Ok(AngleSample {
            raw_deg: raw,
            filtered_deg: filtered,
            reliable,
        })
    }

    pub fn reset_multi_turn(&mut self, id: ServoId) -> Result<()> {
        self.bus
            .write_all(&protocol::encode_reset_multi_turn(id)?)?;
        Ok(())
    }

    pub fn set_origin_point(&mut self, id: ServoId) -> Result<()> {
        self.bus
            .write_all(&protocol::encode_set_origin_point(id)?)?;
        Ok(())
    }

    pub fn set_damping(&mut self, id: ServoId, power: u16) -> Result<()> {
        self.bus.write_all(&protocol::encode_set_damping(id, power)?)?;
        Ok(())
    }

    pub fn set_stop_mode(&mut self, id: ServoId, mode: u8, power: u16) -> Result<()> {
        self.bus
            .write_all(&protocol::encode_set_stop_mode(id, mode, power)?)?;
        Ok(())
    }

    pub fn set_timeout(&mut self, timeout: Duration) {
        self.bus.set_timeout(timeout);
    }

    pub fn filter_timeout_sample(&mut self, id: ServoId) -> Option<AngleSample> {
        let filter = self.filters.entry(id).or_default();
        filter.config.zero_confirm_samples = self.zero_confirm_samples;
        filter.state.last_good_deg.map(|last| AngleSample {
            raw_deg: 0.0,
            filtered_deg: last,
            reliable: false,
        })
    }
}

impl SmartServoController for FashionStarController {
    fn ping(&mut self, id: ServoId) -> Result<bool> {
        self.bus.clear()?;
        self.bus.write_all(&protocol::encode_ping(id)?)?;
        let data = match self.bus.read_until(true, |buf| {
            !protocol::parse_response_stream(buf).packets.is_empty()
        }) {
            Ok(data) => data,
            Err(SmartServoError::Timeout) => return Ok(false),
            Err(err) => return Err(err),
        };
        let report = protocol::parse_response_stream(&data);
        if report.packets.is_empty() {
            if let Some(err) = report.errors.into_iter().next() {
                return Err(err);
            }
        }
        Ok(report
            .packets
            .iter()
            .any(|packet| protocol::decode_ping(packet) == Some(id)))
    }

    fn read_angle(&mut self, id: ServoId, multi_turn: bool) -> Result<AngleSample> {
        self.read_angle_pair(id, multi_turn)
    }

    fn set_angle(
        &mut self,
        id: ServoId,
        angle_deg: f32,
        multi_turn: bool,
        interval_ms: Option<u32>,
    ) -> Result<()> {
        let packet = protocol::encode_set_angle(id, angle_deg, multi_turn, interval_ms)?;
        self.bus.write_all(&packet)?;
        Ok(())
    }
}
