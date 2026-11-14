# Real-browser pick-and-place report

← [vla-arms-agent](../README.md) · <sub>**English** / [简体中文](GRASP_TEST_REPORT.zh.md)</sub>

Test date: 2026-11-14.

## Result

All 5 task rounds completed, comprising 11 completed pick-and-place actions including an additional placement correction. Whole-round completion was 100%. There were 14 actual grasp attempts, of which 11 transported the object (78.6%); the AI recovered from 3 slips autonomously. Work-pose gripper-close commands are excluded. No person moved the object or substituted actions during execution. Completion was checked against grasping, transporting, and releasing into the target area; placement precision was not an acceptance condition.

## Per-action timing

Times are seconds. Center and red-area placements are timed separately; additional corrections are separate actions. Whole-round time is not divided equally.

| Round | Action within round | Destination | Duration | Result and notes |
| --- | ---: | --- | ---: | --- |
| 1 | 1 | Center box | 117.2 | Completed |
| 1 | 2 | Red area | 55.9 | Completed |
| 2 | 1 | Center box | 134.1 | Completed |
| 2 | 2 | Red area | 59.4 | Completed |
| 3 | 1 | Center box | 128.3 | Completed |
| 3 | 2 | Red area | 56.6 | Completed |
| 4 | 1 | Center box | 137.5 | Completed |
| 4 | 2 | Red area | 98.9 | Placement too far left; AI added a correction |
| 4 | 3 | Red-area correction | 226.0 | Completed, including regrasping after 2 slips |
| 5 | 1 | Center box | 211.1 | Completed, including regrasping after 1 slip |
| 5 | 2 | Red area | 64.0 | Completed |

| Round | Return-to-work and close total | Full round | Final result |
| --- | ---: | ---: | --- |
| 1 | 11.9 | 185.0 | Completed |
| 2 | 9.7 | 203.3 | Completed |
| 3 | 9.6 | 194.5 | Completed |
| 4 | 28.0 | 490.4 | Completed |
| 5 | 13.7 | 288.8 | Completed |

Mean first action: 145.7 seconds; mean second action: 67.0 seconds. Across all individual pick-and-place actions, the mean was 117.2 seconds, ranging from 55.9 to 226.0 seconds.

## Timing and conditions

The first action runs from sending the task to center-placement confirmation. The second runs from that confirmation to red-area placement confirmation. Each includes capture, model decisions, pose corrections, execution, release, and verification. Returning to work is separate. Additional correction runs from the decision to regrasp until its placement confirmation, including retries. Boundaries use page conversation timestamps checked against images. Human review waits between rounds are excluded.

All rounds used one real page and conversation, a Star Arm 102-FL follower, and external and wrist cameras bound at 1280×720 and 30 FPS, switching capture as needed. Model: gpt-6-astra, reasoning effort medium.

- Round 1 prompt included the forward-overreach correction reminder.
- Round 2 prompt included the forward-overreach correction reminder.
- Round 3 prompt included the forward-overreach correction reminder.
- Round 4 prompt included the forward-overreach correction reminder.
- Round 5 also added the user's instruction to lift before translating and avoid dragging across the table.

Total execution across rounds was 1362.0 seconds. Model requests accounted for 1184.0 seconds (86.9%). The remainder includes cameras, serial actions, movement waits, and page processing.

Raw timestamps, feedback, tool results, and images are stored in `temp/five-rounds/round-*/`. Recording and summary code is [task-report.mjs](../tests/task-report.mjs); see [testing](../tests/README.md) for usage.
