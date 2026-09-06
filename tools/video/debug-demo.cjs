const path = require('node:path');
const { chromium } = require('/home/redwan/.openclaw/runtime-2026.9.2/node_modules/playwright-core');

const root = path.resolve(__dirname, '../..');
const browserLibraries = path.join(root, 'dist/video/browser-libs/usr/lib/x86_64-linux-gnu');

(async () => {
  const browser = await chromium.launch({
    executablePath: '/home/redwan/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome',
    headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
    env: { ...process.env, LD_LIBRARY_PATH: `${browserLibraries}:${process.env.LD_LIBRARY_PATH || ''}` },
  });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('console', (message) => console.log('CONSOLE', message.type(), message.text()));
  page.on('pageerror', (error) => console.log('PAGEERROR', error.message));
  page.on('response', (response) => {
    if (response.url().includes('execute-api')) console.log('API', response.status(), response.request().method(), response.url());
  });
  await page.goto('https://d1234urv6397y8.cloudfront.net', { waitUntil: 'networkidle' });
  await page.locator('#run').click();
  for (let index = 0; index < 20; index += 1) {
    await page.waitForTimeout(2000);
    console.log(await page.evaluate(() => ({
      status: document.querySelector('#status')?.textContent,
      error: document.querySelector('#error')?.textContent,
      runId: document.querySelector('#run-id')?.textContent,
      items: document.querySelector('#items')?.innerText.slice(0, 500),
      trace: document.querySelector('#trace')?.innerText.slice(-500),
    })));
  }
  await browser.close();
})().catch((error) => { console.error(error); process.exitCode = 1; });
