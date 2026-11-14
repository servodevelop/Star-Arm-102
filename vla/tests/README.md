# Testing

← [vla-arms-agent](../README.md) · <sub>**English** / [简体中文](README.zh.md)</sub>

- `core.test.ts`: Fixed forward-kinematics results and protocol packets from the vendor workbench; virtual serial tests cover fragmentation, background feedback readiness, execution state, queues, cancellation, connection failures, and reconnection. No hardware motion.
- `context.test.ts`: Native encrypted-checkpoint continuation, full-history retention, and preservation of context when a checkpoint is invalid.
- `agent.test.ts`: Initialization failures, stopping, unfinished-conversation recovery, retained instructions, and real SDK request prefixes, session cache keys, native compaction, length-limit continuation, failures, and interrupted-action recovery. Preserves actual execution state and history without network or hardware access.
- `cameras.test.ts`: Closing during startup, playback failures, state and device release, alternating and dual capture, all-black frames, wrong sources, unbound roles preserving existing previews, startup waits, and readiness after disconnects during startup.
- `network.test.ts`: Virtual-clock checks for 15 retries, 10-second spacing, cancellation, and avoiding repeated tool execution after stream interruption.
- `tools.test.ts`: Batched previews, concurrent preview and device ordering, default paired post-motion images, image opt-out, and image failures without repeated motion. Checks that IK failure stops a sequence before later gripper closure and that completed steps return to the model.
- `page.spec.ts`: Playwright checks for editing and saving all AI settings, restoration after refresh, key removal, target previews, unfinished-conversation recovery, cancelling model verification, chronological conversation order, scrolling, and responsive expanded layouts. Run `pnpm test:e2e`; the default target is local port 8780.
- `live-control.mjs`: Real-browser acceptance through normal forms and buttons. Requires real cameras, an arm, and a visual/tool-capable Responses API. Executes real motion. Accepts JSON-line commands on stdin; page and state output goes to `temp/live/`, and browser data to `temp/live-profile/`. Both directories can be recreated after deletion.
- `task-report.mjs`: After sending a task in the page, run `node tests/task-report.mjs 1`, where the argument is the round number. Read-only recording of elapsed time, tool results, model request timing, and images to `temp/five-rounds/round-1/`. Review images and feedback for physical success. After review, fill placement confirmation times, individual durations, return-to-work time, `physical_success`, and `grasp_retries` in `report.json`; run `node tests/task-report.mjs summary` for a final report. The script checks segmented times sum to total time. Source: this project's real-browser repeated acceptance.
- `profile-task.mjs`: Run `node tests/profile-task.mjs astra-batched-center-1` before sending a task normally in the same page. Read-only recording of the next task's requests, first byte, tool argument readiness, response end, token usage, actual tools, and images to `temp/latency-comparison/<name>/`. Sends no model or device commands and retains no API key or complete request body. After completion it saves actual submitted images and checks decoding, dimensions, and all-black frames. Review the images before filling `physical_success`. Source: this project's real-browser performance comparisons.
- `compare-image-codecs.mjs`: With preview active, run `CHROMIUM_PATH=/path/to/chrome node tests/compare-image-codecs.mjs external`, or use `wrist`. Reads one preview frame and uses a separate browser to compare native JPEG90, MozJPEG90, WebP90, and lossless PNG at original resolution. Records size, encoding time, and pixel error to `temp/latency-comparison/codecs/<role>/`. No model requests or arm commands. Source: real camera measurements; compression library `@jsquash/jpeg` (MozJPEG / Squoosh).
- `summarize-latency.mjs`: Collect the six `baseline-{medium,low}` and `final-{medium,low}` benchmark rounds, `native-ui` compaction validation, complete `sol-final-medium-center-1` and `native-grasp-center-1` tasks, and Astra paired-image runs `astra-dual-observation-red-1` and `final-review-astra-red-1`. Review images and fill `physical_success` and `review`, then run `node tests/summarize-latency.mjs` to generate `docs/PERFORMANCE.md`. Checks model, effort, task text, client version, cache keys, and native checkpoints; times read-only observations separately from grasps and retains slower trials. Raw `temp/` data must be collected again after cleanup. Source: real-browser cache and grasp comparisons.
- `select-serial.py`: X11 hardware browser helper selecting the sole USB serial device using the keyboard, without direct serial I/O. First confirm the browser dialog has finished enumerating exactly one USB serial device, listed last. The script does not detect dialog readiness; manual selection is the default.

```sh
CHROMIUM_PATH=/path/to/chrome HEADED=1 node tests/live-control.mjs
```

Enter `{"action":"connect"}` and select the follower serial port in the browser. `configure` uses command parameters or the page's current endpoint/model. An existing parent project `.env` can supply authorized configuration. Keys can come from `AI_API_KEY`, a CLIProxyAPI configuration selected by `AI_CONFIG_FILE`, or an existing `.env`; they populate the real page and remain out of logs. Standalone operation does not require a parent project.

Common commands:

```json
{"action":"configure","baseURL":"http://127.0.0.1:8317/v1","model":"gpt-6-astra","effort":"medium"}
{"action":"cameras","resolution":"1280x720","indices":[1,2],"only":0}
{"action":"task","text":"把海绵移动到中心框并放置到红色框，如果已经在中心框则只需要放到红色框。"}
{"action":"status"}
{"action":"close"}
```

`indices` refers to the page's device-list indices: verify device names first. Both bindings are saved; `only` selects external (0) or wrist (1), and omitting it starts both separately. The page or AI can switch capture for bandwidth limits. `task` uses the start/append buttons and confirms the append dialog for an existing conversation. The AI flow appears chronologically below the input, and capture preserves that order. `temp/live/network.json` records request timing, status, and system-prompt hashes. The test browser stores the configured key; camera tools submit images. Validate completion using final images, motor feedback, and physical placement together.

Source: vendor comparison commit and adaptation scope are described in the [vendor notes](../src/vendor/star-arm/README.md). Page tests, hardware operation wrappers, and the X11 dialog helper were written for this project.

- `benchmark-cache.mjs`: Six read-only observations of the same text through the connected test page. Run `node tests/benchmark-cache.mjs <name> medium 262144`, with low-effort comparisons separate. Uses ordinary forms, saving, start/append, and confirmation buttons without injecting state; permits only read-only tool results. Records elapsed time, all requests, native compaction time, client fingerprints, cache-key hashes, and actual token usage to `temp/native-compaction/<name>/`. Saves no keys, raw request bodies, or encrypted checkpoints. Source: real-browser cache and speed comparisons.
