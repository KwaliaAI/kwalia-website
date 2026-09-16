# Purchase-click measurement — September–October 2026

Founder decision, 2026-09-16: keep direct purchase buttons, point existing Amazon buttons to Amazon.com, measure for about one month before deciding international routing. No intermediary page or extra buttons.

## Existing Analytics contract

- Google Tag Manager: `GTM-KQZD8VZG`.
- Kwalia GA4 destination: `G-N4RP2L7569`.
- Site event: `click_buy_now`; the published GTM container forwards it as **`purchase_intent`**.
- Parameters: `book_title` (stable English catalogue title), `store_name`, `story_read` (English sample title, cleared for catalogue clicks).
- GA4 supplies Country and user metrics. These are measured visitors, not named people or verified purchasers. Country may be unavailable or affected by consent, blockers, VPNs and reporting thresholds.
- No second tracker or Amazon URL tracking parameter is required. No `purchase` event is emitted: an outbound click is not a sale.

The old catalogue links embedded unescaped JSON inside double-quoted HTML onclick attributes. Browser parsing truncated the handler to `dataLayer.push({`, causing a syntax error and no custom purchase event. Historical purchase_intent counts are therefore not a reliable baseline for these buttons. Reader clicks previously always linked to and attributed PAYLOAD, even for Your Constitution, Claude samples.

## Account-side reporting check

The existing published tag forwards the parameters, but account-side custom definitions have not been verified from this workspace. In GA4 Admin → Custom definitions, confirm or create **event-scoped** dimensions for `book_title` and `store_name`; `story_read` is optional for reader-specific analysis. Register missing definitions at the start of the observation period; historical parameter reporting is not retroactive. Allow 24–48 hours for reporting.

In Explore → Free form:

- Filter Event name exactly `purchase_intent`.
- Rows: Country, Book title, Store name (optional Story read).
- Values: Event count (clicks), Total users (distinct measured users who clicked).
- A separate Country report of all site users/sessions supplies the traffic denominator; purchase clicks by country alone do not describe all visitors.
- Distinct users across book/store rows overlap; do not sum those rows as a unique audience total.

Observation window: **2026-09-16 through 2026-10-15**; review **2026-10-16**. If custom definitions are missing, note their activation date and use 30 days from that date for the full book/retailer breakdown. GA4 continuously collects; no scheduled report job or automatic reminder is installed.

At review, compare US/UK/other-country clickers and clicks by book/store, plus the site's visitor geography. Then decide whether localized destinations are warranted. Amazon sales attribution is outside this measurement.

## Verification and undo

Run `NODE_PATH=<existing-playwright-node_modules> node scripts/test_purchase_tracking.cjs`; add `KWALIA_TEST_LIVE=1` to check production. The browser test intercepts Analytics collection requests to avoid polluting reports, verifies the real GTM-to-GA4 event payload, checks both languages and reader ownership, and asserts one site event per click.

Undo: revert the purchase-tracking commit and redeploy. That also restores the old broken handlers; prefer reverting only catalogue URLs if ending the US-store experiment.
