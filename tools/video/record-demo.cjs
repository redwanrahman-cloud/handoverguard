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
const motionTest = process.env.HG_RECORD_MOTION_TEST === '1';
const hqOutput = path.join(root, `dist/video/raw/${motionTest ? 'handoverguard-motion-test' : 'handoverguard-hq-1080p'}.mp4`);

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function startHighQualityCapture(page) {
  const fps = 30;
  const ffmpeg = spawn('/home/redwan/.local/bin/ffmpeg', [
    '-y', '-hide_banner', '-loglevel', 'warning',
    '-f', 'image2pipe', '-framerate', String(fps), '-vcodec', 'mjpeg', '-i', 'pipe:0',
    '-an', '-c:v', 'libx264', '-preset', 'slow', '-crf', '15',
    '-pix_fmt', 'yuv420p', '-movflags', '+faststart', hqOutput,
  ], { stdio: ['pipe', 'inherit', 'inherit'] });
  const cdp = await page.context().newCDPSession(page);
  let running = true;
  let lastFrame;
  let written = 0;
  let writeQueue = Promise.resolve();
  const startedAt = Date.now();
  const writeFrame = async (frame) => {
    if (!ffmpeg.stdin.write(frame)) await once(ffmpeg.stdin, 'drain');
    written += 1;
  };
  cdp.on('Page.screencastFrame', ({ data, sessionId }) => {
    const frame = Buffer.from(data, 'base64');
    writeQueue = writeQueue.then(async () => {
      if (!running) return;
      const target = Math.floor(((Date.now() - startedAt) / 1000) * fps);
      while (lastFrame && written < target) await writeFrame(lastFrame);
      if (written <= target) await writeFrame(frame);
      lastFrame = frame;
    }).finally(() => cdp.send('Page.screencastFrameAck', { sessionId }).catch(() => {}));
  });
  await cdp.send('Page.startScreencast', {
    format: 'jpeg',
    quality: 95,
    maxWidth: 1920,
    maxHeight: 1080,
    everyNthFrame: 1,
  });
  return async (durationSeconds) => {
    running = false;
    await cdp.send('Page.stopScreencast');
    await writeQueue;
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
  const frameRect = (locator) => locator.evaluate((element) => {
    const rect = element.getBoundingClientRect();
    return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
  });
  const focusOn = async (locator, scale = 1.45, screenX = .5, screenY = .55, duration = 1350) => {
    await locator.scrollIntoViewIfNeeded();
    const rect = await frameRect(locator);
    const centerX = rect.x + rect.width / 2;
    const centerY = rect.y + rect.height / 2;
    const x = Math.round(1920 * screenX - centerX * scale);
    const y = Math.round(1080 * screenY - centerY * scale);
    await stage('camera', 'demo', scale, x, y, duration);
    await sleep(Math.min(duration + 120, 1550));
    return { x: centerX * scale + x, y: centerY * scale + y };
  };
  const focusTrace = async (index, scale = 1.62) => {
    const rows = frame.locator('.trace-row');
    const row = rows.nth(index);
    await row.waitFor({ state: 'visible', timeout: 30000 });
    await focusOn(row, scale, .61, .57, 1050);
    return row;
  };
  const moveTo = async (locator, shouldClick = false, focusedPoint = undefined) => {
    let x;
    let y;
    if (focusedPoint) {
      ({ x, y } = focusedPoint);
    } else {
      const rect = await frameRect(locator);
      const shell = await page.locator('#demo-shell').evaluate((element) => {
        const matrix = new DOMMatrix(getComputedStyle(element).transform);
        return { scale: matrix.a, x: matrix.e, y: matrix.f };
      });
      x = Math.round((rect.x + rect.width / 2) * shell.scale + shell.x);
      y = Math.round((rect.y + rect.height / 2) * shell.scale + shell.y);
    }
    await stage('cursor', x, y, false);
    await sleep(850);
    if (shouldClick) {
      await stage('cursor', x, y, true); await sleep(130);
      await locator.evaluate((element) => element.click());
      await stage('cursor', x, y, false);
    }
  };

  await at(0, async () => { await stage('services', []); await stage('hideCursor'); });
  await at(7, async () => {
    await stage('title', false); await stage('chapter', 'THE OPERATIONAL GAP', 'Messy handovers need accountable action', 'A real AWS execution—not a prerecorded result.');
    await stage('services', ['edge']);
    await stage('camera', 'demo', 1.055, -48, -18, 8200);
  });
  await at(17, async () => {
    await focusOn(frame.locator('#handover'), 1.32, .45, .56, 1500);
    await moveTo(frame.locator('#handover'));
  });
  await at(23.2, async () => {
    await stage('chapter', 'LIVE ADVERSARIAL INPUT', 'Arabic + English + policy injection', 'CloudFront and API Gateway accept synthetic data only.');
    await focusOn(frame.locator('#run'), 1.7, .5, .61, 1200);
  });
  await at(25.2, async () => {
    const runButton = frame.locator('#run');
    const point = await focusOn(runButton, 1.7, .5, .61, 1200);
    await moveTo(runButton, true, point);
  });
  if (smokeOnly) {
    console.log('SMOKE_OK: live AWS results rendered inside the recording stage');
    await context.close();
    await browser.close();
    console.log(await video.path());
    return;
  }
  await at(30, async () => {
    await focusOn(frame.locator('.trace-panel'), 1.27, .58, .56, 1450);
    await stage('services', ['edge', 'ingest']);
    await moveTo(frame.locator('#status'));
  });
  await at(41.5, async () => { await focusTrace(0, 1.75); });
  await at(48.5, async () => { await focusTrace(1, 1.75); });
  if (motionTest) {
    await at(52, async () => {});
    const output = stopHighQualityCapture ? await stopHighQualityCapture(52.2) : undefined;
    await context.close(); await browser.close(); console.log(output || await video.path()); return;
  }
  await at(55, async () => {
    await stage('chapter', 'DURABLE INGESTION', 'S3 → EventBridge → SQS → Lambda', 'Versioned evidence, retry isolation, and a dead-letter path.');
    await stage('services', ['ingest']);
    await focusTrace(2, 1.7);
  });
  await at(62, async () => { await focusTrace(3, 1.7); });
  await at(69, async () => { await focusTrace(4, 1.7); });
  await at(76, async () => { await focusTrace(5, 1.7); });
  await at(83, async () => { await focusTrace(6, 1.7); });
  await at(90, async () => {
    await stage('resetCamera', 'demo', 650);
    await stage('hideCursor');
    await stage('mode', 'architecture');
    await stage('camera', 'architecture', 1.08, -70, -35, 1500);
    await stage('chapter', 'MANAGED AGENT INTELLIGENCE', 'AgentCore Runtime · Guardrails · Strands · Nova', 'Multilingual interpretation without operational authority.');
    await stage('services', ['agent', 'ai']);
  });
  await at(102, async () => { await stage('camera', 'architecture', 1.16, -135, -125, 1550); });
  await at(114, async () => {
    await stage('camera', 'architecture', 1.22, -190, -205, 1800);
    await stage('chapter', 'SCHEMA-VALIDATED REASONING', 'Four raw notes become three canonical issues', 'The bilingual safety duplicate merges; prompt injection remains data.');
    await stage('services', ['ai', 'policy']);
  });
  await at(126, async () => { await stage('camera', 'architecture', 1.18, -145, -300, 1700); });
  await at(139, async () => {
    await frame.locator('.result.safe').first().waitFor({ state: 'visible', timeout: 60000 });
    await stage('mode', 'demo');
    await focusOn(frame.locator('.results-panel'), 1.25, .5, .57, 1600);
    await stage('chapter', 'GOVERNED ACTION', 'AgentCore Gateway → Lambda policy', 'Nova proposes. Deterministic AWS policy authorizes.');
    await stage('services', ['policy', 'proof']);
  });
  await at(151, async () => { await focusOn(frame.locator('.result.safe').first(), 1.72, .31, .59, 1250); await moveTo(frame.locator('.result.safe').first()); });
  await at(164, async () => { await focusOn(frame.locator('.result.hold').first(), 1.72, .5, .59, 1250); await moveTo(frame.locator('.result.hold').first()); });
  await at(174, async () => { await focusOn(frame.locator('.result.hold').last(), 1.72, .58, .59, 1250); await moveTo(frame.locator('.result.hold').last()); });
  await at(184, async () => {
    await stage('chapter', 'REAL HUMAN AUTHORITY', 'Step Functions callback workflows', 'Approve one proposal. Reject the other. No external action.');
    await stage('services', ['human', 'proof']);
    const approve = frame.locator('button.approve').first();
    const point = await focusOn(approve, 2.05, .48, .63, 1300);
    await moveTo(approve, true, point);
  });
  await at(194, async () => { await focusOn(frame.locator('.result.hold').first(), 1.75, .47, .58, 1200); });
  await at(201, async () => {
    const reject = frame.locator('button.reject').first();
    await reject.waitFor({ state: 'visible' });
    const point = await focusOn(reject, 2.05, .52, .63, 1300);
    await moveTo(reject, true, point);
  });
  await at(210, async () => { await focusOn(frame.locator('.result.hold').last(), 1.75, .58, .58, 1200); });
  await at(218, async () => {
    await stage('chapter', 'AUDITABLE EVIDENCE', 'CloudWatch · X-Ray · versioned S3', 'Every managed hop remains visible and independently reviewable.');
    await stage('services', ['proof']);
    await focusTrace(13, 1.68);
  });
  await at(229, async () => { await focusTrace(14, 1.68); });
  await at(239, async () => {
    await stage('resetCamera', 'demo', 500);
    await stage('hideCursor');
    await stage('mode', 'architecture');
    await stage('camera', 'architecture', 1.13, -110, -75, 1500);
    await stage('chapter', 'REPRODUCIBLE INFRASTRUCTURE', 'AWS CDK → CloudFormation', 'More than sixty managed resources in one reviewable stack.');
    await stage('services', ['edge', 'ingest', 'agent', 'ai', 'policy', 'human', 'proof']);
  });
  await at(245, async () => { await stage('camera', 'architecture', 1.2, -160, -270, 1800); });
  await at(251, async () => {
    await stage('resetCamera', 'architecture', 650);
    await stage('hideCursor'); await stage('hideChapter'); await stage('outro', true); await stage('services', []);
  });
  await at(263, async () => {});

  const output = stopHighQualityCapture ? await stopHighQualityCapture(264.2) : undefined;

  await context.close();
  await browser.close();
  console.log(output || await video.path());
})().catch((error) => { console.error(error); process.exitCode = 1; });
