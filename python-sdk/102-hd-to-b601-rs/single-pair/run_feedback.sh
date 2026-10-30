#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
# 普通动态阻尼的每轴功率上限（mW），J1-J5 与夹爪共用此上限。
# 默认 1200；也可用 bash run_feedback.sh 1500 临时覆盖，不必改源码。
# 实际输出随各轴负载变化；这个参数不改变独立堵转 HOLD 的功率。
if (( $# > 1 )); then
  echo 'Usage: bash run_feedback.sh [400..1500] (session recording is disabled)' >&2
  exit 2
fi
power_mw="${1:-1200}"
# 当前允许 400..1500mW。若改此范围，需同步 dynamic.py 的 dynamic_config()
# 范围检查、POLICY.allowed_power_mw，以及 feedback.rs-dynamic.json 的 policy。
if [[ ! "$power_mw" =~ ^[0-9]{3,4}$ ]] || (( 10#$power_mw < 400 || 10#$power_mw > 1500 )); then
  echo '普通阻尼功率须为 400..1500 mW，例如 bash run_feedback.sh 1200' >&2
  exit 2
fi
cat <<'TEXT'
动态反馈：会启动从臂跟随，并向主臂输出阻尼/保持。
按当前状态持续更新 J1-J5 与夹爪阻尼，不需要停稳、不使用 3 秒保留。
臂部运动超范围清零已关闭；速度/加速度超过旧阈值时继续计算阻尼。
J1 只按自身回转负载判断；限位按轴释放，主臂缺帧先限时补读一次。
J2/J3 电机角同时接近零位（均小于 3 度）时暂停 J2-J5 阻尼，任一达到 5 度后恢复。
J1 与夹爪独立判断；补读仍失败时暂停从臂新目标，阻尼继续按新鲜 RS 状态更新。
Leader 连续缺帧 0.25 秒仍退出；CAN 过期、故障及限位检查保留。
原有堵转保持独立工作，可对全部主臂关节请求 1500mW。
模型估计包含摩擦及建模误差，不代表精确外力或公斤数；动态空载手感尚待验证。
先空载缓慢移动，再持物缓慢移动、放下对比。
从臂仍会执行官方启动夹爪检查；Ctrl+C 后官方会回零/卸力，请留出空间并做好支撑。
TEXT
echo "本次 J1-J5 与夹爪普通阻尼上限：${power_mw} mW"
exec python -m stararm_rs_feedback.dynamic \
  --dynamic-spec feedback.rs-dynamic.json --feedback-enable \
  --dynamic-max-power-mw "$power_mw" \
  --robot.type=seeed_b601_rs_follower --robot.port=can0 \
  --robot.can_adapter=socketcan --robot.id=follower1 \
  --teleop.type=rebot_arm_102_leader --teleop.port=/dev/ttyUSB0 \
  --teleop.id=rebot_arm_102_leader --fps=30 > /dev/null 2>&1
