import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
// Import as ESM without adding Node package metadata to the Python distribution.
const source = await readFile(new URL('../stararm_rs_feedback/web/torque.js', import.meta.url), 'utf8');
const {torqueVisual} = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
const live = {fresh:true, scale:2};
assert.equal(torqueVisual({torque_nm:0}, live).color, '#3978f6');
assert.equal(torqueVisual({torque_nm:1}, live).color, '#d69b35');
assert.equal(torqueVisual({torque_nm:-2}, live).color, '#dc4d4d');
assert.equal(torqueVisual({torque_nm:20}, live).ratio, 1);
assert.equal(torqueVisual({torque_nm:-.5}, live).value, -.5);
for (const value of [null, undefined, NaN, Infinity, '1']) assert.equal(torqueVisual({torque_nm:value}, live).value, null);
assert.equal(torqueVisual({torque_nm:2}, {fresh:false}).value, null);
assert.equal(torqueVisual({torque_nm:2,can_age_s:.8}, live).value, null);
assert.equal(torqueVisual({torque_nm:2,can_age_s:10}, {...live,source:'replay'}).value, 2);
assert.equal(torqueVisual({residual_nm:1,valid:false}, {...live,metric:'residual_nm'}).value, null);
assert.equal(torqueVisual({residual_nm:1,valid:true}, {...live,metric:'residual_nm'}).value, 1);
assert.equal(torqueVisual({torque_nm:1}, {...live,scale:4}).ratio, .25);
console.log('Torque visualization: magnitude, sign, missing/stale data, replay, residual validity and scale passed.');
