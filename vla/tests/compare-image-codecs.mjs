// Same-frame browser codec comparison; no model requests or device commands.
// Source: native canvas codecs and @jsquash/jpeg (MozJPEG / Squoosh).
import { chromium } from "@playwright/test";
import { createServer } from "node:http";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { dirname, resolve, extname, sep } from "node:path";
import { fileURLToPath } from "node:url";

const role = process.argv[2];
if (role && !["external", "wrist"].includes(role)) throw Error("Choose external or wrist");
const live = await chromium.connectOverCDP(process.env.CDP_URL ?? "http://127.0.0.1:9227");
let source;
try {
  const page = live.contexts().flatMap((c) => c.pages()).find((p) => p.url().startsWith(process.env.ARM_URL ?? "http://localhost:8780/"));
  if (!page) throw Error("Open the test browser first");
  source = await page.evaluate((role) => {
    const videos = [...document.querySelectorAll("video")];
    const index = role ? (role === "external" ? 0 : 1) : videos.findIndex((video) => video.srcObject && video.videoWidth && video.readyState >= 2);
    if (index < 0) throw Error("Open a camera preview first");
    const video = videos[index], canvas = document.createElement("canvas");
    if (!video?.srcObject || !video.videoWidth || video.readyState < 2) throw Error("Requested camera is not active");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    return { role: index === 0 ? "external" : "wrist", width: canvas.width, height: canvas.height, captured_at: new Date().toISOString(), dataURL: canvas.toDataURL("image/png") };
  }, role);
} finally { await live.close(); }
const output = resolve("temp/latency-comparison/codecs", source.role);
await mkdir(output, { recursive: true });
const png = Buffer.from(source.dataURL.split(",")[1], "base64");
await writeFile(resolve(output, "source.png"), png);
const codecRoot = dirname(fileURLToPath(import.meta.resolve("@jsquash/jpeg/package.json")));
const server = createServer(async (request, response) => {
  try {
    const path = new URL(request.url, "http://localhost").pathname;
    if (path === "/") {
      response.setHeader("content-type", "text/html");
      response.end('<!doctype html><script type="module">import encode from "/codec/encode.js";window.encodeMozJpeg=encode;</script>');
    } else if (path === "/source.png") {
      response.setHeader("content-type", "image/png"); response.end(png);
    } else {
      if (!path.startsWith("/codec/")) throw Error("Unknown path");
      const file = resolve(codecRoot, path.slice(7));
      if (!file.startsWith(codecRoot + sep)) throw Error("Invalid path");
      response.setHeader("content-type", extname(file) === ".wasm" ? "application/wasm" : "text/javascript");
      response.end(await readFile(file));
    }
  } catch { response.statusCode = 404; response.end(); }
});
await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
let browser;
try {
  browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH, headless: true });
  const page = await browser.newPage();
  await page.goto(`http://127.0.0.1:${server.address().port}`);
  await page.waitForFunction(() => typeof window.encodeMozJpeg === "function");
  const results = await page.evaluate(async () => {
    const image = await createImageBitmap(await (await fetch("/source.png")).blob());
    const canvas = document.createElement("canvas");
    canvas.width = image.width; canvas.height = image.height;
    const context = canvas.getContext("2d", { willReadFrequently: true });
    context.drawImage(image, 0, 0);
    const pixels = context.getImageData(0, 0, image.width, image.height);
    const native = (type, quality) => new Promise((resolve) => canvas.toBlob(resolve, type, quality));
    const codecs = [
      ["jpeg-90", () => native("image/jpeg", .9)],
      ["mozjpeg-90", async () => new Blob([await window.encodeMozJpeg(pixels, { quality: 90 })], { type: "image/jpeg" })],
      ["webp-90", () => native("image/webp", .9)],
      ["png-lossless", () => native("image/png")],
    ];
    const rows = [];
    for (const [name, encode] of codecs) {
      const coldStart = performance.now();
      let blob = await encode();
      const cold_ms = performance.now() - coldStart;
      const times = [];
      for (let i = 0; i < 3; i++) {
        const start = performance.now(); blob = await encode(); times.push(performance.now() - start);
      }
      const restored = await createImageBitmap(blob);
      const check = document.createElement("canvas"); check.width = image.width; check.height = image.height;
      const ctx = check.getContext("2d", { willReadFrequently: true }); ctx.drawImage(restored, 0, 0);
      const decoded = ctx.getImageData(0, 0, image.width, image.height).data;
      let squared = 0;
      for (let p = 0; p < pixels.data.length; p += 4)
        for (let c = 0; c < 3; c++) squared += (decoded[p + c] - pixels.data[p + c]) ** 2;
      const mse = squared / (image.width * image.height * 3);
      const dataURL = await new Promise((resolve) => { const reader = new FileReader(); reader.onload = () => resolve(reader.result); reader.readAsDataURL(blob); });
      rows.push({ name, width: restored.width, height: restored.height, bytes: blob.size, cold_ms, median_ms: times.sort((a, b) => a - b)[1], rmse: Math.sqrt(mse), psnr_db: mse ? 10 * Math.log10(255 ** 2 / mse) : null, dataURL });
      restored.close();
    }
    image.close();
    return rows;
  });
  for (const row of results) {
    const extension = row.name.startsWith("png") ? "png" : row.name.startsWith("webp") ? "webp" : "jpg";
    await writeFile(resolve(output, `${row.name}.${extension}`), Buffer.from(row.dataURL.split(",")[1], "base64"));
  }
  const { dataURL, ...metadata } = source;
  const report = { source: metadata, codecs: results.map(({ dataURL, ...row }) => row) };
  await writeFile(resolve(output, "report.json"), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report));
} finally {
  if (browser) await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
