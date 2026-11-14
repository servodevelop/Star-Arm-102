use std::collections::HashMap;

use crate::{Result, ServoId, SmartServoError};

/// Per-servo consecutive response loss tracker.
///
/// Calls [`record_ok`] on success and [`record_miss`] on timeout.
/// Returns [`SmartServoError::ConsecutiveLoss`] when a servo's consecutive
/// miss count reaches `threshold`. A `threshold` of `0` disables the check.
#[derive(Debug, Clone)]
pub struct LossTracker {
    counts: HashMap<ServoId, u32>,
    threshold: u32,
}

impl LossTracker {
    pub fn new(threshold: u32) -> Self {
        Self {
            counts: HashMap::new(),
            threshold,
        }
    }

    /// Reset miss counter for `id` after a successful response.
    pub fn record_ok(&mut self, id: ServoId) {
        self.counts.insert(id, 0);
    }

    /// Increment miss counter for `id`. Returns `Err(ConsecutiveLoss)` when
    /// `threshold > 0` and the count reaches the threshold.
    pub fn record_miss(&mut self, id: ServoId) -> Result<()> {
        let count = self.counts.entry(id).or_insert(0);
        *count += 1;
        if self.threshold > 0 && *count >= self.threshold {
            Err(SmartServoError::ConsecutiveLoss { id, count: *count })
        } else {
            Ok(())
        }
    }

    /// Current consecutive miss count for `id`.
    pub fn miss_count(&self, id: ServoId) -> u32 {
        self.counts.get(&id).copied().unwrap_or(0)
    }
}

impl Default for LossTracker {
    /// Default threshold: 20 consecutive misses.
    fn default() -> Self {
        Self::new(20)
    }
}
