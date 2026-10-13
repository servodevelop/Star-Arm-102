# DIY Assembly & Calibration

[← Documentation](../)　|　<sub>**English** / [简体中文](README.zh.md)</sub>

Build and prepare your Star Arm 102 in one guide: assemble the arm, connect it, calibrate zero, set and write the PID parameters for your model, and check joint motion. If your arm is already assembled, configured and calibrated, go to [Get Started](../getting-started.md).

**Contents:**

- [🎬 Assembly Videos](#assembly-videos)
- [🔘 HD Button Installation & Wiring](#button-installation-wiring)
- [🔌 Wiring & Communication](#wiring)
- [🎯 Zero Calibration](#zero-calibration)
- [⚙️ PID Settings & Writing Parameters](#pid-settings)
- [✅ Check & Continue](#check-and-continue)

BOM, CAD (STEP), URDF and 3D printing files: [102-LD](../../hardware/102-ld/) · [102-HD](../../hardware/102-hd/) · [102-FL](../../hardware/102-fl/).

<a id="assembly-videos"></a>

## 🎬 Assembly Videos

Click a cover or its link below to watch the tutorial on YouTube.

<table>
<tr>
<td width="50%" valign="top">
<a id="102-ld"></a><a id="102-hd"></a>
<h3>🦾 102-LD/HD Main Arm Assembly</h3>
<a href="https://www.youtube.com/watch?v=flTCgBx3K0M"><img src="../../media/star-arm-102-ld-hd-assembly-preview.jpg" alt="Star Arm 102-LD / HD main arm assembly video cover" width="100%"></a>
<p>Follow the video for LD. For HD, use the corresponding purple coreless bus servos supplied with your arm; the remaining main arm assembly steps are the same.</p>
<p><a href="https://www.youtube.com/watch?v=flTCgBx3K0M">▶ Watch on YouTube</a></p>
</td>
<td width="50%" valign="top">
<a id="102-fl"></a>
<h3>🦾 102-FL Main Arm Assembly</h3>
<a href="https://www.youtube.com/watch?v=9-ufaI8dwys"><img src="images/star-arm-102-fl-assembly-preview.jpg" alt="Star Arm 102-FL main arm assembly video cover" width="100%"></a>
<p>Follow the video to assemble the 102-FL follower's main arm.</p>
<p><a href="https://www.youtube.com/watch?v=9-ufaI8dwys">▶ Watch on YouTube</a></p>
</td>
</tr>
<tr>
<td width="50%" valign="top">
<a id="flexible-gripper-assembly"></a>
<h3>🤏 Flexible Gripper Assembly</h3>
<a href="https://www.youtube.com/watch?v=lqLOFoPuTgw"><img src="images/star-arm-flexible-gripper-assembly-preview.jpg" alt="Star Arm 102 flexible gripper assembly video cover" width="100%"></a>
<p>Replace and assemble the flexible gripper. See <a href="../../hardware/flexible-gripper/">Flexible Gripper Hardware</a> for parts and BOM.</p>
<p><a href="https://www.youtube.com/watch?v=lqLOFoPuTgw">▶ Watch on YouTube</a></p>
</td>
<td width="50%" valign="top">
<a id="camera-module-assembly"></a>
<h3>📷 Camera Module Assembly</h3>
<p><strong>Video coming soon.</strong></p>
<p>See <a href="../../hardware/camera-module/">Camera Module Hardware</a> for parts and BOM.</p>
</td>
</tr>
</table>

<a id="button-installation-wiring"></a>

## 🔘 HD Button Installation & Wiring

Use the photo to check the button module's position on the base, connector orientation and cable routing. Click to view the full-size image.

<a href="images/star-arm-102-hd-button-wiring.jpg"><img src="images/star-arm-102-hd-button-wiring.jpg" alt="102-HD button module mounting position and wiring reference" width="50%"></a>

<a id="wiring"></a>

## 🔌 Wiring & Communication

Follow [power, wiring and serial-port identification](../getting-started.md#connect), then complete the [communication check](../../python-sdk/README.md#check-communication-without-commanding-motion). Return here to complete zero calibration first, then set and write the PID parameters applicable to your model.

<a id="zero-calibration"></a>

## 🎯 Zero Calibration

LD, HD and FL each need the correct reference pose and zero definition. This section applies after DIY assembly, joint reassembly or servo replacement.

**Reference-pose images and the zero-setting procedure are coming soon.** Until they are available, confirm the method for your hardware revision with [Fashion Star Support](https://fashionstar.com.hk/support/).

Hardware zero calibration, resetting multi-turn counts and LeRobot calibration are separate operations. The direct Python teleoperation script resets multi-turn counts when connecting; it does not perform LeRobot calibration. Follow the selected software guide for any additional calibration it requires.

<a id="pid-settings"></a>

## ⚙️ PID Settings & Writing Parameters

Complete zero calibration before setting and writing PID parameters.

| Model | Applicability | Instructions |
| --- | --- | --- |
| 102-LD | Motorless leader; the HD / FL motor PID procedure does not apply | No motor PID setup |
| 102-HD | Motorized pose-holding leader; use settings for the corresponding servo model and firmware | Parameter table and procedure coming soon |
| 102-FL | Motorized follower; use settings for the corresponding servo model and firmware | Parameter table and procedure coming soon |

See [control and configuration tools](../../tools/README.md#choose-a-tool) for available tools. The approved per-joint PID values and write/save procedure are not yet provided here; do not copy values between different models or firmware versions.

<a id="check-and-continue"></a>

## ✅ Check & Continue

Before first use, confirm that assembly and wiring are complete, communication works, and zero calibration and the applicable PID parameter setup and writing have been completed. Follow your software guide to check joint direction and motion over a small range. If motion or feedback is unexpected, stop and check the setup; see [reference pose and stopping](../getting-started.md#reference-pose-and-stopping).

**[Continue to Get Started →](../getting-started.md#digital-twin)**
