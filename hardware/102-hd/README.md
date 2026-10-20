# Star Arm 102-HD hardware

[← Hardware Resources](../README.md)　|　<sub>**English** / [简体中文](README.zh.md)</sub>

<p align="center">
  <a href="images/102-hd-diy-kit-main-image-01.webp"><img src="images/102-hd-diy-kit-main-image-01.webp" alt="Star Arm 102-HD DIY kit" width="15%"></a>
  <a href="images/102-hd-main-image-02-1.webp"><img src="images/102-hd-main-image-02-1.webp" alt="Star Arm 102-HD product view 2" width="15%"></a>
  <a href="images/102-hd-main-image-04-1.webp"><img src="images/102-hd-main-image-04-1.webp" alt="Star Arm 102-HD product view 3" width="15%"></a>
  <a href="images/102-hd-main-image-05-1.webp"><img src="images/102-hd-main-image-05-1.webp" alt="Star Arm 102-HD product view 4" width="15%"></a>
  <a href="images/102-hd-main-image-06.webp"><img src="images/102-hd-main-image-06.webp" alt="Star Arm 102-HD product view 5" width="15%"></a>
  <a href="images/102-hd-main-image-07.webp"><img src="images/102-hd-main-image-07.webp" alt="Star Arm 102-HD product view 6" width="15%"></a>
</p>

**Contents:**

- [📂 Resources](#resources)
- [📋 Bill of Materials](#bill-of-materials)
- [🔢 Joint and servo ID mapping](../../docs/specifications.md#joint-ids-and-names)

<a id="resources"></a>

## Resources

| Directory | Description | Status |
| --- | --- | --- |
| [Assembly guide](../../docs/diy-assembly/README.md#102-hd) | Main arm video with HD servo substitution and button wiring photo | ✅ Complete |
| [step/](step/) | Part models in parts/; shared assembly in assembly/ | ✅ Complete |
| [printing/](printing/) | STL: [View parts](printing/stl/) · [Download ZIP](printing/star-arm-102-hd-stl.zip) | ✅ Complete |
| [drawings/](../102-ld/drawings/) | Shared LD/HD body drawings (PDF / DWG) | ✅ Complete |
| [robot-description/](robot-description/) | URDF model: [Browse source](robot-description/) · [Download ZIP](robot-description/star-arm-102-ld-hd-urdf.zip) | ✅ Complete |

<a id="bill-of-materials"></a>

## Bill of Materials

The table below lists **32 assembly items** for 102-HD. Missing images are marked pending.

For printed parts, Model / Specification lists the part identifier. Except for Link 6, identifiers match the supplied STEP and STL filenames (without extensions); existing Link 6 files are named `star-arm-102-link6-handle`. The handle support is currently provided as a STEP model. Print settings are not recorded here: take the STL from [printing/stl/](printing/stl/) and slice it for your own printer, because layer height, wall count and infill depend on the machine and filament used.

Printed-part images are rendered from the corresponding STEP models. Fastener images are AI-generated illustrations; refer to the table text for specifications. Click an image to enlarge it.

| No. | Part Name | Model / Specification | Image | Description | Quantity |
| :---: | --- | --- | :---: | --- | :---: |
| 1 | UART bus servo | RP8-U45H-M | <img src="images/rp8-u45h-m.webp" alt="RP8-U45H-M" width="90"> | 12V; 45kg-cm; 118rpm; Dual-shaft; Coreless Motor; 12-bit Magnetic Absolute Encoder; 25T | 4 |
| 2 | UART bus servo | RP8-U45H-M-C028 | <img src="images/rp8-u45h-m-c028.webp" alt="RP8-U45H-M-C028" width="90"> | 12V; 45kg-cm; 118rpm; Dual-shaft Housing (Flat Bottom Cover, No Rear Output Shaft); Coreless Motor; 12-bit Magnetic Absolute Encoder; 25T | 2 |
| 3 | UART bus servo | RP8-U45H-M-C029 | <img src="images/rp8-u45h-m-c029.webp" alt="RP8-U45H-M-C029" width="90"> | 12V; 45kg-cm; 118rpm; Dual-shaft Housing (Flat Bottom Cover, No Rear Output Shaft); Coreless Motor; 12-bit Magnetic Absolute Encoder; D-Type Shaft | 1 |
| 4 | Base bottom plate | star-arm-102-base-bottom | <a href="images/star-arm-102-base-bottom.png"><img src="images/star-arm-102-base-bottom.png" alt="star-arm-102-base-bottom" width="90"></a> | Ivory, PLA 3D printed part | 1 |
| 5 | Base top plate | star-arm-102-base-top | <a href="images/star-arm-102-base-top.png"><img src="images/star-arm-102-base-top.png" alt="star-arm-102-base-top" width="90"></a> | Ivory, PLA 3D printed part | 1 |
| 6 | Link 1 | star-arm-102-link1 | <a href="images/star-arm-102-link1.png"><img src="images/star-arm-102-link1.png" alt="star-arm-102-link1" width="90"></a> | Ivory, PLA 3D printed part | 1 |
| 7 | Link 2 | star-arm-102-link2 | <a href="images/star-arm-102-link2.png"><img src="images/star-arm-102-link2.png" alt="star-arm-102-link2" width="90"></a> | Ivory, PLA 3D printed part | 1 |
| 8 | Link 3 | star-arm-102-link3 | <a href="images/star-arm-102-link3.png"><img src="images/star-arm-102-link3.png" alt="star-arm-102-link3" width="90"></a> | Ivory + black, PLA 3D printed part | 1 |
| 9 | Link 4 | star-arm-102-link4 | <a href="images/star-arm-102-link4.png"><img src="images/star-arm-102-link4.png" alt="star-arm-102-link4" width="90"></a> | Ivory, PLA 3D printed part | 1 |
| 10 | Link 5 | star-arm-102-link5 | <a href="images/star-arm-102-link5.png"><img src="images/star-arm-102-link5.png" alt="star-arm-102-link5" width="90"></a> | Ivory, PLA 3D printed part | 1 |
| 11 | Link 6 | star-arm-102-link6 | <a href="images/star-arm-102-link6-handle.png"><img src="images/star-arm-102-link6-handle.png" alt="star-arm-102-link6-handle" width="90"></a> | Ivory, PLA 3D printed part | 1 |
| 12 | Handle | star-arm-102-handle | <a href="images/star-arm-102-handle.png"><img src="images/star-arm-102-handle.png" alt="star-arm-102-handle" width="90"></a> | Ivory, PLA 3D printed part | 1 |
| 13 | Handle support | [star-arm-102-handle-support](step/parts/star-arm-102-handle-support.step) | <a href="images/star-arm-102-handle-support.png"><img src="images/star-arm-102-handle-support.png" alt="Handle support" width="90"></a> | 3D printed part; supports the handle from below | 1 |
| 14 | Left finger ring | star-arm-102-finger-ring-left | <a href="images/star-arm-102-finger-ring-left.png"><img src="images/star-arm-102-finger-ring-left.png" alt="star-arm-102-finger-ring-left" width="90"></a> | Ivory, PLA 3D printed part | 1 |
| 15 | Right finger ring | star-arm-102-finger-ring-right | <a href="images/star-arm-102-finger-ring-right.png"><img src="images/star-arm-102-finger-ring-right.png" alt="star-arm-102-finger-ring-right" width="90"></a> | Ivory, PLA 3D printed part | 1 |
| 16 | HD button cover | hd-button-cover | <a href="images/hd-button-cover.png"><img src="images/hd-button-cover.png" alt="hd-button-cover" width="90"></a> | Ivory, PLA 3D printed part | 1 |
| 17 | HD button base | hd-button-base | <a href="images/hd-button-base.png"><img src="images/hd-button-base.png" alt="hd-button-base" width="90"></a> | Ivory, PLA 3D printed part | 1 |
| 18 | TTL/USB Servo Adapter | UC-01 | <img src="../../media/uc-01-primary.webp" alt="UC-01" width="90"> | USB Type-C; half-/full-duplex conversion; selectable 3.3 V / 5 V TTL levels; 6–15 V input; 2 × PH2.0 servo ports; reverse-polarity protection<br>XT30 connector | 1 |
| 19 | Button board | UK-01 | <a href="images/uk-01-board.webp"><img src="images/uk-01-board.webp" alt="UK-01 board" width="90"></a> | With socket | 1 |
| 20 | Thrust needle roller bearing | AXK2035+2AS | <img src="../../media/axk2035-2as-bearing.png" alt="AXK2035+2AS thrust needle roller bearing" width="90"> | inner diameter 20 mm, outer diameter 35 mm, thickness 4 mm | 1 |
| 21 | Servo cable | PH2.0 (PH-3Y)<br>120 mm | <a href="../../media/ph-3y-servo-cable-120mm.png"><img src="../../media/ph-3y-servo-cable-120mm-thumbnail.png" alt="PH2.0 120 mm servo cable" width="90"></a> | Black silicone-insulated ribbon cable with black braided sleeving; reversed pin order between ends; 60 × Ø0.08 mm strands per conductor (approx. 22 AWG) | 6 |
| 22 | Servo cable | PH2.0 (PH-3Y)<br>200 mm | <a href="../../media/ph-3y-servo-cable-200mm.png"><img src="../../media/ph-3y-servo-cable-200mm-thumbnail.png" alt="PH2.0 200 mm servo cable" width="90"></a> | Black silicone-insulated ribbon cable with black braided sleeving; reversed pin order between ends; 60 × Ø0.08 mm strands per conductor (approx. 22 AWG) | 2 |
| 23 | Hexagon socket head cap screw | M3 × 22 | <a href="../../media/fasteners/m3-22-socket-head-cap-screw.png"><img src="../../media/fasteners/m3-22-socket-head-cap-screw.png" alt="M3 × 22 hexagon socket head cap screw illustration" width="90"></a> | Black finish | 4 |
| 24 | Hexagon socket head cap screw | M3 × 10 | <a href="../../media/fasteners/m3-10-socket-head-cap-screw.png"><img src="../../media/fasteners/m3-10-socket-head-cap-screw.png" alt="M3 × 10 hexagon socket head cap screw illustration" width="90"></a> | Black finish, property class 12.9 | 1 |
| 25 | Hexagon socket head cap screw | M2 × 10 | <a href="../../media/fasteners/m2-10-socket-head-cap-screw.png"><img src="../../media/fasteners/m2-10-socket-head-cap-screw.png" alt="M2 × 10 Hexagon socket head cap screw illustration" width="90"></a> | Black finish | 8 |
| 26 | Hexagon socket head cap screw | M2 × 8 | <a href="../../media/fasteners/m2-8-socket-head-cap-screw.png"><img src="../../media/fasteners/m2-8-socket-head-cap-screw.png" alt="M2 × 8 hexagon socket head cap screw illustration" width="90"></a> | Black finish | 8 |
| 27 | Phillips countersunk head self-tapping screw | 3 × 12 mm | <a href="../../media/fasteners/3-12-phillips-flat-head-self-tapping-screw.png"><img src="../../media/fasteners/3-12-phillips-flat-head-self-tapping-screw.png" alt="3 × 12 mm Phillips countersunk head self-tapping screw illustration" width="90"></a> | Silver finish; pointed tip | 2 |
| 28 | Phillips pan head machine screw | M3 × 10 | <a href="../../media/fasteners/m3-10-phillips-pan-head-screw.png"><img src="../../media/fasteners/m3-10-phillips-pan-head-screw.png" alt="M3 × 10 Phillips pan head machine screw illustration" width="90"></a> | Black finish, hardened | 1 |
| 29 | Phillips pan head self-tapping screw | 2 × 5 mm | <a href="../../media/fasteners/2-5-phillips-pan-head-blunt-point-self-tapping-screw.png"><img src="../../media/fasteners/2-5-phillips-pan-head-blunt-point-self-tapping-screw.png" alt="2 × 5 mm Phillips pan head self-tapping screw illustration" width="90"></a> | Black finish, hardened; blunt point | 46 |
| 30 | Phillips pan head machine screw | M2 × 4.5 | <a href="../../media/fasteners/m2-4-5-phillips-pan-head-screw.png"><img src="../../media/fasteners/m2-4-5-phillips-pan-head-screw.png" alt="M2 × 4.5 Phillips pan head machine screw illustration" width="90"></a> | Black finish; blue pre-applied threadlocker on approximately the lower two-thirds of the threaded shank (toward the tip) | 35 |
| 31 | Nut | M3 | <a href="../../media/fasteners/m3-nut.png"><img src="../../media/fasteners/m3-nut.png" alt="M3 Nut illustration" width="90"></a> | Black finish | 5 |
| 32 | Washer | M3 (3 × 6 × 0.5 mm) | <a href="../../media/fasteners/m3-6-0-5-stainless-washer.png"><img src="../../media/fasteners/m3-6-0-5-stainless-washer.png" alt="M3 (3 × 6 × 0.5 mm) Washer illustration" width="90"></a> | Stainless steel | 1 |

Found an error in these resources or need help? Contact our [Support Hub](https://fashionstar.com.hk/support/) with your model and the relevant file or item.
