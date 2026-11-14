# AI wait time, caching, and native compaction

← [vla-arms-agent](../README.md) · <sub>**English** / [简体中文](PERFORMANCE.zh.md)</sub>

Test date: 2026-11-14. Model gpt-6.1-sol, comparing medium and low separately at the same reasoning effort. Tasks used real local-page forms and start/continue buttons, actual arm feedback, and 1280×720 external images. Static scenes first measured model waits and caching; complete grasps were separate. The first two comparisons used the initial-image implementation at 471be14; later sections cover Astra with default post-motion paired images.

## Six read-only rounds at the same effort

Task: “Read the external camera and current joint state once, then report the sponge position in one sentence. Do not move the arm.” Each group starts a new conversation and continues six times without manually changing the scene or arm. Total time includes initial image preparation, model waits, capture, and the final reply.

| Effort | Six-round total: old→new / s | Mean per round: old→new / s | Model requests: old→new | Cache hit: old→new | Total reduction |
| --- | ---: | ---: | ---: | ---: | ---: |
| medium | 47.9→28.9 | 8.0→4.8 | 12→6 | 62.3%→74.5% | 39.6% |
| low | 45.6→30.7 | 7.6→5.1 | 12→6 | 36.2%→74.6% | 32.8% |

Baseline: 8abb396. The final implementation supplies the active preview's current image and actual pose with the task. Each observation and reply needs one request, avoiding a separate image-request round trip. Model effort and image resolution stay unchanged. Cache hit rate is the weighted ratio of provider-reported cached_tokens to input_tokens.

| Effort | Round | Baseline / s | Final / s |
| --- | ---: | ---: | ---: |
| medium | 1 | 8.6 | 3.6 |
| medium | 2 | 7.4 | 4.2 |
| medium | 3 | 9.8 | 5.6 |
| medium | 4 | 7.1 | 5.4 |
| medium | 5 | 7.2 | 4.4 |
| medium | 6 | 7.8 | 5.9 |
| low | 1 | 6.9 | 5.6 |
| low | 2 | 7.0 | 4.6 |
| low | 3 | 7.0 | 5.4 |
| low | 4 | 8.0 | 4.5 |
| low | 5 | 8.0 | 5.8 |
| low | 6 | 8.6 | 4.8 |

## Complete hardware pick-and-place

Both runs used gpt-6.1-sol / medium and the same task: move the purple sponge from the left red box to the center white dashed box, then return to work. Timing starts at page submission and ends at task completion, including all images, pose previews, motion, release, and return. Read-only speedup ratios are not applied to complete grasps.

| Implementation | Full task / s | All model requests / s | Devices, capture, and page / s | Requests |
| --- | ---: | ---: | ---: | ---: |
| 8abb396 | 178.2 | 154.9 | 23.4 | 19 |
| Final | 240.9 | 217.1 | 23.8 | 24 |

Final physical result: lift and transport images show the sponge between both fingers and the original location empty. The final image shows it entirely inside the center white box. Work-pose feedback confirms the six axes returned; gripper angle was 0.4°.

This complete task did not become faster: regular model requests rose from 19 to 23, and native compaction took another 17.6 seconds. Extra pose-correction turns and compaction overhead offset caching gains.

Each version has only one complete-grasp measurement. Object orientation, model decisions, and corrections vary, so the table establishes neither a stable success rate nor a general speedup. Model-request time includes network, upstream processing, and streaming. The remainder is total minus requests, not pure motor movement.

## Native compaction and cache implementation

- Vercel AI SDK compactionTrigger uses the same /responses endpoint and receives a genuine encrypted openai.compaction item. Checkpoints pass through unchanged; the browser retains full original history rather than a manual summary.
- The current default is 256K (262144 tokens); these comparisons used 32768. Provider-reported input usage triggers compaction after a model call and before the next. Set 0 to disable. Progress is visible and cancellable; additional instructions arrive before the next step.
- A conversation keeps a stable prompt_cache_key and appends within a window. Input starts at the latest native checkpoint. Changing the model or endpoint rebuilds compaction context.
- Settings display the latest response time, input usage, and actual cache hit rate; missing usage is shown as “Not reported”.
- The local CLIProxyAPI routing.session-affinity setting changed from false to true without changing other routing or credentials or restarting the proxy. This belongs to the local model service and is not deployed with application source.

A separate page test used a low threshold to trigger native compaction and correctly recovered native-check-741 afterward. It restored the then-current 32768 setting; the default is now 256K. Unit tests also cover missing checkpoints, additional messages during compaction, model changes, and cache-key continuity.

Compaction reduces input but changes the cache prefix and costs processing time, so a frequent low threshold was not adopted. See [OpenAI native compaction](https://developers.openai.com/api/docs/guides/compaction) and [prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching).

## Alternative settings and ablations

All six-round results below are retained. native uses a fixed key, 16K threshold, and no proxy affinity; affinity only enables affinity; cache-only uses 32K and affinity without the initial-image optimization. Regular-request cache ratios exclude compaction requests, but total time includes compaction.

| Variant / effort | Six-round total / s | Regular-request cache hit | Compactions / time in s |
| --- | ---: | ---: | ---: |
| native-medium | 60.2 | 65.9% | 1 / 14.4 |
| native-low | 70.7 | 73.6% | 1 / 21.0 |
| affinity-medium | 66.9 | 69.6% | 1 / 18.9 |
| cache-only-medium | 50.7 | 80.5% | 0 / 0.0 |

Improved cache-only hit rate did not lower total time, motivating fewer initial-image round trips too. The 16K setting incurred substantial compaction time and was not the default. Sequential measurements cannot isolate routing or cache effects; final differences combine application and local-proxy changes.

## Astra: default paired images after motion

Task: “Put the purple sponge inside the left red dashed box, then return to work.” Started through the real page with gpt-6-astra / medium and 256K compaction. Recording was read-only, without injected movements, reminders, or correction instructions.

| Stage | Duration / s |
| --- | ---: |
| Full pick-and-place including return to work | 189.4 |
| All model requests (17) | 150.7 |
| Alternating activation, paired capture, and encoding (11 pairs) | 19.6 |
| Remaining movement, feedback, and page handling | 19.1 |

Boundaries use actual conversation timestamps, model time uses browser ResourceTiming, and capture uses tool observation_ms. Remaining time is subtraction, not pure motor time.

Physical result: all 22 actual tool images were reviewed for view and integrity. Lift and transport show the sponge held between the fingers and its former location empty. Final placement overlaps the left red box with some edges outside. The arm returned to work; gripper feedback was 0.4°.

- 22 post-motion images: 11 external and 11 wrist, all 1280×720. Decoding, dimensions, non-black checks, and per-image view review passed. WebP90 images were about 67.0–113.5 KiB each.
- Alternating capture averaged 1.8 seconds per pair. Images carry separate capture times and are not synchronized stereo exposures.
- There were 0 standalone observe_camera calls and 5 pose previews. Model waits accounted for about 79.6% of the task.
- Tools attach both views by default and allow observe=false; this run kept images enabled. Sequences capture only at completion, and image failure preserves movement results.

This is one Astra result with a different task direction and model from the sol comparison, so no same-condition speedup or success rate is inferred.

## Final review regression

The final regression used gpt-6-astra / medium and the same red-box task, including updated camera readiness and consolidated instructions. Execution was observed and recorded without intervention.

| Item | Final measurement |
| --- | ---: |
| Full task and return to work | 307.1 s |
| Model-request total / count | 238.7 s / 20 |
| Paired capture, switching, and encoding | 41.1 s |
| Remaining movement, feedback, and page handling | 27.4 s |
| Pose previews / standalone capture | 4 / 0 |
| Actual post-motion images | 30, at 1280×720 |

After an initial empty grasp, the model retreated, adjusted depth, and regrasped autonomously. Images confirm held-object lift, transport, release, and return to work. Final placement overlaps the left red box with edges outside. All 30 tool images passed individual review; globally underexposed external startup frames did not recur, and the object and fingers remained visible in wrist shadows.

This run contains an autonomous retry and does not establish stable speedup or success rate. Instruction changes remain sensitive to model decisions and physical conditions.

Fault injection through the real SDK verified length truncation, filtering, and continuation after stopping during a call. Unexecuted and unconfirmed calls are distinguished; completed actions are not replayed. The real page verified that requesting an unbound wrist camera preserves the external preview. At that revision, 37 unit tests, 5 page tests, a production build, and this hardware regression completed.

## Repeating measurements

[Testing](../tests/README.md) describes benchmark-cache.mjs, profile-task.mjs, and the report generator. Data goes to temp/native-compaction/ and temp/latency-comparison/ and can be collected again. Reports contain no API key, request images, or encrypted checkpoint. Validate lift and final placement images rather than relying only on model descriptions.
