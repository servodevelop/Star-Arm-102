# Star Arm 102-FL hardware

[← Hardware Resources](../README.md)　|　<sub>**English** / [简体中文](README.zh.md)</sub>

<p align="center">
  <a href="images/102-fl-diy-kit-main-image-01.webp"><img src="images/102-fl-diy-kit-main-image-01.webp" alt="Star Arm 102-FL DIY kit" width="15%"></a>
  <a href="images/102-fl-main-image-02.webp"><img src="images/102-fl-main-image-02.webp" alt="Star Arm 102-FL product view 2" width="15%"></a>
  <a href="images/102-fl-main-image-03.webp"><img src="images/102-fl-main-image-03.webp" alt="Star Arm 102-FL product view 3" width="15%"></a>
  <a href="images/102-fl-main-image-04.webp"><img src="images/102-fl-main-image-04.webp" alt="Star Arm 102-FL product view 4" width="15%"></a>
  <a href="images/102-fl-main-image-05.webp"><img src="images/102-fl-main-image-05.webp" alt="Star Arm 102-FL product view 5" width="15%"></a>
  <a href="images/102-fl-main-image-06.webp"><img src="images/102-fl-main-image-06.webp" alt="Star Arm 102-FL product view 6" width="15%"></a>
</p>

**Contents:**

- [📂 Resources](#resources)
- [📋 Bill of Materials](#bill-of-materials)

<a id="resources"></a>

## Resources

| Directory | Description | Status |
| --- | --- | --- |
| [Assembly guide](../../docs/diy-assembly/README.md#102-fl) | Main arm assembly video | ✅ Complete |
| [step/](step/) | Part models in parts/; whole-arm assemblies in assembly/ | ✅ Complete |
| [printing/](printing/) | 3MF projects; STL: [View parts](printing/stl/) · [Download ZIP](printing/star-arm-102-fl-stl.zip) | ✅ Complete |
| [drawings/](drawings/) | PDF / DWG drawings | ✅ Complete |
| [robot-description/](robot-description/) | URDF model: [Browse source](robot-description/) · [Download ZIP](robot-description/star-arm-102-fl-urdf.zip) | ✅ Complete |

<a id="bill-of-materials"></a>

## Bill of Materials

The table below lists **29 assembly items** for 102-FL. Missing images are marked pending.

Printed-part names match the STEP, STL, and individual 3MF filenames. Print settings in Notes are references pending physical print validation. The BOM specifies 5 wall loops / 50% infill for link1, while the supplied 3MF uses 2 / 15%; confirm before printing.

| No. | Name | Image | Description | Quantity | Notes |
| :---: | --- | :---: | --- | :---: | --- |
| 1 | RX8-U50H-M | <img src="images/rx8-u50h-m-primary.webp" alt="RX8-U50H-M" width="90"> | UART Bus Servo/12V/50kg-cm/70rpm/<br>Dual-shaft/Brushless Motor/12-bit Magnetic Absolute Encoder/25T | 2 | Firmware V330 |
| 2 | RA8-U35H-M | <img src="images/ra8-u35h-m.webp" alt="RA8-U35H-M" width="90"> | UART Bus Servo/12V/35kg-cm/55rpm/<br>Dual-shaft/Brushed Core Motor/12-bit Magnetic Absolute Encoder/25T | 3 | Firmware V225 |
| 3 | RA8-U35H-M-C047 | <img src="images/ra8-u35h-m-c047.webp" alt="RA8-U35H-M-C047" width="90"> | UART Bus Servo/12V/35kg-cm/55rpm/<br>Dual-shaft Housing (Flat Bottom Cover, No Rear Output Shaft)/Brushed Core Motor/12-bit Magnetic Absolute Encoder/25T | 1 | Firmware V225 |
| 4 | RA8-U27H-M-C005 | <img src="images/ra8-u27h-m-c005.webp" alt="RA8-U27H-M-C005" width="90"> | UART Bus Servo/12V/25kg-cm/72rpm/<br>Dual-shaft Housing (Flat Bottom Cover, No Rear Output Shaft)/Brushed Core Motor/12-bit Magnetic Absolute Encoder/D-Type Shaft | 1 | Firmware V225 |
| 5 | star-arm-102-base-bottom | <img src="images/star-arm-102-base-bottom.png" alt="star-arm-102-base-bottom" width="90"> | PLA 3D printed part (ivory) | 1 | 2 wall loops; 15% infill |
| 6 | star-arm-102-base-top | <img src="images/star-arm-102-base-top.png" alt="star-arm-102-base-top" width="90"> | PLA 3D printed part (ivory) | 1 | Settings vary by region; see 3MF |
| 7 | star-arm-102-link1 | <img src="images/star-arm-102-link1.png" alt="star-arm-102-link1" width="90"> | PLA 3D printed part (ivory) | 1 | 5 wall loops; 50% infill |
| 8 | star-arm-102-link2 | <img src="images/star-arm-102-link2.png" alt="star-arm-102-link2" width="90"> | PLA 3D printed part (ivory) | 1 | 2 wall loops; 10% infill |
| 9 | star-arm-102-link3 | <img src="images/star-arm-102-link3.png" alt="star-arm-102-link3" width="90"> | PLA 3D printed part (ivory + black) | 1 | Settings vary by region; see 3MF |
| 10 | star-arm-102-link4 | <img src="images/star-arm-102-link4.png" alt="star-arm-102-link4" width="90"> | PLA 3D printed part (ivory) | 1 | 2 wall loops; 15% infill |
| 11 | star-arm-102-link5 | <img src="images/star-arm-102-link5.png" alt="star-arm-102-link5" width="90"> | PLA 3D printed part (ivory) | 1 | 2 wall loops; 15% infill |
| 12 | star-arm-102-link6-gripper | <img src="images/star-arm-102-link6-gripper.png" alt="star-arm-102-link6-gripper" width="90"> | PLA 3D printed part (ivory) | 1 | 4 wall loops; 15% infill |
| 13 | star-arm-102-gripper-body | <img src="images/star-arm-102-gripper-body.png" alt="star-arm-102-gripper-body" width="90"> | PLA 3D printed part (ivory) | 1 | 4 wall loops; 15% infill |
| 14 | star-arm-102-fingertip-left | <img src="images/star-arm-102-fingertip-left.png" alt="star-arm-102-fingertip-left" width="90"> | PLA 3D printed part (ivory) | 1 | 4 wall loops; 15% infill |
| 15 | star-arm-102-fingertip-right | <img src="images/star-arm-102-fingertip-right.png" alt="star-arm-102-fingertip-right" width="90"> | PLA 3D printed part (ivory) | 1 | 4 wall loops; 15% infill |
| 16 | Thrust needle roller bearing | <img src="../../media/axk2035-2as-bearing.png" alt="AXK2035+2AS thrust needle roller bearing" width="90"> | AXK2035+2AS; inner diameter 20 mm, outer diameter 35 mm, thickness 4 mm | 1 | Installed part |
| 17 | UC-01 board | <img src="../../media/uc-01-primary.webp" alt="UC-01" width="90"> | XT30 connector | 1 | Installed part |
| 18 | 120 mm servo cable | <a href="../../media/ph-3y-servo-cable-120mm.png"><img src="../../media/ph-3y-servo-cable-120mm.png" alt="PH-3Y 120 mm servo cable" width="90"></a> | PH-3Y, reverse-wired ends, black braided silicone cable | 4 | Installed part |
| 19 | 200 mm servo cable | <a href="../../media/ph-3y-servo-cable-200mm.png"><img src="../../media/ph-3y-servo-cable-200mm.png" alt="PH-3Y 200 mm servo cable" width="90"></a> | PH-3Y, reverse-wired ends, black braided silicone cable | 3 | Installed part |
| 20 | M3 × 10 socket-head screw | Pending | HSCS, grade 12.9 | 1 | Installed part |
| 21 | M3 × 22 socket-head screw | Pending | Black finish | 4 | Installed part |
| 22 | M3 × 10 Phillips screw | Pending | Hardened, black finish | 1 | Installed part |
| 23 | PB2.0 × 5 self-tapping screw | Pending | Phillips countersunk, hardened, black finish | 30 | Installed part |
| 24 | M2 × 4.5 Phillips screw | Pending | Countersunk, black finish, pre-applied threadlocker | 47 | Installed part |
| 25 | M2 × 10 socket-head screw | Pending | Black finish | 8 | Installed part |
| 26 | M2 × 8 socket-head screw | Pending | Black finish | 16 | Installed part |
| 27 | M3 × 12 self-tapping screw | Pending | Phillips head | 2 | Installed part |
| 28 | M3 locknut | Pending | Black finish | 6 | Installed part |
| 29 | M3 washer | Pending | 3 × 6 × 0.5 mm | 2 | Installed part |

Found an error in these resources or need help? Contact our [Support Hub](https://fashionstar.com.hk/support/) with your model and the relevant file or item.
