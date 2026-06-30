# Hardware

This directory stores hardware-related resources for Star Arm 102, making it easy to check the parts list, view CAD drawings, and refer to assembly documentation.



## Directory Overview

- [parts/](./parts/): STEP files for parts and BOM
- [cad/](./cad/README.md): CAD engineering drawings
- [assembly/](./assembly/README.md): Assembly instructions and reference materials

## Navigation

### 1. Parts List

If you want to understand which parts are required for this robotic arm and how many of each part are needed, start with `Star Arm 102-LD_BOM.xlsx`. The following two tables are provided for convenient browsing on GitHub: the main BOM and the accessory list.

#### Main BOM

| No. | Item | Notes | Qty |
|:---|:---|:---|:---|
| 1 | 3D-printed part (star102 base bottom) | - | 1 |
| 2 | 3D-printed part (star102 base top) | - | 1 |
| 3 | 3D-printed part (star102_link1) | - | 1 |
| 4 | 3D-printed part (star102_link2) | - | 1 |
| 5 | 3D-printed part (star102_link3) | - | 1 |
| 6 | 3D-printed part (star102_link4) | - | 1 |
| 7 | 3D-printed part (star102_link5) | - | 1 |
| 8 | 3D-printed part (star102_link6 handle) | - | 1 |
| 9 | 3D-printed part (star102 handle) | - | 1 |
| 10 | 3D-printed part (star102 left finger ring) | - | 1 |
| 11 | 3D-printed part (star102 right finger ring) | - | 1 |
| 12 | PCBD | UC-01, 0.75 mm² 5.5 x 2.1 female connector | 1 |
| 13 | Cable | L=120 mm black braided cable | 5 |
| 14 | Cable | L=200 mm black braided cable | 2 |
| 15 | Screw | HSCS M3*10, grade 12.9 hex socket head cap screw | 1 |
| 16 | Screw | M3*22 black hex socket screw | 4 |
| 17 | Screw | M3*8 hardened black Phillips screw | 1 |
| 18 | Screw | PB2.0*5 hardened black countersunk self-tapping Phillips screw | 39 |
| 19 | Screw | M2*4.5 pre-applied threadlocker black countersunk Phillips screw | 35 |
| 20 | Screw | M2*8 black hex socket screw | 16 |
| 21 | Screw | M3*8 self-tapping Phillips screw | 2 |
| 22 | Nut | M3 black locknut | 5 |
| 23 | Washer | M3 stainless steel | 1 |
| 24 | RA8-U01H-M | - | 4 |
| 25 | RA8-U02H-M | - | 1 |
| 26 | RA8-U03H-M | - | 2 |

#### Accessory List

| No. | Item | Notes | Qty |
|:---|:---|:---|:---|
| 27 | Threadlocker | - | 1 |
| 28 | Woodworking clamp | - | 2 |
| 29 | Spare PCBD | UC-01 | 1 |
| 30 | Spare power cable | XT30 power adapter cable, 0.25 m | 1 |
| 31 | Data cable | USB to Type-C data cable | 1 |
| 32 | Cable | PH-3Y dual-end reverse 60-core 0.08 black silicone ribbon cable, L=200 mm black braided cable | 1 |
| 33 | No. 7 screw kit | M2*8 black hex socket screw, 8 pcs | 1 |
| 34 | No. 8 screw kit | M2*4.5 pre-applied threadlocker black countersunk Phillips screw, 16 pcs | 1 |
| 35 | No. 9 screw kit | PB2.0*5 hardened black countersunk self-tapping Phillips screw, 16 pcs | 1 |
| 36 | Mouse pad | - | 1 |

- [MakerWorld Models](https://makerworld.com.cn/zh/models/2366043-xing-bi-102-ld?from=search#profileId-2682765): Download the 3D-printable files for Star Arm 102-LD here. You can use them to replace parts or assemble the robotic arm yourself.

### 2. Open STEP Files

The `parts/` directory provides several editable STEP files. Users can modify them for their own mounting scenario, base shape, or hand size. Open these files with common CAD software, adjust them as needed, and then export STL or another format for 3D printing.

| File | Description | Use Case |
|:---|:---|:---|
| [First-Person_Camera_Mount_Base.STEP](./parts/First-Person_Camera_Mount_Base.STEP) | First-person camera mount base | Mounts the first-person camera. Adjust it for the camera size or mounting position. |
| [First-Person_Camera_Mount_Top_Cover.STEP](./parts/First-Person_Camera_Mount_Top_Cover.STEP) | First-person camera mount top cover | Works with the camera mount base to secure the camera. |
| [StarArm102_Base_Bottom.STEP](./parts/StarArm102_Base_Bottom.STEP) | Lower half of the robotic arm base | Modify the bottom structure for the actual mounting method. |
| [StarArm102_Base_Top.STEP](./parts/StarArm102_Base_Top.STEP) | Upper half of the robotic arm base | Assemble it with the modified StarArm102_Base_Bottom to check for interference. |
| [StarArm102_Base_Support.STEP](./parts/StarArm102_Base_Support.STEP) | Robotic arm base support | Used to place the handle when homing; users can print it themselves. |
| [StarArm102_Handle.STEP](./parts/StarArm102_Handle.STEP) | Handle | Adjust it for the user's palm size and grip preference. |
| [StarArm102_Finger_Ring_Left.STEP](./parts/StarArm102_Finger_Ring_Left.STEP) | Left finger ring | Adjust it for the user's left-hand finger size and comfort. |
| [StarArm102_Finger_Ring_Right.STEP](./parts/StarArm102_Finger_Ring_Right.STEP) | Right finger ring | Adjust it for the user's right-hand finger size and comfort. |

> Keep a backup of the original files before editing. If you modify the camera mounts, base, or handle structure, check assembly clearance, screw-hole positions, and motion space before printing to avoid interference with the robotic arm's range of motion.


### 3. CAD and Engineering Drawings

If you want to view the overall structure or check dimensions, go to [cad/README.md](./cad/README.md).


### 4. Assembly Instructions

Assembly instructions are still being prepared. In the future, users will be able to purchase a parts kit and assemble their own robotic arm.


