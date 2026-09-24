// Requires existing Playwright on NODE_PATH. KWALIA_TEST_LIVE=1 checks production.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const published = JSON.parse(fs.readFileSync(path.join(root, 'data/essays.json'))).filter(e => e.status === 'published');
(async () => {
    const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
    try {
        const context = await browser.newContext();
        await context.route(/google-analytics\.com\/.*collect/, r => r.fulfill({ status: 204, body: '' }));
        if (!process.env.KWALIA_TEST_LIVE) await context.route('https://kwalia.ai/**', async r => {
            let name = new URL(r.request().url()).pathname;
            if (name.endsWith('/')) name += 'index.html';
            const file = path.join(root, name);
            if (fs.existsSync(file) && fs.statSync(file).isFile()) return r.fulfill({ path: file });
            return r.continue();
        });
        const page = await context.newPage();
        const errors = [];
        page.on('pageerror', e => errors.push(e.message));
        for (const width of [1280, 390]) {
            await page.setViewportSize({ width, height: 900 });
            await page.goto('https://kwalia.ai/essays/', { waitUntil: 'domcontentloaded' });
            await page.evaluate(() => localStorage.setItem('kwalia-lang', 'es'));
            await page.reload({ waitUntil: 'domcontentloaded' });
            await page.waitForFunction(() => typeof getVisibleEssays === 'function' && currentLang === 'es' && document.querySelector('#pagination button'));
            for (const lang of ['es', 'en', 'es']) {
                if (width < 768 && !(await page.locator('#lang-es-mobile').isVisible())) await page.locator('#mobile-menu-button').click();
                await page.locator('#lang-' + lang + (width < 768 ? '-mobile' : '')).click();
                const expected = published.filter(e => e.slug[lang]).map(e => e.slug[lang]);
                const actual = await page.evaluate(() => getVisibleEssays().map(card => card.getAttribute('href')));
                assert.deepEqual(actual.sort(), expected.sort());
                assert.equal(await page.evaluate(() => currentPage), 1);
                assert.equal(await page.locator('#essays-list .essay-card:visible').count(), 10);
                // Every pagination page must contain only essays available in this language.
                const pages = Math.ceil(expected.length / 10);
                for (let i = 1; i <= pages; i++) {
                    await page.evaluate(n => showPage(n), i);
                    const hrefs = await page.locator('#essays-list .essay-card:visible').evaluateAll(nodes => nodes.map(n => n.getAttribute('href')));
                    assert(hrefs.every(href => expected.includes(href)));
                }
                console.log('PASS listing/pagination', width, lang, expected.length);
            }
            // Search retains original card indexes when untranslated cards are excluded.
            await page.locator('#essay-search').fill('the permanent underclass');
            assert(await page.locator('.essay-card[data-href-es="que-es-la-subclase-permanente"]').isVisible());
            assert.equal(await page.locator('.essay-card[data-href-es=""]:visible').count(), 0);
            await page.locator('#clear-search').click();
            await page.locator('.filter-pill[data-filter="rights"]').click();
            const filtered = await page.evaluate(() => getVisibleEssays().map(c => c.getAttribute('data-href-es')));
            assert.deepEqual(filtered.sort(), published.filter(e => e.slug.es && e.tags.includes('rights')).map(e => e.slug.es).sort());
            await page.reload({ waitUntil: 'domcontentloaded' });
            await page.waitForFunction(() => typeof getVisibleEssays === 'function' && currentLang === 'es');
            assert.equal(await page.evaluate(() => getVisibleEssays().length), published.filter(e => e.slug.es).length);
            assert.equal(await page.locator('a.sr-only[lang="es"][href=""]').count(), 0);
            for (const lang of ['es', 'en']) {
                await page.evaluate(l => localStorage.setItem('kwalia-lang', l), lang);
                await page.goto('https://kwalia.ai/', { waitUntil: 'domcontentloaded' });
                const expected = published.filter(e => e.slug[lang]).sort((a,b) => new Date(b.date)-new Date(a.date)).slice(0,3).map(e => '/essays/'+e.slug[lang]);
                await page.waitForFunction(want => JSON.stringify([...document.querySelectorAll('#featured-essays > a')].map(a => a.getAttribute('href'))) === JSON.stringify(want), expected);
                console.log('PASS homepage', width, lang);
            }
        }
        assert.deepEqual(errors, []);
        console.log('Essay language checks PASS');
    } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exit(1); });
