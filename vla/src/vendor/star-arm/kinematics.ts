// Typed adaptation of star-arm-studio 71114a0 ik_solver.js.
// Same URDF transforms and damped least-squares position solver; adds link points.
import { JOINTS, type Joint } from "./model-data";

function multiply(a: number[], b: number[]) {
  return Array.from({ length: 16 }, (_, i) => {
    const row = Math.floor(i / 4),
      column = i % 4;
    return [0, 1, 2, 3].reduce(
      (sum, k) => sum + a[row * 4 + k] * b[k * 4 + column],
      0,
    );
  });
}
function origin({ xyz, rpy }: Joint["origin"]) {
  const [r, p, y] = rpy,
    cr = Math.cos(r),
    sr = Math.sin(r),
    cp = Math.cos(p),
    sp = Math.sin(p),
    cy = Math.cos(y),
    sy = Math.sin(y);
  return [
    cy * cp,
    cy * sp * sr - sy * cr,
    cy * sp * cr + sy * sr,
    xyz[0],
    sy * cp,
    sy * sp * sr + cy * cr,
    sy * sp * cr - cy * sr,
    xyz[1],
    -sp,
    cp * sr,
    cp * cr,
    xyz[2],
    0,
    0,
    0,
    1,
  ];
}
function rotation(axis: number[], angle: number) {
  const length = Math.hypot(...axis),
    [x, y, z] = axis.map((v) => v / length);
  const c = Math.cos(angle),
    s = Math.sin(angle),
    t = 1 - c;
  return [
    c + x * x * t,
    x * y * t - z * s,
    x * z * t + y * s,
    0,
    y * x * t + z * s,
    c + y * y * t,
    y * z * t - x * s,
    0,
    z * x * t - y * s,
    z * y * t + x * s,
    c + z * z * t,
    0,
    0,
    0,
    0,
    1,
  ];
}
export function forwardKinematics(angles: number[]) {
  if (angles.length !== 6 || !angles.every(Number.isFinite))
    throw Error("正解需要 6 个有限弧度值");
  let matrix = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
  const points = [[0, 0, 0]];
  JOINTS.forEach((j, i) => {
    matrix = multiply(
      multiply(matrix, origin(j.origin)),
      rotation(j.axis, angles[i]),
    );
    points.push([matrix[3], matrix[7], matrix[11]]);
  });
  return { matrix, points, position: [matrix[3], matrix[7], matrix[11]] };
}
function solve3(matrix: number[][], vector: number[]) {
  const rows = matrix.map((r, i) => [...r, vector[i]]);
  for (let c = 0; c < 3; c++) {
    let pivot = c;
    for (let r = c + 1; r < 3; r++)
      if (Math.abs(rows[r][c]) > Math.abs(rows[pivot][c])) pivot = r;
    [rows[c], rows[pivot]] = [rows[pivot], rows[c]];
    const divisor = rows[c][c];
    if (!Number.isFinite(divisor) || Math.abs(divisor) < 1e-15) return null;
    for (let k = c; k < 4; k++) rows[c][k] /= divisor;
    for (let r = 0; r < 3; r++)
      if (r !== c) {
        const factor = rows[r][c];
        for (let k = c; k < 4; k++) rows[r][k] -= factor * rows[c][k];
      }
  }
  return rows.map((r) => r[3]);
}
const clamp = (v: number, low: number, high: number) =>
  Math.max(low, Math.min(high, v));
export function solveInverseKinematics(target: number[], seed: number[]) {
  if (
    target.length !== 3 ||
    seed.length !== 6 ||
    ![...target, ...seed].every(Number.isFinite)
  )
    return {
      success: false,
      angles: null,
      positionError: null,
      iterations: 0,
      reason: "invalid-input",
    };
  const angles = seed.map((v, i) =>
    clamp(v, JOINTS[i].limit.lower, JOINTS[i].limit.upper),
  );
  // Same conservative geometric bound as upstream; this does not reject a
  // target inside the arm's reach just because one local solve fails.
  const maximumReach = JOINTS.reduce(
    (sum, joint) => sum + Math.hypot(...joint.origin.xyz),
    0,
  );
  if (Math.hypot(...target) > maximumReach + 0.001) {
    const position = forwardKinematics(angles).position;
    return {
      success: false,
      angles: null,
      positionError: Math.hypot(...target.map((v, i) => v - position[i])),
      iterations: 0,
      reason: "unreachable",
    };
  }
  let positionError = Infinity;
  // Numerical settings are those of the referenced position solver.
  for (let iteration = 0; iteration <= 100; iteration++) {
    const position = forwardKinematics(angles).position,
      error = target.map((v, i) => v - position[i]);
    positionError = Math.hypot(...error);
    if (positionError <= 0.001)
      return {
        success: true,
        angles,
        positionError,
        iterations: iteration,
        reason: "converged",
      };
    if (iteration === 100) break;
    const jacobian: number[][] = [[], [], []];
    for (let j = 0; j < 6; j++) {
      const perturbed = [...angles];
      perturbed[j] += 1e-5;
      const next = forwardKinematics(perturbed).position;
      for (let axis = 0; axis < 3; axis++)
        jacobian[axis][j] = (next[axis] - position[axis]) / 1e-5;
    }
    const normal = Array.from({ length: 3 }, (_, r) =>
      Array.from(
        { length: 3 },
        (_, c) =>
          jacobian[r].reduce((sum, v, i) => sum + v * jacobian[c][i], 0) +
          (r === c ? 0.03 ** 2 : 0),
      ),
    );
    const step = solve3(normal, error);
    if (!step) break;
    for (let j = 0; j < 6; j++) {
      const delta = jacobian.reduce(
        (sum, axis, i) => sum + axis[j] * step[i],
        0,
      );
      angles[j] = clamp(
        angles[j] + clamp(delta, -0.2, 0.2),
        JOINTS[j].limit.lower,
        JOINTS[j].limit.upper,
      );
    }
  }
  return {
    success: false,
    angles: null,
    positionError,
    iterations: 100,
    reason: "max-iterations",
  };
}
