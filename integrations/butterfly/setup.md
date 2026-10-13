# Setup and first task

[Integration overview](README.md) · [Compatibility](compatibility.md) · [Troubleshooting](troubleshooting.md)

This is an orientation guide to the partner application. The referenced upstream deployment procedure has not yet been reproduced by Fashion Star.

## 1. Obtain the matching application revision

Clone the application into a separate directory, outside your Star Arm 102 checkout:

```bash
git clone https://github.com/butterfly-community/robot-arm.git butterfly-robot-arm
cd butterfly-robot-arm
git checkout --detach 08498c31c56cf339601851851225bf111f89c82d
```

This selects the documentation reference revision. It does not install dependencies or start the robot.

## 2. Prepare the upstream environment

Follow the matching [Docker deployment document](https://github.com/butterfly-community/robot-arm/blob/08498c31c56cf339601851851225bf111f89c82d/docs/DOCKER.md), including its build order, model assets, device configuration, and service settings. Configure a model service only if you want natural-language operation.

Keep credentials in the upstream local environment configuration. Use your host's actual network address rather than assuming that the example address in the partner documentation matches your machine. Its start command assumes service images have already been built.

## 3. Explore without hardware

Use the partner's documented software-only mode and supplied scene data first. Confirm that the browser can display the scene, select targets, and follow a planned task using virtual feedback. Confirm image and tool-call support before trying the natural-language interface.

This verifies application flow only. It does not validate camera calibration, physical contact, or grasp stability.

## 4. Connect a confirmed hardware configuration

After checking [compatibility](compatibility.md), follow the partner's device setup and [coordinate conventions](https://github.com/butterfly-community/robot-arm/blob/08498c31c56cf339601851851225bf111f89c82d/docs/STARARM-102.md). Check actual joint feedback and camera data before requesting motion. Run only the intended control application against the servo port.

Use the partner's camera-to-robot calibration process and the correct calibration-board dimensions. Recalibrate when the camera/robot mounting relationship changes. The process moves the arm; prepare a clear workspace and an accessible servo-power cutoff as described in the [hardware setup guide](../../docs/getting-started.md#connect).

## 5. Try one pick-and-place task

Begin with one visible object and one clear destination. Inspect the selected target, planned motion, device feedback, and camera result. Once explicit page-based operation works, describe the same task through the natural-language interface.

Record the application revision, exact arm/camera configuration, calibration setup, and observed outcome. A completed chat response or software task status alone does not establish that the physical grasp succeeded.
