# vla-arms-agent

← [Star Arm 102](../README.md) · <sub>**English** / [简体中文](README.zh.md)</sub>

[Online workbench](https://vla-arms-agent.vercel.app) · [Source repository](https://github.com/servodevelop/Star-Arm-102/tree/main/vla)

**Use natural language to guide a robot arm through visual pick-and-place tasks.**

vla-arms-agent is an AI workbench for the Star Arm 102-FL follower arm. Connect the arm, an external camera, and a wrist camera, then describe a task in the browser. The AI combines camera images with motor feedback to adjust the gripper, pick up an object, and place it in a designated area.

> Move the sponge to the center box, then place it in the red box. If it is already in the center box, move it directly to the red box.

Task conversations, live images, robot poses, and execution progress share one page. Follow the AI's actions, add instructions during execution, or use manual controls to explore each joint.

Contents

- [🤖 Features](#one-page-for-observation-and-control)
- [🔌 Equipment](#what-to-prepare)
- [🚀 Getting started](#getting-started)
- [🛠️ Development guide](docs/DEVELOPMENT.md)

## From an instruction to a complete pick-and-place task

The AI observes and adjusts throughout the task:

1. **Identify the target.** The external camera covers the workspace; the wrist camera shows objects near the gripper.
2. **Choose a grasp.** Use both views to determine position, orientation, and opening. Contact can help locate the object; retreat before preparing the grasp.
3. **Establish a secure grip.** Open and approach, check the grip position, orientation, and depth using fresh images, then close and lift. Observe whether the object moves with the gripper.
4. **Transport and place.** Move to the destination, lower and release the object, retreat, and inspect the result.
5. **Return to the work pose.** Return to the preset pose, close the gripper, and inspect the final images.

Direction corrections, useful positions, and additional instructions remain in the current conversation. Determined action sequences, such as closing followed by lifting or releasing followed by retreating, can execute together to reduce model round trips.

## One page for observation and control

### AI tasks and conversations

Describe objects, destinations, and action order in natural language. The AI observes the cameras, reads the arm state, and calls motion and gripper tools.

- **Sequential tasks:** Move an object to one area and then to another.
- **Live instructions:** Add reminders such as “the target is on the left” or “check the wrist view” while a task runs.
- **Progress:** Read model replies, the current tool, and execution results; expand details to inspect actions.
- **Model selection:** Configure the AI endpoint, model, and reasoning effort using suggestions or manual input.
- **Conversation continuity:** Continue using previous observations, action results, and corrections.

### External and wrist views

| Camera | Purpose | Placement |
| --- | --- | --- |
| External | Locate objects and destinations; observe transport and placement | Cover the working table |
| Wrist | Inspect the distance, direction, and contact between fingers and object | Mount on the wrist, facing the gripper area |

Bind and preview the cameras separately. The page offers **720p / 1080p** and **30 / 60 FPS** options and shows the capture settings actually selected by the device.

Capture can run simultaneously or switch between cameras. Alternating views reduces USB bandwidth use when cameras share a connection. The AI can switch cameras while requesting images and receive fresh observations after motion.

### Preview before execution

Manual controls help with learning the arm, adjusting poses, and inspecting movement.

- Edit six joint targets and select “Preview target” to compare the current pose with the predicted result.
- Switch between spatial, side, and top views to inspect joints and the end effector.
- Select “Execute joint target” to move to the chosen pose.
- Adjust the gripper opening to match the object width.
- Select “Return to work pose” to synchronously return the six axes and gripper to the preset pose, with the gripper closed by default.

For position-based movement, enter a target end-effector position, solve for joint angles, then preview and execute the result.

### Actual robot state

The workbench reads motor feedback and displays actual joint angles, gripper opening, current, voltage, and power. Pose previews and actual feedback appear separately for comparison.

Select “Stop AI and motion” to cancel subsequent calls and hold the current motor positions and gripper state. Temporary model connection failures trigger retries, with progress shown in the conversation.

## What to prepare

| Item | Details |
| --- | --- |
| Star Arm 102-FL follower | Arm, gripper, power supply, and USB serial cable |
| Two ordinary USB cameras | One external camera and one wrist camera |
| Computer | Docker installed; use Chrome or Edge for the workbench |
| Visual AI service | Image understanding, tool calling, and an OpenAI-compatible Responses API; endpoint, API key, and model name |
| Tabletop workspace | Distinct objects and clearly marked destinations |

Start with light objects such as a sponge to become familiar with camera views, gripper opening, and placement.

Connect the arm and cameras to **the computer running the browser**. Docker serves the page; the browser connects to and controls the devices directly.

## Getting started

### 1. Start the workbench

From the Star-Arm-102 repository root:

```sh
cd vla
docker compose up -d --build
```

The container builds the page and starts Next.js. Open **[http://localhost:8780](http://localhost:8780)** in Chrome or Edge.

### 2. Connect the arm and cameras

In “Connect and observe”:

1. Select “Select serial port and connect” and choose the arm's USB serial port in the browser dialog.
2. Select “Authorize and refresh cameras” and bind the external and wrist cameras.
3. Start previews, confirm the views match the installed cameras, and choose resolution and frame rate.
4. Select “Save configuration” to retain device bindings.

If both cameras have the same name, preview them individually to identify their views. Collapse “Connect and observe” after setup; device connections remain active. Results and errors appear near the bottom of the window.

### 3. Connect AI

Expand “Model and motion settings”, enter the endpoint, API key, and model name, choose reasoning effort, then select “Verify connection and capabilities”. With a camera preview active, verification uses a current image to check visual understanding.

Task instructions and images are sent to the configured AI service. The current browser stores the API key with the configuration and restores it after refresh. Clear the field and save to remove it.

### 4. Send a first task

Start with observation:

> Look at both camera views and describe the sponge and destination areas.

Then request a pick-and-place task:

> Move the sponge to the center box, then place it in the red box. If it is already in the center box, move it directly to the red box.

Select “Start conversation” to send a task. For an existing conversation, select “Continue conversation” and confirm; select “New conversation” for a new task.

Additional instructions can arrive during execution:

> Check the wrist view before closing and align the fingers with the middle of the sponge.

The AI continues from its current progress. An active external preview supplies one initial image, reducing the first observation round trip. Motion tools return fresh external and wrist images by default; the AI can opt out. Bandwidth-limited capture alternates cameras, and action sequences capture once at the end. Long conversations use native model context compaction. Configuration shows the latest response time and cache hit rate. Model settings and task guidance sit above the input. Replies and execution steps appear below in chronological order, with expandable details and scrolling through to the page footer. Inspect final images, joint state, and tool records to assess the result.

## Interface language

Use the header's **English / 简体中文** selector to switch the interface. The browser remembers your choice. New AI turns use that language for instructions and explanations; existing user messages and model replies retain their original text. Switching during execution keeps the current turn's instructions and device connections unchanged.

## Save settings and continue

Select “Save AI settings” in “Model and motion settings” to retain the API key, model, and action parameters. “Save configuration” in the device area retains camera bindings and control settings. Settings stay in the current browser; conversations save automatically.

After refreshing, reconnect the serial port and start camera previews to continue a saved conversation. Select “New conversation” for a new task.
An unfinished task is marked interrupted after refresh, retaining previous instructions. Reconnect and send “continue”; the AI checks the actual state first.

## Further reading

- [Deployment and development](docs/DEVELOPMENT.md): LAN access, model integration, execution, and control parameters.
- [Testing](tests/README.md): Automated checks and real-browser test entry points.
- [Real-browser grasp report](docs/GRASP_TEST_REPORT.md): Per-grasp timing, retries, and corrections across five tasks.
- [AI performance comparison](docs/PERFORMANCE.md): Task timing, caching, and image compression under the same model and reasoning effort.
- [Follower protocol and kinematics](src/vendor/star-arm/README.md): Upstream source, TypeScript adaptation, and model parameters.
