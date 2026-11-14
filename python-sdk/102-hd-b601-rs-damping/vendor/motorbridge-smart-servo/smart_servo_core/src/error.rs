use thiserror::Error;

pub type Result<T> = std::result::Result<T, SmartServoError>;

#[derive(Debug, Error)]
pub enum SmartServoError {
    #[error("serial error: {0}")]
    Serial(#[from] serialport::Error),
    #[error("io error: {0}")]
    Io(#[from] std::io::Error),
    #[error("timeout")]
    Timeout,
    #[error("checksum mismatch: code={code} expected={expected:#04x} got={got:#04x}")]
    ChecksumMismatch { code: u8, expected: u8, got: u8 },
    #[error("protocol error: {0}")]
    Protocol(String),
    #[error("unsupported: {0}")]
    Unsupported(String),
    #[error("servo {id} lost {count} consecutive responses")]
    ConsecutiveLoss { id: u8, count: u32 },
}
