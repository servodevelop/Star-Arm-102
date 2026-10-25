# Try the pretrained ACT block-placement model

[← examples](../)　|　<sub>**English** / [简体中文](README.zh.md)</sub>

**Contents:**

- [🎬 Watch the demo](#page-section-1)
- [📋 What you need](#page-section-2)
- [🤖 Model card](#page-section-3)
- [🧩 Match the scene](#page-section-4)

**Try a supplied policy without retraining.** This example uses a Star Arm 102-FL and two cameras to place a block in the center of a prepared workspace.

**[Run the model](inference.md) · [Download the release](https://github.com/servodevelop/Star-Arm-102/releases/tag/act-pick-v1.0.0) · [Train your own task](../../single-arm/README.md#record)**

<a id="page-section-1"></a>

## Watch the demo

[![ACT demonstration workspace](docs/images/setup-front.jpg)](https://github.com/user-attachments/assets/6774384d-f437-4aa9-a364-cd66eba965f7)

[Play the original demonstration](https://github.com/user-attachments/assets/6774384d-f437-4aa9-a364-cd66eba965f7). The [release](https://github.com/servodevelop/Star-Arm-102/releases/tag/act-pick-v1.0.0) also contains the downloadable video `stararm102_act_trained_demo.mp4`.

<a id="page-section-2"></a>

## What you need

- A Star Arm 102-FL with a secure base, its matching supply, and a USB data connection.
- Two RGB cameras: `up` (overhead) and `front` (frontal), each at **640 × 480, 30 FPS**.
- A workspace, block, placement target, and camera views matching the photographs below.
- Ubuntu 22.04, an NVIDIA GPU with a compatible driver for the saved CUDA configuration, and the release-compatible LeRobot environment described in [inference](inference.md).
- A leader is optional for autonomous inference; it is useful for manual demonstrations or resets after separate calibration.

Setup and calibration are required before motion. This is a task-specific demo, and a different block, camera position, lighting, or calibration can change the result. No measured success rate is published in this release.

<a id="page-section-3"></a>

## Model card

| Field | Released information |
| --- | --- |
| Policy | ACT, checkpoint at 100,000 training steps |
| Robot | Star Arm 102-FL, release-compatible 0.0.1 robot plugin |
| State / action | 7 position channels: `Motor_0`…`Motor_5`, `gripper` |
| Image inputs | `observation.images.up`, `observation.images.front` |
| Model archive | `stararm102_pick_act_torch271.tar.gz` |
| Integrity | [SHA256SUMS.txt](SHA256SUMS.txt) |
| Download location | GitHub release `act-pick-v1.0.0`; no Hugging Face model repository is required for this example |
| Training configuration | Included as `train_config.json`; training dataset and full environment lock are not supplied. See [training scope](training.md) |

Keep the weights, configuration, and processor files together. The refactored `stararm102_fl` plugin is **not** a drop-in replacement for this model.

<a id="page-section-4"></a>

## Match the scene

![Overhead camera and arm from the side](docs/images/setup-side.jpg)

![Oblique view of the cameras, arm, and block workspace](docs/images/setup-oblique.jpg)

[Start installation and the first trial →](inference.md)

The original [Chinese customer guide (DOCX)](docs/Star_Arm_102_ACT_客户运行指南.docx) remains available as supplementary material. Use the English inference guide for the current command sequence.

[Historical Chinese material (not the current operating guide)](legacy-guide.zh.md)
