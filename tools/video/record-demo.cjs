const path = require('node:path');
const { once } = require('node:events');
const { spawn } = require('node:child_process');
const { chromium } = require('/home/redwan/.openclaw/runtime-2026.9.2/node_modules/playwright-core');

const root = path.resolve(__dirname, '../..');
const videoDir = path.join(root, 'dist/video/raw');
const stageUrl = `file://${path.join(__dirname, 'stage.html')}`;
const chromiumPath = '/home/redwan/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome';
const browserLibraries = path.join(root, 'dist/video/browser-libs/usr/lib/x86_64-linux-gnu');
const smokeOnly = process.env.HG_RECORD_SMOKE === '1';
const highQuality = process.env.HG_RECORD_HQ === '1';
const hqOutput = path.join(root, 'dist/video/raw/handoverguard-hq-1080p.mp4');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function startHighQualityCapture(page) {
  const fps = 15;
  const ffmpeg = spawn('/home/redwan/.local/bin/ffmpeg', [
    '-y', '-hide_banner', '-loglevel', 'warning',
    '-f', 'image2pipe', '-framerate', String(fps), '-vcodec', 'mjpeg', '-i', 'pipe:0',
    '-an', '-c:v', 'libx264', '-preset', 'slow', '-crf', '15',
    '-pix_fmt', 'yuv420p', '-movflags', '+faststart', hqOutput,
  ], { stdio: ['pipe', 'inherit', 'inherit'] });
  let running = true;
  let lastFrame;
  let written = 0;
  const startedAt = Date.now();
  const writeFrame = async (frame) => {
    if (!ffmpeg.stdin.write(frame)) await once(ffmpeg.stdin, 'drain');
    written += 1;
  };
  const loop = (async () => {
    while (running) {
      const frame = await page.screenshot({ type: 'jpeg', quality: 95 });
      const target = Math.floor(((Date.now() - startedAt) / 1000) * fps);
      while (lastFrame && written < target) await writeFrame(lastFrame);
      await writeFrame(frame);
      lastFrame = frame;
    }
  })();
  return async (durationSeconds) => {
    running = false;
    await loop;
    const targetFrames = Math.ceil(durationSeconds * fps);
    while (lastFrame && written < targetFrames) await writeFrame(lastFrame);
    ffmpeg.stdin.end();
    const [code] = await once(ffmpeg, 'close');
    if (code !== 0) throw new Error(`High-quality ffmpeg capture exited ${code}`);
    return hqOutput;
  };
}

(async () => {
  const browser = await chromium.launch({
    executablePath: chromiumPath,
    headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--autoplay-policy=no-user-gesture-required'],
    env: {
      ...process.env,
      LD_LIBRARY_PATH: `${browserLibraries}:${process.env.LD_LIBRARY_PATH || ''}`,
    },
  });
  const contextOptions = {
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 1,
  };
  if (!highQuality) contextOptions.recordVideo = { dir: videoDir, size: { width: 1920, height: 1080 } };
  const context = await browser.newContext(contextOptions);
  const page = await context.newPage();
  const video = highQuality ? undefined : page.video();
  await page.goto(stageUrl, { waitUntil: 'load' });
  const frame = page.frames().find((candidate) => candidate.url().includes('cloudfront.net'));
  if (!frame) throw new Error('Public demo iframe did not load');
  await frame.locator('#run').waitFor({ state: 'visible' });

  const stopHighQualityCapture = highQuality ? await startHighQualityCapture(page) : undefined;
  const start = Date.now();
  const at = async (seconds, action) => {
    const remaining = start + seconds * 1000 - Date.now();
    if (remaining > 0) await sleep(remaining);
    await action();
  };
  const stage = (method, ...args) => page.evaluate(([name, values]) => window.production[name](...values), [method, args]);
  const moveTo = async (locator, shouldClick = false) => {
    const box = await locator.boundingBox();
    if (!box) throw new Error('Target has no bounding box');
    const x = Math.round(box.x + box.width / 2);
    const y = Math.round(box.y + box.height / 2);
    await stage('cursor', x, y, false);
    await page.mouse.move(x, y, { steps: 28 });
    await sleep(750);
    if (shouldClick) {
      await stage('cursor', x, y, true); await sleep(130);
      await locator.evaluate((element) => element.click());
      await stage('cursor', x, y, false);
    }
  };

  await at(0, async () => { await stage('services', []); });
  await at(7, async () => {
    await stage('title', false); await stage('chapter', 'THE OPERATIONAL GAP', 'Messy handovers need accountable action', 'A real AWS execution—not a prerecorded result.');
    await stage('services', ['edge']);
  });
  await at(17, async () => {
    await frame.locator('#handover').scrollIntoViewIfNeeded(); await stage('focus', 'input');
    await moveTo(frame.locator('#handover'));
  });
  await at(24.5, async () => {
    await stage('chapter', 'LIVE ADVERSARIAL INPUT', 'Arabic + English + policy injection', 'CloudFront and API Gateway accept synthetic data only.');
    await moveTo(frame.locator('#run'), true);
    await frame.locator('.result.safe').first().waitFor({ state: 'visible', timeout: 60000 });
  });
  if (smokeOnly) {
    console.log('SMOKE_OK: live AWS results rendered inside the recording stage');
    await context.close();
    await browser.close();
    console.log(await video.path());
    return;
  }
  await at(29, async () => {
    await frame.locator('.trace-panel').scrollIntoViewIfNeeded(); await stage('focus', 'trace');
    await stage('services', ['edge', 'ingest']);
  });
  await at(55, async () => {
    await stage('chapter', 'DURABLE INGESTION', 'S3 → EventBridge → SQS → Lambda', 'Versioned evidence, retry isolation, and a dead-letter path.');
    await stage('services', ['ingest']);
    await frame.locator('#trace').evaluate((node) => node.scrollTo({ top: 0, behavior: 'smooth' }));
  });
  await at(73, async () => {
    await frame.locator('#trace').evaluate((node) => node.scrollTo({ top: node.scrollHeight * .38, behavior: 'smooth' }));
  });
  await at(90, async () => {
    await stage('mode', 'architecture');
    await stage('chapter', 'MANAGED AGENT INTELLIGENCE', 'AgentCore Runtime · Guardrails · Strands · Nova', 'Multilingual interpretation without operational authority.');
    await stage('services', ['agent', 'ai']);
  });
  await at(114, async () => {
    await stage('chapter', 'SCHEMA-VALIDATED REASONING', 'Four raw notes become three canonical issues', 'The bilingual safety duplicate merges; prompt injection remains data.');
    await stage('services', ['ai', 'policy']);
  });
  await at(139, async () => {
    await stage('mode', 'demo'); await stage('focus', 'results');
    await frame.locator('.results-panel').scrollIntoViewIfNeeded();
    await stage('chapter', 'GOVERNED ACTION', 'AgentCore Gateway → Lambda policy', 'Nova proposes. Deterministic AWS policy authorizes.');
    await stage('services', ['policy', 'proof']);
  });
  await at(151, async () => { await moveTo(frame.locator('.result.safe').first()); });
  await at(165, async () => { await moveTo(frame.locator('.result.hold').first()); });
  await at(184, async () => {
    await stage('chapter', 'REAL HUMAN AUTHORITY', 'Step Functions callback workflows', 'Approve one proposal. Reject the other. No external action.');
    await stage('services', ['human', 'proof']);
    await moveTo(frame.locator('button.approve').first(), true);
  });
  await at(201, async () => {
    await frame.locator('button.reject').first().waitFor({ state: 'visible' });
    await moveTo(frame.locator('button.reject').first(), true);
  });
  await at(218, async () => {
    await frame.locator('.trace-panel').scrollIntoViewIfNeeded(); await stage('focus', 'trace');
    await stage('chapter', 'AUDITABLE EVIDENCE', 'CloudWatch · X-Ray · versioned S3', 'Every managed hop remains visible and independently reviewable.');
    await stage('services', ['proof']);
    await frame.locator('#trace').evaluate((node) => node.scrollTo({ top: node.scrollHeight, behavior: 'smooth' }));
  });
  await at(239, async () => {
    await stage('mode', 'architecture');
    await stage('chapter', 'REPRODUCIBLE INFRASTRUCTURE', 'AWS CDK → CloudFormation', 'More than sixty managed resources in one reviewable stack.');
    await stage('services', ['edge', 'ingest', 'agent', 'ai', 'policy', 'human', 'proof']);
  });
  await at(251, async () => {
    await stage('hideChapter'); await stage('outro', true); await stage('services', []);
  });
  await at(263, async () => {});

  const output = stopHighQualityCapture ? await stopHighQualityCapture(264.2) : undefined;

  await context.close();
  await browser.close();
  console.log(output || await video.path());
})().catch((error) => { console.error(error); process.exitCode = 1; });
