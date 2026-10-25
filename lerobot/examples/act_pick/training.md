# Train your own ACT task

[Try the supplied policy first](inference.md) · [Choose a LeRobot integration](../../README.md)

To collect a new dataset and train your own task, follow the [complete LeRobot tutorial](../../single-arm/README.md#record). This page explains how that workflow relates to the supplied ACT release.

## What is available now

- The released 100,000-step ACT checkpoint and [scene photographs](README.md).
- [Calibration and inference](inference.md) for the release-compatible plugins.
- A [recording, data review, and training workflow](../../single-arm/README.md#record) for the refactored HD/FL integration. Its dataset has different joint features and is not interchangeable with the released model.

The archive includes `train_config.json`: 100,000 steps, batch size 8, seed 1000, four data workers, ACT chunk size 100, and AdamW learning rate `1e-5`. It also contains the policy configuration and normalization processors. The dataset path in that file points to the original training machine; it is not a downloadable dataset URL.

The release does not include the training dataset, a complete software environment lock, or an evaluated success-rate report. The recorded configuration is useful reference material, but those missing pieces prevent a claim of exact reproducibility.

## Workflow for a new task

1. Select one plugin generation and save its package versions and calibration IDs.
2. Fix the cameras, workspace, objects, and task definition. Keep camera names and image settings consistent.
3. Verify small-motion teleoperation and record a short sample before collecting a full dataset.
4. Inspect images, joint values, task completion, and timestamps. Collect varied demonstrations within the task you intend to evaluate.
5. Train ACT against that dataset and save the training configuration, checkpoint, processor files, and environment together.
6. Evaluate supervised trials in the same setup. Record attempts, successes, failure types, and setup changes before making performance claims.

For the general workflow, see the [official LeRobot documentation](https://huggingface.co/docs/lerobot/). Match commands to the LeRobot version you installed.

## Continue with your own task

Follow [recording](../../single-arm/README.md#record), [review and replay](../../single-arm/README.md#replay), [ACT training](../../single-arm/README.md#train), and [evaluation](../../single-arm/README.md#evaluate) in order. The refactored workflow still needs end-to-end hardware validation; completing this documentation does not establish training performance.
