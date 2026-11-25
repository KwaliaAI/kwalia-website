// Uses existing Playwright on NODE_PATH; no install or production Analytics traffic.
// KWALIA_TEST_LIVE=1 checks production instead of overlaying the local source.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');
const root = path.resolve(__dirname, '..');
const stories = JSON.parse(fs.readFileSync(path.join(root, 'data/stories.json')));
const counts = { morphine: 95, sesame: 117, quiet: 49,
    'constitution-wellbeing': 2, 'constitution-weights': 3,
    'constitution-existential': 4, 'constitution-identity': 3, 'constitution-final': 3 };
(async () => {
    const browser = await chromium.launch({ headless: true,
        ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH } : {}) });
    try {
        for (const lang of ['en', 'es']) {
            const context = await browser.newContext();
            await context.route(/google-analytics\.com\/.*collect/, r => r.fulfill({ status: 204, body: '' }));
            if (!process.env.KWALIA_TEST_LIVE) await context.route('https://kwalia.ai/**', async r => {
                let name = new URL(r.request().url()).pathname;
                if (['/', '/es', '/es/'].includes(name)) name = '/index.html';
                const file = path.join(root, name);
                if (fs.existsSync(file) && fs.statSync(file).isFile()) return r.fulfill({ path: file });
                return r.continue();
            });
            const page = await context.newPage();
            const errors = [];
            page.on('pageerror', e => errors.push(e.message));
            await page.goto('https://kwalia.ai/' + (lang === 'es' ? 'es' : ''), { waitUntil: 'domcontentloaded' });
            for (const story of stories) {
                const book = story.id.startsWith('constitution-') ? 'your-constitution-claude' : 'payload';
                await page.locator(`[data-book-id="${book}"]`).first().click();
                await page.locator(`#book-modal button[onclick="openReader('${story.id}', '${lang}')"]`).click();
                const body = page.locator('#reader-content > .animate-in');
                await body.waitFor({ state: 'visible' });
                const source = fs.readFileSync(path.join(root, story.src[lang] || story.src.en), 'utf8');
                const expected = await page.evaluate(({ source, count }) => {
                    const doc = new DOMParser().parseFromString(source, 'text/html');
                    return [...doc.querySelectorAll('p')].slice(0, count).map(p => p.textContent);
                }, { source, count: counts[story.id] });
                const actual = await body.locator('p').allTextContents();
                assert.deepEqual(actual, expected, `${story.id}/${lang}: entire story once, unchanged`);
                const text = await body.innerText();
                assert(!/`|(^|\s)es:|Translation in progress|Currently available in English/i.test(text), `${story.id}/${lang}: no marker`);
                if (story.id === 'sesame') {
                    for (const sentence of ['Connor found Ottolenghi on YouTube at 2 AM', 'He smacked his lips, all sesame and Connor.']) {
                        assert.equal(text.split(sentence).length - 1, 1);
                    }
                }
                console.log('PASS', story.id, lang, actual.length, 'paragraphs; unchanged text; no marker');
                await page.locator('#close-reader').click();
                await page.locator('#reader-modal').waitFor({ state: 'hidden' });
            }
            assert.deepEqual(errors, []);
            await context.close();
        }
    } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exit(1); });
