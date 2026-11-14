use std::io::{Read, Write};
use std::time::{Duration, Instant};

use serialport::SerialPort;

use crate::{Result, SmartServoError};

#[derive(Debug, Clone)]
pub struct SerialBusConfig {
    pub port: String,
    pub baudrate: u32,
    pub timeout: Duration,
    pub read_timeout: Duration,
}

impl SerialBusConfig {
    pub fn new(port: impl Into<String>, baudrate: u32) -> Self {
        Self {
            port: port.into(),
            baudrate,
            timeout: Duration::from_millis(100),
            read_timeout: Duration::from_millis(10),
        }
    }
}

pub struct SerialBus {
    port: Box<dyn SerialPort>,
    timeout: Duration,
}

impl SerialBus {
    pub fn open(config: SerialBusConfig) -> Result<Self> {
        let port = serialport::new(&config.port, config.baudrate)
            .timeout(config.read_timeout)
            .open()?;
        Ok(Self {
            port,
            timeout: config.timeout,
        })
    }

    pub fn write_all(&mut self, data: &[u8]) -> Result<()> {
        self.port.write_all(data)?;
        self.port.flush()?;
        Ok(())
    }

    pub fn clear(&mut self) -> Result<()> {
        self.port.clear(serialport::ClearBuffer::All)?;
        Ok(())
    }

    pub fn set_timeout(&mut self, timeout: Duration) {
        self.timeout = timeout;
    }

    /// Read bytes until `done(&buf)` returns `true`, or `self.timeout` elapses.
    ///
    /// When `idle_gap` is `true`, also stops if a `TimedOut` occurs after
    /// receiving data (useful for single-packet reads where silence means the
    /// response is complete). Set `idle_gap` to `false` for multi-packet reads
    /// (e.g. sync_monitor) where silence between packets is expected.
    pub fn read_until<F>(&mut self, idle_gap: bool, mut done: F) -> Result<Vec<u8>>
    where
        F: FnMut(&[u8]) -> bool,
    {
        let started = Instant::now();
        let mut out = Vec::new();
        let mut scratch = [0_u8; 256];

        while started.elapsed() < self.timeout {
            match self.port.read(&mut scratch) {
                Ok(n) if n > 0 => {
                    out.extend_from_slice(&scratch[..n]);
                    if done(&out) {
                        break;
                    }
                }
                Err(e) if e.kind() == std::io::ErrorKind::TimedOut => {
                    if idle_gap && !out.is_empty() {
                        break;
                    }
                }
                Ok(_) => {}
                Err(e) => return Err(e.into()),
            }
        }

        if out.is_empty() {
            return Err(SmartServoError::Timeout);
        }
        Ok(out)
    }
}
