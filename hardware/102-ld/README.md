# Star Arm 102-LD hardware

[← Hardware Resources](../README.md)　|　<sub>**English** / [简体中文](README.zh.md)</sub>

<p align="center">
  <a href="images/102-ld-diy-kit-main-image-01-2.webp"><img src="images/102-ld-diy-kit-main-image-01-2.webp" alt="Star Arm 102-LD DIY kit" width="15%"></a>
  <a href="images/102-ld-main-image-02.webp"><img src="images/102-ld-main-image-02.webp" alt="Star Arm 102-LD product view 2" width="15%"></a>
  <a href="images/102-ld-main-image-03.webp"><img src="images/102-ld-main-image-03.webp" alt="Star Arm 102-LD product view 3" width="15%"></a>
  <a href="images/102-ld-main-image-04.webp"><img src="images/102-ld-main-image-04.webp" alt="Star Arm 102-LD product view 4" width="15%"></a>
  <a href="images/102-ld-main-image-05.webp"><img src="images/102-ld-main-image-05.webp" alt="Star Arm 102-LD product view 5" width="15%"></a>
  <a href="images/102-ld-main-image-06.webp"><img src="images/102-ld-main-image-06.webp" alt="Star Arm 102-LD product view 6" width="15%"></a>
</p>

**Contents:**

- [📂 Resources](#resources)
- [📋 Bill of Materials](#bill-of-materials)

<a id="resources"></a>

## Resources

| Directory | Description | Status |
| --- | --- | --- |
| [Assembly guide](../../docs/diy-assembly/README.md#102-ld) | Main arm assembly video | ✅ Complete |
| [step/](step/) | Part models in parts/; shared assembly in assembly/ | ✅ Complete |
| [printing/](printing/) | 3MF projects; STL: [View parts](printing/stl/) · [Download ZIP](printing/star-arm-102-ld-stl.zip) | ✅ Complete |
| [drawings/](drawings/) | PDF / DWG drawings | ✅ Complete |
| [robot-description/](robot-description/) | URDF model: [Browse source](robot-description/) · [Download ZIP](robot-description/star-arm-102-ld-hd-urdf.zip) | ✅ Complete |

<a id="bill-of-materials"></a>

## Bill of Materials

The table below lists **28 assembly items** for 102-LD. Missing images are marked pending.

Printed-part identifiers in Model / Specification match the STEP, STL, and individual 3MF filenames (without extensions). Print settings in this BOM are references pending physical print validation.

Screw images are AI-generated illustrations; refer to the table text for specifications. Click an image to enlarge it.

| No. | Part Name | Model / Specification | Image | Description | Quantity | SKU |
| :---: | --- | --- | :---: | --- | :---: | --- |
| 1 | UART bus servo | RA8-U01H-M | <img src="images/ra8-u01h-m.webp" alt="RA8-U01H-M" width="90"> | 12V; Dual-shaft; No Motor (No Torque Output); 12-bit Magnetic Absolute Encoder; 25T | 4 | 02.06.00000394 |
| 2 | UART bus servo | RA8-U02H-M | <img src="images/ra8-u02h-m.webp" alt="RA8-U02H-M" width="90"> | 12V; Dual-shaft Housing (Flat Bottom Cover, No Rear Output Shaft); No Motor (No Torque Output); 12-bit Magnetic Absolute Encoder; D-Type Shaft | 1 | 02.06.00000396 |
| 3 | UART bus servo | RA8-U03H-M | <img src="images/ra8-u03h-m.webp" alt="RA8-U03H-M" width="90"> | 12V; Dual-shaft Housing (Flat Bottom Cover, No Rear Output Shaft); No Motor (No Torque Output); 12-bit Magnetic Absolute Encoder; 25T | 2 | 02.06.00000395 |
| 4 | Base bottom plate | star-arm-102-base-bottom | <img src="images/star-arm-102-base-bottom.png" alt="star-arm-102-base-bottom" width="90"> | Ivory, PLA 3D printed part; wall loops: 2; infill density: 15% | 1 | 01.03.03000131 |
| 5 | Base top plate | star-arm-102-base-top | <img src="images/star-arm-102-base-top.png" alt="star-arm-102-base-top" width="90"> | Ivory, PLA 3D printed part; settings vary by region; see 3MF | 1 |  |
| 6 | Link 1 | star-arm-102-link1 | <img src="images/star-arm-102-link1.png" alt="star-arm-102-link1" width="90"> | Ivory, PLA 3D printed part; wall loops: 5; infill density: 50% | 1 | 01.03.03000133 |
| 7 | Link 2 | star-arm-102-link2 | <img src="images/star-arm-102-link2.png" alt="star-arm-102-link2" width="90"> | Ivory, PLA 3D printed part; wall loops: 2; infill density: 10% | 1 | 01.03.03000134 |
| 8 | Link 3 | star-arm-102-link3 | <img src="images/star-arm-102-link3.png" alt="star-arm-102-link3" width="90"> | Ivory + black, PLA 3D printed part; settings vary by region; see 3MF | 1 | 01.03.03000135 |
| 9 | Link 4 | star-arm-102-link4 | <img src="images/star-arm-102-link4.png" alt="star-arm-102-link4" width="90"> | Ivory, PLA 3D printed part; wall loops: 2; infill density: 15% | 1 | 01.03.03000136 |
| 10 | Link 5 | star-arm-102-link5 | <img src="images/star-arm-102-link5.png" alt="star-arm-102-link5" width="90"> | Ivory, PLA 3D printed part; wall loops: 2; infill density: 15% | 1 | 01.03.03000137 |
| 11 | Link 6 (handle) | star-arm-102-link6-handle | <img src="images/star-arm-102-link6-handle.png" alt="star-arm-102-link6-handle" width="90"> | Ivory, PLA 3D printed part; wall loops: 5; infill density: 15% | 1 | 01.03.03000138 |
| 12 | Handle | star-arm-102-handle | <img src="images/star-arm-102-handle.png" alt="star-arm-102-handle" width="90"> | Ivory, PLA 3D printed part; wall loops: 2; infill density: 15% | 1 | 01.03.03000139 |
| 13 | Left finger ring | star-arm-102-finger-ring-left | <img src="images/star-arm-102-finger-ring-left.png" alt="star-arm-102-finger-ring-left" width="90"> | Ivory, PLA 3D printed part; wall loops: 2; infill density: 15% | 1 | 01.03.03000140 |
| 14 | Right finger ring | star-arm-102-finger-ring-right | <img src="images/star-arm-102-finger-ring-right.png" alt="star-arm-102-finger-ring-right" width="90"> | Ivory, PLA 3D printed part; wall loops: 2; infill density: 15% | 1 | 01.03.03000141 |
| 15 | Thrust needle roller bearing | AXK2035+2AS | <img src="../../media/axk2035-2as-bearing.png" alt="AXK2035+2AS thrust needle roller bearing" width="90"> | inner diameter 20 mm, outer diameter 35 mm, thickness 4 mm | 1 | 01.08.05000012 |
| 16 | Circuit board | UC-01 | <img src="../../media/uc-01-primary.webp" alt="UC-01" width="90"> | DC power lead: 0.75 mm², 5.5 × 2.1 mm female, 0.15 m | 1 | 03.01.00000107 |
| 17 | Servo cable | PH2.0 (PH-3Y)<br>120 mm | <a href="../../media/ph-3y-servo-cable-120mm.png"><img src="../../media/ph-3y-servo-cable-120mm.png" alt="PH2.0 120 mm servo cable" width="90"></a> | Black silicone-insulated ribbon cable with black braided sleeving; reversed pin order between ends; 60 × Ø0.08 mm strands per conductor (approx. 22 AWG) | 5 | 01.01.17000102 |
| 18 | Servo cable | PH2.0 (PH-3Y)<br>200 mm | <a href="../../media/ph-3y-servo-cable-200mm.png"><img src="../../media/ph-3y-servo-cable-200mm.png" alt="PH2.0 200 mm servo cable" width="90"></a> | Black silicone-insulated ribbon cable with black braided sleeving; reversed pin order between ends; 60 × Ø0.08 mm strands per conductor (approx. 22 AWG) | 2 | 01.01.17000101 |
| 19 | Socket-head cap screw | M3 × 10 | <a href="../../media/fasteners/m3-10-socket-head-cap-screw.png"><img src="../../media/fasteners/m3-10-socket-head-cap-screw.png" alt="M3 × 10 socket-head cap screw illustration" width="90"></a> | Black finish, property class 12.9 | 1 | 01.06.01000167 |
| 20 | Socket-head cap screw | M3 × 22 | <a href="../../media/fasteners/m3-22-socket-head-cap-screw.png"><img src="../../media/fasteners/m3-22-socket-head-cap-screw.png" alt="M3 × 22 socket-head cap screw illustration" width="90"></a> | Black finish | 4 | 01.06.01000183 |
| 21 | Phillips screw | M3 × 10 | Pending | Black finish, hardened | 1 |  |
| 22 | Phillips self-tapping screw | PB2.0 × 5 | Pending | Black finish, hardened | 39 | 01.06.01000060 |
| 23 | Phillips pan-head screw | M2 × 4.5 | <a href="../../media/fasteners/m2-4-5-phillips-pan-head-screw.png"><img src="../../media/fasteners/m2-4-5-phillips-pan-head-screw.png" alt="M2 × 4.5 Phillips pan-head screw illustration" width="90"></a> | Black finish, pre-applied threadlocker | 35 | 01.06.01000079 |
| 24 | Socket-head cap screw | M2 × 8 | <a href="../../media/fasteners/m2-8-socket-head-cap-screw.png"><img src="../../media/fasteners/m2-8-socket-head-cap-screw.png" alt="M2 × 8 socket-head cap screw illustration" width="90"></a> | Black finish | 16 | 01.06.01000184 |
| 25 | Hex socket screw | M2 × 10 | Pending | Black finish | 8 |  |
| 26 | Phillips flat-head self-tapping screw | 3 × 12 mm | <a href="../../media/fasteners/3-12-phillips-flat-head-self-tapping-screw.png"><img src="../../media/fasteners/3-12-phillips-flat-head-self-tapping-screw.png" alt="3 × 12 mm Phillips flat-head self-tapping screw illustration" width="90"></a> | Silver finish | 2 |  |
| 27 | Locknut | M3 | Pending | Black finish | 5 | 01.06.01000086 |
| 28 | Washer | M3 | Pending | Stainless steel | 1 |  |

Found an error in these resources or need help? Contact our [Support Hub](https://fashionstar.com.hk/support/) with your model and the relevant file or item.
