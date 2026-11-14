import { t } from "./i18n";
import {
  forwardKinematics,
  solveInverseKinematics,
} from "../vendor/star-arm/kinematics";
import { JOINTS } from "../vendor/star-arm/model-data";

export type Mapping = { directions: number[]; offsets: number[] };
export const DEFAULT_MAPPING: Mapping = {
  directions: [1, 1, 1, -1, 1, 1],
  offsets: [0, 0, 0, 0, 0, 0],
};
// Original project's physical work pose: native [0,0,-60,+60,0,0].
// The referenced model reverses the J4 axis, hence -60° in this model.
export const WORK_POSE = [0, 0, -60, -60, 0, 0];
export const JOINT_ANGLE_TOLERANCE_DEG = 0.5;
export const limits = JOINTS.map((j) => [
  (j.limit.lower * 180) / Math.PI,
  (j.limit.upper * 180) / Math.PI,
]);
export const toRadians = (values: number[]) =>
  values.map((v) => (v * Math.PI) / 180);
export const toDegrees = (values: number[]) =>
  values.map((v) => (v * 180) / Math.PI);
export function modelAngles(raw: number[], mapping: Mapping) {
  return raw
    .slice(0, 6)
    .map((v, i) => (v - mapping.offsets[i]) * mapping.directions[i]);
}
export function servoAngles(model: number[], mapping: Mapping) {
  return model.map((v, i) => v / mapping.directions[i] + mapping.offsets[i]);
}
export function assertJoints(values: number[]) {
  if (values.length !== 6 || !values.every(Number.isFinite))
    throw Error(t("需要 6 个有限的模型关节角（度）"));
  values.forEach((v, i) => {
    const [lower, upper] = limits[i];
    if (v < lower - JOINT_ANGLE_TOLERANCE_DEG - 1e-6 || v > upper + JOINT_ANGLE_TOLERANCE_DEG + 1e-6)
      throw Error(
        t("J{0} 超出原模型范围 {1}°", i + 1, limits[i].map((v) => v.toFixed(1)).join("～")),
      );
  });
}
export function posture(degrees: number[]) {
  const fk = forwardKinematics(toRadians(degrees));
  const m = fk.matrix;
  return {
    joints_deg: [...degrees],
    tcp_mm: fk.position.map((v) => v * 1000),
    tool_axes_in_base: [
      [m[0], m[4], m[8]],
      [m[1], m[5], m[9]],
      [m[2], m[6], m[10]],
    ],
    points: fk.points,
  };
}
// Keep render geometry in RobotState; return only control-relevant pose data
// to the model. Elevation is measured from the base XY plane, positive upward.
export function poseSummary(value: ReturnType<typeof posture>) {
  return {
    joints_deg: value.joints_deg,
    tcp_mm: value.tcp_mm.map((v) => Math.round(v * 10) / 10),
    tool_axes_in_base: value.tool_axes_in_base.map((axis) =>
      axis.map((v) => Math.round(v * 10000) / 10000),
    ),
    tool_axis_elevation_deg: value.tool_axes_in_base.map((axis) =>
      Math.round(Math.atan2(axis[2], Math.hypot(axis[0], axis[1])) * 1800 / Math.PI) / 10,
    ),
  };
}
export function inverse(positionMm: number[], seed: number[]) {
  const result = solveInverseKinematics(
    positionMm.map((v) => v / 1000),
    toRadians(seed),
  );
  return {
    success: result.success,
    joints_deg: result.angles ? toDegrees(result.angles) : null,
    error_mm: result.positionError == null ? null : result.positionError * 1000,
    iterations: result.iterations,
    reason: result.reason,
  };
}
