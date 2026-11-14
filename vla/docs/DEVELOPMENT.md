# Deployment and development

← [vla-arms-agent](../README.md) · <sub>**English** / [简体中文](DEVELOPMENT.zh.md)</sub>

## Runtime

vla-arms-agent is an independent Next.js application using React, TypeScript, and Vercel AI SDK. Docker uses Node.js 26 LTS, pnpm 12, and the Next.js standalone build. Node.js serves the generated `server.js`, page, and static assets directly. Direct dependencies are pinned to verified stable versions; the lockfile controls the full dependency tree.

The browser handles camera capture, image extraction, kinematics, Web Serial, and AI tool execution. Model requests go directly to the configured OpenAI-compatible Responses endpoint. Installation, builds, and execution use this directory's source and dependencies.

## Local operation and development

Open `http://localhost:8780` in Chrome or Edge and authorize cameras and the serial port in browser dialogs.

Build and start with Docker:

```sh
docker compose up -d --build
```

The container listens on port `3000`, mapped to host port `8780` by default. Override `BIND_ADDRESS` and `HTTP_PORT` when starting Compose to change the binding or port, for example: `BIND_ADDRESS=0.0.0.0 HTTP_PORT=8781 docker compose up -d --build`.

For local development, run `pnpm install --frozen-lockfile` and `pnpm dev`, then visit `http://localhost:3000`. Changes update in the page automatically.

Browser device authorization works on localhost. Access from another computer requires trusted HTTPS; use the deployment environment's HTTPS configuration.

The model endpoint must allow cross-origin requests (CORS) from the workbench. An HTTPS page needs an HTTPS model endpoint or a browser-supported local endpoint. Devices connect to the computer running the browser.

## Vercel deployment

Source is in [servodevelop/Star-Arm-102, directory vla](https://github.com/servodevelop/Star-Arm-102/tree/main/vla). For Git deployment, set Root Directory to `vla`, use the Next.js preset and Node.js 26, and set production `ENABLE_EXPERIMENTAL_COREPACK` to `1` to select pnpm 12 from `packageManager`.

Vercel serves the HTTPS page. The browser still handles the arm, cameras, and model connection. Allow the site's CORS origin at the model service and enter the AI key in the page. Devices connect to the browser's computer.

Publish a committed local version with `vercel --prod`, or connect the repository above for Git deployment.

## Interface and AI language

English is the default. The header's language selector switches to Simplified Chinese. The browser remembers the choice independently of model and device settings. Switching language updates controls, accessibility labels, application statuses, and notifications without reconnecting devices or starting motion.

A new AI turn snapshots the selected language for its static instructions and tool descriptions. Changing the interface during a running turn keeps that turn's instructions unchanged; the next turn uses the new language. Switching language rebuilds native context and cache scope from the original history. User input and existing assistant replies stay in their original language.

Translations are in `src/lib/messages.ts`; `src/lib/i18n.ts` handles parameters and application-status localization. `src/lib/prompts.ts` contains matching English and Chinese task, tool, and experience sections. Protocol bytes, joint mappings, coordinates, and numeric parameters share one implementation. Documentation uses an English default file and a `.zh.md` Chinese counterpart.

## AI and control flow

AI uses eight tools backed by the same execution methods as manual controls:

| Tool | Purpose |
| --- | --- |
| `get_state` | Read actual joints, TCP, and device state |
| `observe_camera` | Activate or switch a bound camera and return a compressed image |
| `preview_joints` | Preview multiple candidate joint poses |
| `move_joints` | Execute six absolute joint targets |
| `move_tcp` | Solve and execute an absolute TCP position or relative offset |
| `gripper` | Set opening angle and protocol power limit |
| `work_pose` | Return all six axes and close the gripper synchronously |
| `run_sequence` | Execute a determined action sequence in order |

Motion tools attach fresh external and wrist images by default; `observe: false` opts out. Sequences capture once at the end. `observe_exclusive: true` alternates cameras, while `false` retains both. When omitted, existing dual capture is retained; otherwise capture alternates and ends on the external view. Each image includes its role, timestamp, and actual resolution. All-black, empty, or mismatched-source images return errors for the affected camera while valid images remain available. Capture failure preserves completed movement without replaying it.

A newly activated camera waits 500 ms after playback starts before reporting readiness, allowing later frames to replace startup frames; existing streams are reused immediately. Native browser WebP at quality 0.9 preserves actual resolution. Image outputs declare the actual MIME type, including historical JPEG images. Compression changes neither feedback nor commands.

Multiple tools can be called in one model turn. Pose previews can compute while movement waits; serial actions, camera switching, and capture retain call order. A failed sequence step returns completed steps and the current result for the next decision.

Motion tools validate targets and update the preview. Use batched previews to compare candidates and move directly once the target is determined. Model input includes joint angles, TCP, tool axes, and their elevation relative to base XY; complete link geometry remains in the page renderer instead of being repeatedly sent.

System instructions remain static. Task text, initial pose, feedback, and reminders are conversation messages. An already active external preview supplies the task's initial image. Motion tools supply both views after execution; independent observation uses the camera tool. Initial capture does not start or close cameras. An unbound-role request preserves existing previews. Images and actual state are supplied directly to reduce observation round trips.

Each conversation retains `prompt_cache_key` and append-only messages within a native compaction window, including original images, tool results, and encrypted reasoning. The default threshold is 256K (262144) input tokens. After a model call and before the next, Vercel AI SDK `compactionTrigger` uses the same `/responses` endpoint. Native encrypted checkpoints pass through unchanged, and later input starts at the latest checkpoint. The browser keeps full original history rather than a manual summary. Set the threshold to 0 to disable it. Success requires a usable `openai.compaction` item. Compaction progress is visible and cancellable; additional user messages are delivered before the next model request.

Settings show the latest response time, input tokens, and provider-reported cache hit rate. Model or endpoint changes rebuild context from original history. CLIProxyAPI `routing.session-affinity: true` helps reuse upstream credentials within a conversation. This is a model-service setting; cache hits are measured from actual provider usage rather than inferred from a cache key.

Transient network failures retry up to 15 times, 10 seconds apart. Length-limited output retains history and continues. Unexecuted calls and started calls with unconfirmed results receive distinct errors, preventing orphaned calls or action replay. Filtered and failed responses show errors; the conversation remains available for further messages.

Select “Save AI settings” to save the key, model, and motion parameters. Configuration and conversations use browser IndexedDB and restore on refresh. Clear the key field and save to remove a stored key.
On the same origin, old configurations and conversations migrate once into the `vla-arms-agent` database; existing new-name data takes precedence. Different origins retain separate permissions, bindings, and settings.
Live additional messages save with the conversation. Reopening marks unfinished tasks interrupted and retains history and pending messages. After reconnecting, continue by sending a message; the model checks actual state without replaying motion. Stop also cancels model validation or model-list requests.

## Motion and gripper parameters

| Item | Current implementation |
| --- | --- |
| Serial | Default 1 Mbps, servo IDs 0–6, synchronous position commands |
| Actual pose | Motor angles transformed through model mapping and FK |
| TCP | Model `link6` origin; tools use millimeters |
| Position IK | Simplified local damped least-squares iteration from current angles |
| Gripper orientation | Adjusted through joint targets |
| Environment collision detection | Not integrated in this version |
| Gripper control | Opening angle and protocol power limit; 0° closed |
| Gripper power | mW; 0 uses the servo default; this is an output power limit |

Position IK returns iteration count and position error. Preview and adjust the joint configuration before retrying when local solving is difficult.

Reviewed gripping-space references are approximately 71 mm at 30° and 129 mm at 60°. The two samples use different measurement depths and are separate opening references. Mechanical travel ends at 90°; choose the actual opening for the object width.

J4 uses the reference model's +Z axis with a single reverse mapping. The previous project's motor work angle J4=+60° corresponds to model J4=-60° here. The page configures directions and offsets, with one mapping for both conversions.

Joint feedback deviations within 0.5° are normal. Preview and execution share the 0.5° model-range tolerance while original feedback stays unchanged. The AI state and instructions include this rule. Position IK still iterates within URDF limits.

The work pose is `[0,0,-60,-60,0,0]°` in model coordinates. One seven-axis synchronous command returns the arm and closes the gripper; the gripper's power setting affects only its own servo. Stop uses the vendor's hold-current-position command and retains gripper state.

Feedback and motion share one serial queue. Background feedback does not change the page execution state; manual refresh shows progress on its button.

## Development commands

```sh
pnpm install --frozen-lockfile
pnpm dev
pnpm typecheck
pnpm test
pnpm test:e2e
pnpm build
```

See [testing](../tests/README.md) for automated checks, real-browser entry points, and output directories.

## Code sources

Follower communication and kinematics derive from `star-arm-studio` and are adapted here in TypeScript. See the [vendor notes](../src/vendor/star-arm/README.md) for the source commit and scope.

AI orchestration, context, and network recovery reference the original `robot-arm` pure-vision flow at commit `5412efe`.
