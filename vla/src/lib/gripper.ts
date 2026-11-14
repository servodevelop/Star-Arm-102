// Independently maintained subset of robot-arm's audited GraspGenX manifest
// backend/devices/stararm-102/graspgenx/manifest.json (5412efe), sweep_volume.
// These are measured grasp-space references, not a continuous opening curve.
export const GRIPPER_REFERENCE = {
  servo_id: 6,
  closed_deg: 0,
  mechanical_max_deg: 90,
  samples: [
    {
      angle_deg: 30,
      inner_width_mm: 71,
      reference_center_mm: [1.34, 0.15, 80],
    },
    {
      angle_deg: 60,
      inner_width_mm: 129,
      reference_center_mm: [1.33, 0.15, 60],
    },
  ],
  note: "源于经审核的 GraspGenX 有效夹持空间；测量深度不同，不是所有深度的指尖间距，也不是连续角度—宽度标定曲线。90°为机械行程上限，不是默认张开目标。",
};
