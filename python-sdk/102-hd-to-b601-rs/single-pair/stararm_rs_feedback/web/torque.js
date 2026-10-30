// Display-only mapping. The scale is not a motor limit or a control parameter.
export const finite = value => typeof value === 'number' && Number.isFinite(value);
export const HEAT_COLORS = ['#3978f6', '#d69b35', '#dc4d4d'];
export function torqueVisual(joint, {fresh = false, metric = 'torque_nm', scale = 2} = {}) {
  const available = fresh && (!finite(joint?.can_age_s) || joint.can_age_s < .8);
  const valid = available && finite(joint?.[metric]) && (metric !== 'residual_nm' || joint.valid === true);
  if (!valid) return {value: null, ratio: 0, color: '#92a29e', level: available ? '缺少数据' : '非实时'};
  const value = joint[metric], ratio = Math.min(1, Math.abs(value) / (finite(scale) && scale > 0 ? scale : 2));
  const level = ratio < .5 ? '低' : ratio < .8 ? '中' : '高';
  const a = ratio < .5 ? HEAT_COLORS[0] : HEAT_COLORS[1];
  const b = ratio < .5 ? HEAT_COLORS[1] : HEAT_COLORS[2];
  const mix = ratio < .5 ? ratio * 2 : (ratio - .5) * 2;
  const rgb = hex => hex.match(/\w\w/g).map(channel => parseInt(channel, 16));
  const ca = rgb(a.slice(1)), cb = rgb(b.slice(1));
  const color = '#' + ca.map((channel, i) => Math.round(channel + (cb[i] - channel) * mix).toString(16).padStart(2, '0')).join('');
  return {value, ratio, color, level};
}
