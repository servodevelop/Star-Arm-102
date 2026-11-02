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
- [📋 Standard-gripper Bill of Materials](#bill-of-materials)
- [🖐️ Flexible-gripper Parts](#flexible-gripper-bom)
- [📷 Camera Module (Optional)](#camera-module-bom)
- [🔢 Joint and servo ID mapping](../../docs/specifications.md#joint-ids-and-names)

<a id="resources"></a>

## Resources

| Directory | Description | Status |
| --- | --- | --- |
| [Assembly guide](../../docs/diy-assembly/README.md#102-fl) | Main arm assembly video | ✅ Complete |
| [step/](step/) | Whole-arm STEP models: [Standard gripper](step/star-arm-102-fl-assembly-export-2026-11-01.step) · [Flexible gripper](step/star-arm-102-fl-flexible-gripper-assembly-export-2026-11-01.step) | ✅ Complete |
| [3mf/](3mf/) | 3D printing files (3MF) | — Coming soon |
| [drawings/](drawings/) | PDF / DWG drawings | ✅ Complete |
| [URDF Models](urdf/) | [Download complete URDF package](urdf/downloads/star-arm-102-fl-urdf-2026-10-23.zip?raw=true) · [Browse source](urdf/stararm102-fl-description/) | ✅ Complete |

<a id="bill-of-materials"></a>

## Standard-gripper Bill of Materials

The table below lists **29 assembly items** for the **standard-gripper version of 102-FL**. Missing images are marked pending.

For printed parts, the part name identifies the component. English names in the assembly tree, such as `Link 1`, correspond to the English BOM’s Part Name column.

For printed parts, Model / Specification / Part Identifier lists the part identifier. For example, `Link 1` uses the identifier `star-arm-102-link1`. The `star-arm-102-` prefix identifies the product series.

3MF printing files will be provided in [3mf/](3mf/); they are not yet available. Print settings are not listed here; choose layer height, wall count and infill for your printer and filament.

Printed-part images are rendered from the corresponding STEP models. Fastener images are AI-generated illustrations; refer to the table text for specifications. Click an image to enlarge it.

<table width="100%">
<thead>
<tr>
  <th width="5%">No.</th>
  <th width="17%">Part Name</th>
  <th width="24%">Model / Specification / Part Identifier</th>
  <th width="11%">Image</th>
  <th width="37%">Description</th>
  <th width="6%">Quantity</th>
</tr>
</thead>
<tbody>
<tr>
  <td align="center">1</td>
  <td>UART bus servo</td>
  <td>RX8-U48H-M</td>
  <td align="center"><a href="images/rx8-u48h-m.webp"><img src="images/rx8-u48h-m.webp" alt="RX8-U48H-M" width="90"></a></td>
  <td>12V; 48kg-cm; 70rpm; Dual-shaft; Brushless Motor; 12-bit Magnetic Absolute Encoder; 25T</td>
  <td align="center">2</td>
</tr>
<tr>
  <td align="center">2</td>
  <td>UART bus servo</td>
  <td>RA8-U35H-M</td>
  <td align="center"><a href="images/ra8-u35h-m.png"><img src="images/ra8-u35h-m.png" alt="RA8-U35H-M" width="90"></a></td>
  <td>12V; 35kg-cm; 55rpm; Dual-shaft; Brushed Core Motor; 12-bit Magnetic Absolute Encoder; 25T</td>
  <td align="center">3</td>
</tr>
<tr>
  <td align="center">3</td>
  <td>UART bus servo</td>
  <td>RA8-U35H-M-C047</td>
  <td align="center"><a href="images/ra8-u35h-m-c047.webp"><img src="images/ra8-u35h-m-c047.webp" alt="RA8-U35H-M-C047" width="90"></a></td>
  <td>12V; 35kg-cm; 55rpm; Dual-shaft Housing (Flat Bottom Cover, No Rear Output Shaft); Brushed Core Motor; 12-bit Magnetic Absolute Encoder; 25T</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">4</td>
  <td>UART bus servo</td>
  <td>RA8-U27H-M-C005</td>
  <td align="center"><a href="images/ra8-u27h-m-c005.webp"><img src="images/ra8-u27h-m-c005.webp" alt="RA8-U27H-M-C005" width="90"></a></td>
  <td>12V; 25kg-cm; 72rpm; Dual-shaft Housing (Flat Bottom Cover, No Rear Output Shaft); Brushed Core Motor; 12-bit Magnetic Absolute Encoder; D-Type Shaft</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">5</td>
  <td>Base bottom plate</td>
  <td>star-arm-102-base-bottom</td>
  <td align="center"><a href="images/star-arm-102-base-bottom.png"><img src="images/star-arm-102-base-bottom.png" alt="star-arm-102-base-bottom" width="90"></a></td>
  <td>Ivory, PLA 3D printed part</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">6</td>
  <td>Base top plate</td>
  <td>star-arm-102-base-top</td>
  <td align="center"><a href="images/star-arm-102-base-top.png"><img src="images/star-arm-102-base-top.png" alt="star-arm-102-base-top" width="90"></a></td>
  <td>Ivory, PLA 3D printed part</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">7</td>
  <td>Link 1</td>
  <td>star-arm-102-link1</td>
  <td align="center"><a href="images/star-arm-102-link1.png"><img src="images/star-arm-102-link1.png" alt="star-arm-102-link1" width="90"></a></td>
  <td>Ivory, PLA 3D printed part</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">8</td>
  <td>Link 2</td>
  <td>star-arm-102-link2</td>
  <td align="center"><a href="images/star-arm-102-link2.png"><img src="images/star-arm-102-link2.png" alt="star-arm-102-link2" width="90"></a></td>
  <td>Ivory, PLA 3D printed part</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">9</td>
  <td>Link 3</td>
  <td>star-arm-102-link3</td>
  <td align="center"><a href="images/star-arm-102-link3.png"><img src="images/star-arm-102-link3.png" alt="star-arm-102-link3" width="90"></a></td>
  <td>Ivory + black, PLA 3D printed part</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">10</td>
  <td>Link 4</td>
  <td>star-arm-102-link4</td>
  <td align="center"><a href="images/star-arm-102-link4.png"><img src="images/star-arm-102-link4.png" alt="star-arm-102-link4" width="90"></a></td>
  <td>Ivory, PLA 3D printed part</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">11</td>
  <td>Link 5</td>
  <td>star-arm-102-link5</td>
  <td align="center"><a href="images/star-arm-102-link5.png"><img src="images/star-arm-102-link5.png" alt="star-arm-102-link5" width="90"></a></td>
  <td>Ivory, PLA 3D printed part</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">12</td>
  <td>Link 6</td>
  <td>star-arm-102-link6</td>
  <td align="center"><a href="images/star-arm-102-link6.png"><img src="images/star-arm-102-link6.png" alt="star-arm-102-link6" width="90"></a></td>
  <td>Ivory, PLA 3D printed part</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">13</td>
  <td>Gripper body</td>
  <td>star-arm-102-gripper-body</td>
  <td align="center"><a href="images/star-arm-102-gripper-body.png"><img src="images/star-arm-102-gripper-body.png" alt="star-arm-102-gripper-body" width="90"></a></td>
  <td>Ivory, PLA 3D printed part</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">14</td>
  <td>Fingertip Left</td>
  <td>star-arm-102-fingertip-left</td>
  <td align="center"><a href="images/star-arm-102-fingertip-left.png"><img src="images/star-arm-102-fingertip-left.png" alt="star-arm-102-fingertip-left" width="90"></a></td>
  <td>Ivory, PLA 3D printed part</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">15</td>
  <td>Fingertip Right</td>
  <td>star-arm-102-fingertip-right</td>
  <td align="center"><a href="images/star-arm-102-fingertip-right.png"><img src="images/star-arm-102-fingertip-right.png" alt="star-arm-102-fingertip-right" width="90"></a></td>
  <td>Ivory, PLA 3D printed part</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">16</td>
  <td>Thrust needle roller bearing</td>
  <td>AXK2035+2AS</td>
  <td align="center"><a href="../../media/axk2035-2as-bearing.png"><img src="../../media/axk2035-2as-bearing.png" alt="AXK2035+2AS thrust needle roller bearing" width="90"></a></td>
  <td>inner diameter 20 mm, outer diameter 35 mm, thickness 4 mm</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">17</td>
  <td>TTL/USB Servo Adapter</td>
  <td>UC-01</td>
  <td align="center"><a href="../../media/uc-01-primary.webp"><img src="../../media/uc-01-primary.webp" alt="UC-01" width="90"></a></td>
  <td>USB Type-C; half-/full-duplex conversion; selectable 3.3 V / 5 V TTL levels; 6–15 V input; 2 × PH2.0 servo ports; reverse-polarity protection<br>XT30 connector</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">18</td>
  <td>Servo cable</td>
  <td>PH2.0 (PH-3Y)<br>120 mm</td>
  <td align="center"><a href="../../media/ph-3y-servo-cable-120mm-thumbnail.png"><img src="../../media/ph-3y-servo-cable-120mm-thumbnail.png" alt="PH2.0 120 mm servo cable" width="90"></a></td>
  <td>Black silicone-insulated ribbon cable with black braided sleeving; reversed pin order between ends; 60 × Ø0.08 mm strands per conductor (approx. 22 AWG)</td>
  <td align="center">4</td>
</tr>
<tr>
  <td align="center">19</td>
  <td>Servo cable</td>
  <td>PH2.0 (PH-3Y)<br>200 mm</td>
  <td align="center"><a href="../../media/ph-3y-servo-cable-200mm-thumbnail.png"><img src="../../media/ph-3y-servo-cable-200mm-thumbnail.png" alt="PH2.0 200 mm servo cable" width="90"></a></td>
  <td>Black silicone-insulated ribbon cable with black braided sleeving; reversed pin order between ends; 60 × Ø0.08 mm strands per conductor (approx. 22 AWG)</td>
  <td align="center">3</td>
</tr>
<tr>
  <td align="center">20</td>
  <td>Hexagon socket head cap screw</td>
  <td>M3 × 22</td>
  <td align="center"><a href="../../media/fasteners/m3-22-socket-head-cap-screw.png"><img src="../../media/fasteners/m3-22-socket-head-cap-screw.png" alt="M3 × 22 hexagon socket head cap screw illustration" width="90"></a></td>
  <td>Black finish</td>
  <td align="center">4</td>
</tr>
<tr>
  <td align="center">21</td>
  <td>Hexagon socket head cap screw</td>
  <td>M3 × 10</td>
  <td align="center"><a href="../../media/fasteners/m3-10-socket-head-cap-screw.png"><img src="../../media/fasteners/m3-10-socket-head-cap-screw.png" alt="M3 × 10 hexagon socket head cap screw illustration" width="90"></a></td>
  <td>Black finish, property class 12.9</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">22</td>
  <td>Hexagon socket head cap screw</td>
  <td>M2 × 10</td>
  <td align="center"><a href="../../media/fasteners/m2-10-socket-head-cap-screw.png"><img src="../../media/fasteners/m2-10-socket-head-cap-screw.png" alt="M2 × 10 Hexagon socket head cap screw illustration" width="90"></a></td>
  <td>Black finish</td>
  <td align="center">8</td>
</tr>
<tr>
  <td align="center">23</td>
  <td>Hexagon socket head cap screw</td>
  <td>M2 × 8</td>
  <td align="center"><a href="../../media/fasteners/m2-8-socket-head-cap-screw.png"><img src="../../media/fasteners/m2-8-socket-head-cap-screw.png" alt="M2 × 8 hexagon socket head cap screw illustration" width="90"></a></td>
  <td>Black finish</td>
  <td align="center">16</td>
</tr>
<tr>
  <td align="center">24</td>
  <td>Phillips countersunk head self-tapping screw</td>
  <td>3 × 12 mm</td>
  <td align="center"><a href="../../media/fasteners/3-12-phillips-flat-head-self-tapping-screw.png"><img src="../../media/fasteners/3-12-phillips-flat-head-self-tapping-screw.png" alt="3 × 12 mm Phillips countersunk head self-tapping screw illustration" width="90"></a></td>
  <td>Silver finish; pointed tip</td>
  <td align="center">2</td>
</tr>
<tr>
  <td align="center">25</td>
  <td>Phillips pan head machine screw</td>
  <td>M3 × 10</td>
  <td align="center"><a href="../../media/fasteners/m3-10-phillips-pan-head-screw.png"><img src="../../media/fasteners/m3-10-phillips-pan-head-screw.png" alt="M3 × 10 Phillips pan head machine screw illustration" width="90"></a></td>
  <td>Black finish, hardened</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">26</td>
  <td>Phillips pan head self-tapping screw</td>
  <td>2 × 5 mm</td>
  <td align="center"><a href="../../media/fasteners/2-5-phillips-pan-head-blunt-point-self-tapping-screw.png"><img src="../../media/fasteners/2-5-phillips-pan-head-blunt-point-self-tapping-screw.png" alt="2 × 5 mm Phillips pan head self-tapping screw illustration" width="90"></a></td>
  <td>Black finish, hardened; blunt point</td>
  <td align="center">30</td>
</tr>
<tr>
  <td align="center">27</td>
  <td>Phillips pan head machine screw</td>
  <td>M2 × 4.5</td>
  <td align="center"><a href="../../media/fasteners/m2-4-5-phillips-pan-head-screw.png"><img src="../../media/fasteners/m2-4-5-phillips-pan-head-screw.png" alt="M2 × 4.5 Phillips pan head machine screw illustration" width="90"></a></td>
  <td>Black finish; blue pre-applied threadlocker on approximately the lower two-thirds of the threaded shank (toward the tip)</td>
  <td align="center">47</td>
</tr>
<tr>
  <td align="center">28</td>
  <td>Nut</td>
  <td>M3</td>
  <td align="center"><a href="../../media/fasteners/m3-nut.png"><img src="../../media/fasteners/m3-nut.png" alt="M3 Nut illustration" width="90"></a></td>
  <td>Black finish</td>
  <td align="center">6</td>
</tr>
<tr>
  <td align="center">29</td>
  <td>Washer</td>
  <td>M3 (3 × 6 × 0.5 mm)</td>
  <td align="center"><a href="../../media/fasteners/m3-6-0-5-stainless-washer.png"><img src="../../media/fasteners/m3-6-0-5-stainless-washer.png" alt="M3 (3 × 6 × 0.5 mm) Washer illustration" width="90"></a></td>
  <td>Stainless steel</td>
  <td align="center">2</td>
</tr>
</tbody>
</table>
<a id="flexible-gripper-bom"></a>

## Flexible-gripper Parts

The **7 mechanical parts** below replace the standard gripper body and both fingertips (items 13–15 above). Shared servos are not counted again. Installation fastener specifications and quantities await verification, so this is not a complete retrofit purchasing BOM. Quantities are per flexible gripper.

Images are rendered from the [flexible-gripper whole-arm STEP](step/star-arm-102-fl-flexible-gripper-assembly-export-2026-11-01.step). Model / Specification / Part Identifier uses the English component labels from the STEP assembly tree for easy identification. The body, links and gears are ivory PLA 3D printed parts; both fingertips are white TPU 90A 3D printed parts. The left and right links have identical geometry and are distinguished by their installation positions, with one of each required.

<table width="100%">
<thead>
<tr>
  <th width="5%">No.</th>
  <th width="17%">Part Name</th>
  <th width="24%">Model / Specification / Part Identifier</th>
  <th width="11%">Image</th>
  <th width="37%">Description</th>
  <th width="6%">Quantity</th>
</tr>
</thead>
<tbody>
<tr>
  <td align="center">1</td>
  <td>Flexible Gripper Body</td>
  <td>Flexible Gripper Body</td>
  <td align="center"><a href="images/flexible-gripper-body.png"><img src="images/flexible-gripper-body.png" alt="Flexible Gripper Body" width="90"></a></td>
  <td>Ivory, PLA 3D printed part</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">2</td>
  <td>Flexible Gripper Link Left</td>
  <td>Flexible Gripper Link Left</td>
  <td align="center"><a href="images/flexible-gripper-link-left.png"><img src="images/flexible-gripper-link-left.png" alt="Flexible Gripper Link Left" width="90"></a></td>
  <td>Ivory, PLA 3D printed part</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">3</td>
  <td>Flexible Gripper Link Right</td>
  <td>Flexible Gripper Link Right</td>
  <td align="center"><a href="images/flexible-gripper-link-right.png"><img src="images/flexible-gripper-link-right.png" alt="Flexible Gripper Link Right" width="90"></a></td>
  <td>Ivory, PLA 3D printed part</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">4</td>
  <td>Flexible Gripper Gear Left</td>
  <td>Flexible Gripper Gear Left</td>
  <td align="center"><a href="images/flexible-gripper-gear-left.png"><img src="images/flexible-gripper-gear-left.png" alt="Flexible Gripper Gear Left" width="90"></a></td>
  <td>Ivory, PLA 3D printed part</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">5</td>
  <td>Flexible Gripper Gear Right</td>
  <td>Flexible Gripper Gear Right</td>
  <td align="center"><a href="images/flexible-gripper-gear-right.png"><img src="images/flexible-gripper-gear-right.png" alt="Flexible Gripper Gear Right" width="90"></a></td>
  <td>Ivory, PLA 3D printed part</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">6</td>
  <td>Flexible Gripper Fingertip Left</td>
  <td>Flexible Gripper Fingertip Left</td>
  <td align="center"><a href="images/flexible-gripper-fingertip-left.png"><img src="images/flexible-gripper-fingertip-left.png" alt="Flexible Gripper Fingertip Left" width="90"></a></td>
  <td>White, TPU 90A 3D printed part</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">7</td>
  <td>Flexible Gripper Fingertip Right</td>
  <td>Flexible Gripper Fingertip Right</td>
  <td align="center"><a href="images/flexible-gripper-fingertip-right.png"><img src="images/flexible-gripper-fingertip-right.png" alt="Flexible Gripper Fingertip Right" width="90"></a></td>
  <td>White, TPU 90A 3D printed part</td>
  <td align="center">1</td>
</tr>
</tbody>
</table>
<a id="camera-module-bom"></a>

## Camera Module (Optional)

**Optional; excluded from the 29 standard-gripper assembly items.** The following parts form one first-person camera module mounted above the gripper, with one of each required. The camera model, interface and performance specifications await confirmation. The camera image is a STEP shape reference; its actual appearance depends on the selected model. Installation cables and fasteners will be checked after camera selection.

The third-person desktop camera base serves a different mounting arrangement and is excluded here; see the [camera-module directory](../camera-module/) for those resources.

<table width="100%">
<thead>
<tr>
  <th width="5%">No.</th>
  <th width="17%">Part Name</th>
  <th width="24%">Model / Specification / Part Identifier</th>
  <th width="11%">Image</th>
  <th width="37%">Description</th>
  <th width="6%">Quantity</th>
</tr>
</thead>
<tbody>
<tr>
  <td align="center">1</td>
  <td>First-person camera base (snap-fit)</td>
  <td>first-person-camera-base-snap-fit</td>
  <td align="center"><a href="images/first-person-camera-base.png"><img src="images/first-person-camera-base.png" alt="First-person camera base (snap-fit)" width="90"></a></td>
  <td>Ivory, PLA 3D printed part</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">2</td>
  <td>First-person camera cover (snap-fit)</td>
  <td>first-person-camera-cover-snap-fit</td>
  <td align="center"><a href="images/first-person-camera-cover.png"><img src="images/first-person-camera-cover.png" alt="First-person camera cover (snap-fit)" width="90"></a></td>
  <td>Ivory, PLA 3D printed part</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">3</td>
  <td>Camera module</td>
  <td>To be confirmed</td>
  <td align="center"><a href="images/first-person-camera-module.png"><img src="images/first-person-camera-module.png" alt="Camera module" width="90"></a></td>
  <td>Model, interface and performance specifications to be confirmed; STEP shape reference</td>
  <td align="center">1</td>
</tr>
</tbody>
</table>
Found an error in these resources or need help? Contact our [Support Hub](https://fashionstar.com.hk/support/) with your model and the relevant file or item.
