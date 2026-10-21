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
- [🔢 Joint and servo ID mapping](../../docs/specifications.md#joint-ids-and-names)

<a id="resources"></a>

## Resources

| Directory | Description | Status |
| --- | --- | --- |
| [Assembly guide](../../docs/diy-assembly/README.md#102-ld) | Main arm assembly video | ✅ Complete |
| [step/](step/) | Part models in parts/; shared assembly in assembly/ | ✅ Complete |
| [stl/](stl/) | [Download all STL files (12 parts)](stl/downloads/star-arm-102-ld-stl-2026-10-21.zip?raw=true) · [Browse individual STL files](stl/) | ✅ Complete |
| [drawings/](drawings/) | PDF / DWG drawings | ✅ Complete |
| [robot-description/](robot-description/) | URDF model: [Download complete URDF package](robot-description/downloads/star-arm-102-ld-hd-urdf-2026-10-21.zip?raw=true) · [Browse source](robot-description/stararm102-ld-hd-description/) | ✅ Complete |

<a id="bill-of-materials"></a>

## Bill of Materials

The table below lists **29 assembly items** for 102-LD. Missing images are marked pending.

For printed parts, the part name identifies the component. English names in the assembly tree, such as `Link 1`, correspond to the English BOM’s Part Name column.

For printed parts, Model / Specification / Part Identifier lists the part identifier, matching the supplied STEP and STL filenames (without extensions). For example, `Link 1` uses the identifier `star-arm-102-link1`. The `star-arm-102-` prefix identifies the product series when files are downloaded separately. All 12 printed parts, including the handle rest, are available as STEP and STL files. The STL ZIP contains the same 12 files as the stl/ directory.

Print settings are not recorded here: take the STL from [stl/](stl/) and slice it for your own printer, because layer height, wall count and infill depend on the machine and filament used.

Printed-part images are rendered from the corresponding STEP models. Fastener images are AI-generated illustrations; refer to the table text for specifications. Click an image to enlarge it.

| No. | Part Name | Model / Specification / Part Identifier | Image | Description | Quantity |
| :---: | --- | --- | :---: | --- | :---: |
| 1 | UART bus servo | RA8-U01H-M | <img src="images/ra8-u01h-m.webp" alt="RA8-U01H-M" width="90"> | 12V; Dual-shaft; No Motor (No Torque Output); 12-bit Magnetic Absolute Encoder; 25T | 4 |
| 2 | UART bus servo | RA8-U02H-M | <img src="images/ra8-u02h-m.webp" alt="RA8-U02H-M" width="90"> | 12V; Dual-shaft Housing (Flat Bottom Cover, No Rear Output Shaft); No Motor (No Torque Output); 12-bit Magnetic Absolute Encoder; D-Type Shaft | 1 |
| 3 | UART bus servo | RA8-U03H-M | <img src="images/ra8-u03h-m.webp" alt="RA8-U03H-M" width="90"> | 12V; Dual-shaft Housing (Flat Bottom Cover, No Rear Output Shaft); No Motor (No Torque Output); 12-bit Magnetic Absolute Encoder; 25T | 2 |
| 4 | Base bottom plate | star-arm-102-base-bottom | <a href="images/star-arm-102-base-bottom.png"><img src="images/star-arm-102-base-bottom.png" alt="star-arm-102-base-bottom" width="90"></a> | Ivory, PLA 3D printed part | 1 |
| 5 | Base top plate | star-arm-102-base-top | <a href="images/star-arm-102-base-top.png"><img src="images/star-arm-102-base-top.png" alt="star-arm-102-base-top" width="90"></a> | Ivory, PLA 3D printed part | 1 |
| 6 | Link 1 | star-arm-102-link1 | <a href="images/star-arm-102-link1.png"><img src="images/star-arm-102-link1.png" alt="star-arm-102-link1" width="90"></a> | Ivory, PLA 3D printed part | 1 |
| 7 | Link 2 | star-arm-102-link2 | <a href="images/star-arm-102-link2.png"><img src="images/star-arm-102-link2.png" alt="star-arm-102-link2" width="90"></a> | Ivory, PLA 3D printed part | 1 |
| 8 | Link 3 | star-arm-102-link3 | <a href="images/star-arm-102-link3.png"><img src="images/star-arm-102-link3.png" alt="star-arm-102-link3" width="90"></a> | Ivory + black, PLA 3D printed part | 1 |
| 9 | Link 4 | star-arm-102-link4 | <a href="images/star-arm-102-link4.png"><img src="images/star-arm-102-link4.png" alt="star-arm-102-link4" width="90"></a> | Ivory, PLA 3D printed part | 1 |
| 10 | Link 5 | star-arm-102-link5 | <a href="images/star-arm-102-link5.png"><img src="images/star-arm-102-link5.png" alt="star-arm-102-link5" width="90"></a> | Ivory, PLA 3D printed part | 1 |
| 11 | Link 6 | star-arm-102-link6 | <a href="images/star-arm-102-link6.png"><img src="images/star-arm-102-link6.png" alt="star-arm-102-link6" width="90"></a> | Ivory, PLA 3D printed part | 1 |
| 12 | Handle | star-arm-102-handle | <a href="images/star-arm-102-handle.png"><img src="images/star-arm-102-handle.png" alt="star-arm-102-handle" width="90"></a> | Ivory, PLA 3D printed part | 1 |
| 13 | Handle rest | star-arm-102-handle-rest | <a href="images/star-arm-102-handle-rest.png"><img src="images/star-arm-102-handle-rest.png" alt="Handle rest" width="90"></a> | Ivory, PLA 3D printed part | 1 |
| 14 | Left finger ring | star-arm-102-finger-ring-left | <a href="images/star-arm-102-finger-ring-left.png"><img src="images/star-arm-102-finger-ring-left.png" alt="star-arm-102-finger-ring-left" width="90"></a> | Ivory, PLA 3D printed part | 1 |
| 15 | Right finger ring | star-arm-102-finger-ring-right | <a href="images/star-arm-102-finger-ring-right.png"><img src="images/star-arm-102-finger-ring-right.png" alt="star-arm-102-finger-ring-right" width="90"></a> | Ivory, PLA 3D printed part | 1 |
| 16 | Thrust needle roller bearing | AXK2035+2AS | <img src="../../media/axk2035-2as-bearing.png" alt="AXK2035+2AS thrust needle roller bearing" width="90"> | inner diameter 20 mm, outer diameter 35 mm, thickness 4 mm | 1 |
| 17 | TTL/USB Servo Adapter | UC-01 | <img src="../../media/uc-01-primary.webp" alt="UC-01" width="90"> | USB Type-C; half-/full-duplex conversion; selectable 3.3 V / 5 V TTL levels; 6–15 V input; 2 × PH2.0 servo ports; reverse-polarity protection<br>DC power lead: 0.75 mm², 5.5 × 2.1 mm female, 0.15 m | 1 |
| 18 | Servo cable | PH2.0 (PH-3Y)<br>120 mm | <a href="../../media/ph-3y-servo-cable-120mm.png"><img src="../../media/ph-3y-servo-cable-120mm-thumbnail.png" alt="PH2.0 120 mm servo cable" width="90"></a> | Black silicone-insulated ribbon cable with black braided sleeving; reversed pin order between ends; 60 × Ø0.08 mm strands per conductor (approx. 22 AWG) | 5 |
| 19 | Servo cable | PH2.0 (PH-3Y)<br>200 mm | <a href="../../media/ph-3y-servo-cable-200mm.png"><img src="../../media/ph-3y-servo-cable-200mm-thumbnail.png" alt="PH2.0 200 mm servo cable" width="90"></a> | Black silicone-insulated ribbon cable with black braided sleeving; reversed pin order between ends; 60 × Ø0.08 mm strands per conductor (approx. 22 AWG) | 2 |
| 20 | Hexagon socket head cap screw | M3 × 22 | <a href="../../media/fasteners/m3-22-socket-head-cap-screw.png"><img src="../../media/fasteners/m3-22-socket-head-cap-screw.png" alt="M3 × 22 hexagon socket head cap screw illustration" width="90"></a> | Black finish | 4 |
| 21 | Hexagon socket head cap screw | M3 × 10 | <a href="../../media/fasteners/m3-10-socket-head-cap-screw.png"><img src="../../media/fasteners/m3-10-socket-head-cap-screw.png" alt="M3 × 10 hexagon socket head cap screw illustration" width="90"></a> | Black finish, property class 12.9 | 1 |
| 22 | Hexagon socket head cap screw | M2 × 10 | <a href="../../media/fasteners/m2-10-socket-head-cap-screw.png"><img src="../../media/fasteners/m2-10-socket-head-cap-screw.png" alt="M2 × 10 Hexagon socket head cap screw illustration" width="90"></a> | Black finish | 8 |
| 23 | Hexagon socket head cap screw | M2 × 8 | <a href="../../media/fasteners/m2-8-socket-head-cap-screw.png"><img src="../../media/fasteners/m2-8-socket-head-cap-screw.png" alt="M2 × 8 hexagon socket head cap screw illustration" width="90"></a> | Black finish | 16 |
| 24 | Phillips countersunk head self-tapping screw | 3 × 12 mm | <a href="../../media/fasteners/3-12-phillips-flat-head-self-tapping-screw.png"><img src="../../media/fasteners/3-12-phillips-flat-head-self-tapping-screw.png" alt="3 × 12 mm Phillips countersunk head self-tapping screw illustration" width="90"></a> | Silver finish; pointed tip | 2 |
| 25 | Phillips pan head machine screw | M3 × 10 | <a href="../../media/fasteners/m3-10-phillips-pan-head-screw.png"><img src="../../media/fasteners/m3-10-phillips-pan-head-screw.png" alt="M3 × 10 Phillips pan head machine screw illustration" width="90"></a> | Black finish, hardened | 1 |
| 26 | Phillips pan head self-tapping screw | 2 × 5 mm | <a href="../../media/fasteners/2-5-phillips-pan-head-blunt-point-self-tapping-screw.png"><img src="../../media/fasteners/2-5-phillips-pan-head-blunt-point-self-tapping-screw.png" alt="2 × 5 mm Phillips pan head self-tapping screw illustration" width="90"></a> | Black finish, hardened; blunt point | 39 |
| 27 | Phillips pan head machine screw | M2 × 4.5 | <a href="../../media/fasteners/m2-4-5-phillips-pan-head-screw.png"><img src="../../media/fasteners/m2-4-5-phillips-pan-head-screw.png" alt="M2 × 4.5 Phillips pan head machine screw illustration" width="90"></a> | Black finish; blue pre-applied threadlocker on approximately the lower two-thirds of the threaded shank (toward the tip) | 35 |
| 28 | Nut | M3 | <a href="../../media/fasteners/m3-nut.png"><img src="../../media/fasteners/m3-nut.png" alt="M3 Nut illustration" width="90"></a> | Black finish | 5 |
| 29 | Washer | M3 (3 × 6 × 0.5 mm) | <a href="../../media/fasteners/m3-6-0-5-stainless-washer.png"><img src="../../media/fasteners/m3-6-0-5-stainless-washer.png" alt="M3 (3 × 6 × 0.5 mm) Washer illustration" width="90"></a> | Stainless steel | 1 |

Found an error in these resources or need help? Contact our [Support Hub](https://fashionstar.com.hk/support/) with your model and the relevant file or item.
