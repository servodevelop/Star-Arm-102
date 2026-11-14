use crate::{Result, ServoId};

#[derive(Debug, Clone, Copy)]
pub struct AngleSample {
    pub raw_deg: f32,
    pub filtered_deg: f32,
    pub reliable: bool,
}

pub trait SmartServoController {
    fn ping(&mut self, id: ServoId) -> Result<bool>;
    fn read_angle(&mut self, id: ServoId, multi_turn: bool) -> Result<AngleSample>;
    fn set_angle(
        &mut self,
        id: ServoId,
        angle_deg: f32,
        multi_turn: bool,
        interval_ms: Option<u32>,
    ) -> Result<()>;
}
