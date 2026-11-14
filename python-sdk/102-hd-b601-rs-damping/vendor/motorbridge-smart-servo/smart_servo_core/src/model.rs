pub type ServoId = u8;

#[derive(Debug, Clone, Copy, Default)]
pub struct SmartServoInfo {
    pub id: ServoId,
    pub online: bool,
    pub angle_deg: Option<f32>,
}
