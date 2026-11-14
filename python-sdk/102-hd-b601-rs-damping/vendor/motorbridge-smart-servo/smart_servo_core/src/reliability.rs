#[derive(Debug, Clone, Copy)]
pub struct AngleReliabilityConfig {
    pub zero_eps_deg: f32,
    pub zero_confirm_samples: u16,
    /// Readings whose magnitude exceeds this value are treated as unreliable
    /// power-on garbage and held back just like near-zero glitches.
    /// Defaults to 3,686,400° (FashionStar ±1024-turn protocol limit).
    pub valid_range_deg: f32,
}

impl Default for AngleReliabilityConfig {
    fn default() -> Self {
        Self {
            zero_eps_deg: 0.2,
            zero_confirm_samples: 30,
            valid_range_deg: 3_686_400.0,
        }
    }
}

#[derive(Debug, Clone, Copy, Default)]
pub struct AngleReliabilityState {
    pub last_good_deg: Option<f32>,
    pub zero_candidate_count: u16,
}

#[derive(Debug, Clone, Default)]
pub struct AngleReliability {
    pub config: AngleReliabilityConfig,
    pub state: AngleReliabilityState,
}

impl AngleReliability {
    pub fn filter(&mut self, raw_deg: f32) -> (f32, bool) {
        let is_near_zero = raw_deg.abs() <= self.config.zero_eps_deg;
        let is_in_range = raw_deg.abs() <= self.config.valid_range_deg;

        let Some(last_good) = self.state.last_good_deg else {
            // First reading ever.
            if !is_in_range {
                // Out-of-range garbage before any good reading — no value to hold.
                return (0.0, false);
            }
            self.state.last_good_deg = Some(raw_deg);
            return (raw_deg, true);
        };

        if !is_in_range {
            // Out-of-range (e.g. power-on firmware garbage) — hold last good.
            self.state.zero_candidate_count = 0;
            return (last_good, false);
        }

        // Already accepted near-zero readings must stay accepted. Otherwise
        // a stationary zero is suppressed for 29 out of every 30 samples.
        if is_near_zero && last_good.abs() <= self.config.zero_eps_deg {
            self.state.zero_candidate_count = 0;
            self.state.last_good_deg = Some(raw_deg);
            return (raw_deg, true);
        }

        if is_near_zero {
            self.state.zero_candidate_count = self.state.zero_candidate_count.saturating_add(1);
            if self.state.zero_candidate_count >= self.config.zero_confirm_samples {
                self.state.zero_candidate_count = 0;
                self.state.last_good_deg = Some(raw_deg);
                return (raw_deg, true);
            }
            return (last_good, false);
        }

        self.state.zero_candidate_count = 0;
        self.state.last_good_deg = Some(raw_deg);
        (raw_deg, true)
    }
}

#[cfg(test)]
mod tests {
    use super::AngleReliability;

    #[test]
    fn accepted_zero_stays_reliable() {
        let mut filter = AngleReliability::default();
        for _ in 0..90 {
            assert_eq!(filter.filter(0.0), (0.0, true));
        }
    }

    #[test]
    fn confirmed_zero_stays_reliable() {
        let mut filter = AngleReliability::default();
        filter.config.zero_confirm_samples = 3;
        assert_eq!(filter.filter(10.0), (10.0, true));
        assert_eq!(filter.filter(0.0), (10.0, false));
        assert_eq!(filter.filter(0.0), (10.0, false));
        for _ in 0..90 {
            assert_eq!(filter.filter(0.0), (0.0, true));
        }
    }

    #[test]
    fn startup_out_of_range_returns_zero_unreliable() {
        let mut filter = AngleReliability::default();
        assert_eq!(filter.filter(-23_592_960.0), (0.0, false));
    }

    #[test]
    fn out_of_range_after_good_holds_last_good() {
        let mut filter = AngleReliability::default();
        filter.config.zero_confirm_samples = 3;
        assert_eq!(filter.filter(5.0), (5.0, true));
        assert_eq!(filter.filter(-23_592_960.0), (5.0, false));
        assert_eq!(filter.filter(-23_592_960.0), (5.0, false));
        // Once back in range, accepted immediately.
        assert_eq!(filter.filter(5.1), (5.1, true));
    }

    #[test]
    fn startup_trusts_first_reading_nonzero() {
        let mut filter = AngleReliability::default();
        assert_eq!(filter.filter(-12.6), (-12.6, true));
    }

    #[test]
    fn startup_trusts_first_reading_zero() {
        let mut filter = AngleReliability::default();
        assert_eq!(filter.filter(-0.1), (-0.1, true));
    }

    #[test]
    fn startup_trusts_first_reading_exact_zero() {
        let mut filter = AngleReliability::default();
        assert_eq!(filter.filter(0.0), (0.0, true));
    }

    #[test]
    fn any_angle_to_zero_needs_confirm() {
        let mut filter = AngleReliability::default();
        filter.config.zero_confirm_samples = 3;
        assert_eq!(filter.filter(-70.0), (-70.0, true));
        assert_eq!(filter.filter(0.0), (-70.0, false));
        assert_eq!(filter.filter(0.0), (-70.0, false));
        assert_eq!(filter.filter(0.0), (0.0, true));
    }

    #[test]
    fn small_angle_to_zero_needs_confirm() {
        let mut filter = AngleReliability::default();
        filter.config.zero_confirm_samples = 3;
        assert_eq!(filter.filter(5.0), (5.0, true));
        assert_eq!(filter.filter(0.0), (5.0, false));
        assert_eq!(filter.filter(0.0), (5.0, false));
        assert_eq!(filter.filter(0.0), (0.0, true));
    }

    #[test]
    fn normal_a_to_b_is_not_delayed() {
        let mut filter = AngleReliability::default();
        assert_eq!(filter.filter(-70.0), (-70.0, true));
        assert_eq!(filter.filter(-55.0), (-55.0, true));
        assert_eq!(filter.filter(-20.0), (-20.0, true));
    }

    #[test]
    fn zero_interrupted_resets_count() {
        let mut filter = AngleReliability::default();
        filter.config.zero_confirm_samples = 3;
        assert_eq!(filter.filter(-70.0), (-70.0, true));
        assert_eq!(filter.filter(0.0), (-70.0, false));
        assert_eq!(filter.filter(0.0), (-70.0, false));
        assert_eq!(filter.filter(-55.0), (-55.0, true));
        assert_eq!(filter.filter(0.0), (-55.0, false));
        assert_eq!(filter.filter(0.0), (-55.0, false));
        assert_eq!(filter.filter(0.0), (0.0, true));
    }
}
