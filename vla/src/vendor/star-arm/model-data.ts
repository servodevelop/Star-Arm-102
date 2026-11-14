// Adapted from star-arm-studio 71114a0, urdf_model_data.js. Only FL arm joints.
export interface Joint {
  name: string;
  origin: { xyz: number[]; rpy: number[] };
  axis: number[];
  limit: { lower: number; upper: number };
}
const joint = (
  name: string,
  xyz: number[],
  rpy: number[],
  axis: number[],
  lower: number,
  upper: number,
): Joint => ({ name, origin: { xyz, rpy }, axis, limit: { lower, upper } });
export const JOINTS: Joint[] = [
  joint("joint1", [0, -0.004138, 0.02785], [0, 0, 0], [0, 0, -1], -2.27, 2.27),
  joint(
    "joint2",
    [0.0001, 0, 0.061025],
    [-1.5708, 0, 3.1416],
    [0, 0, -1],
    0,
    3.14,
  ),
  joint("joint3", [0.12162, -0.0021, 0], [0, 0, -1.5708], [0, 0, -1], -3.14, 0),
  joint(
    "joint4",
    [0.024219, -0.10865, 0],
    [0, 0, -1.5708],
    [0, 0, 1],
    -1.57,
    2.2,
  ),
  joint("joint5", [0.035, 0.00122, 0], [-1.5708, 0, 0], [0, 0, -1], -1.2, 1.2),
  joint(
    "joint6",
    [0.15168, 0, 0.002625],
    [-1.5708, 0, -1.5708],
    [0, 0, -1],
    -3.14,
    3.14,
  ),
];
