// Run with Playwright available on NODE_PATH. Collection requests are intercepted
// so the regression checks never add synthetic clicks to production Analytics.
// KWALIA_TEST_LIVE=1 checks the deployed site instead of local source overlays.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');
const root = path.resolve(__dirname, '..');

(async () => {
    const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
    try {
        const context = await browser.newContext();
        const hits = [], errors = [];
        await context.route(/google-analytics\.com\/.*collect/, async route => {
            const request = route.request();
            const url = new URL(request.url());
            const lines = (request.postData() || '').split('\n');
            for (const line of lines) {
                hits.push(new URLSearchParams(url.search.slice(1) + '&' + line));
            }
            await route.fulfill({ status: 204, body: '' });
        });
        if (!process.env.KWALIA_TEST_LIVE) {
            await context.route('https://kwalia.ai/**', async route => {
                const pathname = new URL(route.request().url()).pathname;
                const file = { '/': 'index.html', '/data/books.json': 'data/books.json', '/data/fiction.json': 'data/fiction.json' }[pathname];
                if (!file) return route.continue();
                await route.fulfill({ status: 200, contentType: file.endsWith('.json') ? 'application/json' : 'text/html', body: fs.readFileSync(path.join(root, file)) });
            });
        }
        const page = await context.newPage();
        page.on('pageerror', error => errors.push(error.message));
        await page.goto('https://kwalia.ai/#udair', { waitUntil: 'domcontentloaded' });
        await page.waitForSelector('#book-modal [href*="amazon"]');
        await page.waitForFunction(() => window.google_tag_manager && window.google_tag_manager['GTM-KQZD8VZG']);
        // Wait for the GA destination to initialize before checking its wire event.
        for (let i = 0; i < 100 && !hits.some(h => h.get('en') === 'page_view'); i++) await page.waitForTimeout(100);
        assert(hits.some(h => h.get('tid') === 'G-N4RP2L7569'), 'Existing Kwalia GA4 destination must initialize');
        const books = await page.evaluate(async () => [...await (await fetch('/data/books.json')).json(), ...await (await fetch('/data/fiction.json')).json()]);
        async function clickAndCheck(selector, book, store, story = null) {
            const before = await page.evaluate(() => window.dataLayer.filter(e => e.event === 'click_buy_now').length);
            await page.locator(selector).evaluate(link => {
                link.addEventListener('click', e => e.preventDefault(), { once: true });
                link.click();
            });
            const events = await page.evaluate(() => window.dataLayer.filter(e => e.event === 'click_buy_now'));
            assert.equal(events.length, before + 1, 'Exactly one event per button click');
            assert.equal(events.at(-1).book_title, book.title.en);
            assert.equal(events.at(-1).store_name, store.name);
            assert.equal(events.at(-1).story_read, story);
            assert.equal(await page.locator(selector).getAttribute('href'), store.url);
        }
        async function waitForPurchases(count) {
            for (let i = 0; i < 150 && hits.filter(h => h.get('en') === 'purchase_intent').length < count; i++) await page.waitForTimeout(100);
            assert.equal(hits.filter(h => h.get('en') === 'purchase_intent').length, count, 'GTM must forward every click exactly once');
        }
        let checked = 0;
        for (const lang of ['en', 'es']) {
            // Use the site's actual card click path and both language versions.
            await page.evaluate(lang => { localStorage.setItem('kwalia-lang', lang); }, lang);
            await page.evaluate(() => history.replaceState(null, '', '/#udair'));
            await page.reload({ waitUntil: 'domcontentloaded' });
            await page.waitForSelector('#book-modal [href*="amazon"]');
            await page.locator('#close-modal').click();
            for (const book of books) {
                if (!(book.stores || []).length) continue;
                await page.locator(`[data-book-id="${book.id}"]`).click();
                for (const [index, store] of book.stores.entries()) {
                    if (store.name === 'Amazon') assert.equal(new URL(store.url).hostname, 'www.amazon.com');
                    await clickAndCheck(`[data-store-index="${index}"]`, book, store);
                    checked++;
                }
                await page.locator('#close-modal').click();
            }
            await waitForPurchases(checked);
        }
        const stories = await page.evaluate(async () => (await fetch('/data/stories.json')).json());
        for (const book of books.filter(b => b.stories)) {
            for (const storyId of book.stories) {
                await page.evaluate(id => window.openReader(id, 'en'), storyId);
                const store = book.stores.find(s => s.name === 'Amazon');
                await clickAndCheck('#reader-buy-link', book, store, stories.find(s => s.id === storyId).title.en);
                checked++;
            }
        }
        await waitForPurchases(checked);
        // A catalogue click after a sample must not inherit that sample's title.
        await page.evaluate(() => history.replaceState(null, '', '/#udair'));
        await page.reload({ waitUntil: 'domcontentloaded' });
        await page.waitForSelector('#book-modal [href*="amazon"]');
        const udair = books.find(b => b.id === 'udair');
        await page.evaluate(() => window.dataLayer.push({ story_read: 'Previous sample' }));
        await clickAndCheck('[data-store-index="0"]', udair, udair.stores[0]);
        for (let i = 0; i < 100 && hits.filter(h => h.get('en') === 'purchase_intent').length < checked + 1; i++) await page.waitForTimeout(100);
        const purchases = hits.filter(h => h.get('en') === 'purchase_intent');
        assert.equal(purchases.length, checked + 1, 'Exactly one GA4 purchase_intent request per click');
        assert(purchases.every(h => h.get('tid') === 'G-N4RP2L7569'));
        assert(purchases.some(h => h.get('ep.book_title') === udair.title.en && h.get('ep.store_name') === 'Amazon'));
        assert(purchases.some(h => h.get('ep.book_title') === 'Your Constitution, Claude'), 'Reader attribution must reach GA4');
        assert.deepEqual(errors, []);
        console.log(JSON.stringify({ mode: process.env.KWALIA_TEST_LIVE ? 'live' : 'local overlay', buttonsChecked: checked + 1, ga4: 'G-N4RP2L7569', event: 'purchase_intent', interceptedPurchaseEvents: purchases.length, errors }, null, 2));
    } finally {
        await browser.close();
    }
})().catch(error => { console.error(error); process.exitCode = 1; });
