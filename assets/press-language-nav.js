// Keep the bilingual release's navigation in the same language as its article.
(async () => {
    const lang = document.documentElement.lang === 'es' ? 'es' : 'en';
    const response = await fetch(`/data/i18n/${lang}.json`);
    if (!response.ok) return;
    const labels = await response.json();
    const keys = {
        '#fiction': 'nav.fiction', '#catalogue': 'nav.catalogue',
        '#heteronyms': 'nav.heteronyms', '#press': 'nav.press',
        '#about': 'nav.about', '#contact': 'nav.cta'
    };
    const home = lang === 'es' ? '/es' : '/';
    document.querySelectorAll('#site-header a[href]').forEach(link => {
        const url = new URL(link.href, location.href);
        if (url.origin !== location.origin) return;
        if (url.pathname === '/' && keys[url.hash]) {
            link.href = home + url.hash;
            link.textContent = labels[keys[url.hash]] || link.textContent;
        } else if (url.pathname === '/' && !url.hash) {
            link.href = home;
        } else if (url.pathname === '/essays/') {
            link.textContent = labels['nav.essays'] || link.textContent;
        }
    });
    document.querySelectorAll('article[lang="es"] a[href]').forEach(link => {
        const url = new URL(link.href, location.href);
        if (url.origin === location.origin && url.pathname === '/' && url.hash) {
            url.pathname = '/es';
            link.href = url.href;
        }
    });
})().catch(() => {});
