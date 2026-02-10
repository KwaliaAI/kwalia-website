# Kwalia Website Style Guide

**Website:** https://kwalia.ai
**Repository:** https://github.com/KwaliaAI/kwalia-website
**Last updated:** 2026-02-10

---

## Typography

### Font Families

| Class | Font | Usage |
|-------|------|-------|
| `.font-f1` | Instrument Serif | Headings (h1, h2, h3, h4), display text |
| `.font-f2` | Plus Jakarta Sans | Body text, navigation, UI elements |
| `.font-f3` | JetBrains Mono | Code, monospace text |

### Font Files

Local fonts are stored in `/fonts/`:
```
fonts/
├── Instrument_Serif/
│   ├── InstrumentSerif-Regular.ttf
│   ├── InstrumentSerif-Italic.ttf
│   └── OFL.txt (license)
└── Plus_Jakarta_Sans/
    ├── PlusJakartaSans-VariableFont_wght.ttf
    ├── PlusJakartaSans-Italic-VariableFont_wght.ttf
    ├── static/ (individual weight files)
    ├── OFL.txt (license)
    └── README.txt
```

Currently loading from Google Fonts CDN:
```html
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Plus+Jakarta+Sans:wght@400;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
```

---

## Color Palette

| Class | Hex | Usage |
|-------|-----|-------|
| `.bg-c1` | `#FFFF00` (Yellow) | Accent highlights, nav hover underline |
| `.text-c2` / `.bg-c2` | `#474747` (Dark Gray) | Primary text, buttons |
| `.bg-c3` / `.text-c3` / `.border-c3` | `#FF70A6` (Pink) | Secondary accent, button hover states |
| `.bg-c4` / `.text-c4` | `#FFFFFF` (White) | Background, inverse text |

### Color Usage
- **Background:** White (`#FFFFFF`)
- **Text:** Dark gray (`#474747`)
- **Primary accent:** Yellow (`#FFFF00`) — used for highlights and hover effects
- **Secondary accent:** Pink (`#FF70A6`) — used for links, buttons, CTAs

---

## Logo & Assets

All assets are in `/assets/`:

| File | Description |
|------|-------------|
| `logo-kwalia-small.png` | Main logo (header, og:image) |
| `kwalia-icon.png` | Favicon |

### Book Covers
Named by ISBN: `9781917717XXX.jpg`

---

## CSS Framework

Using **Tailwind CSS** via CDN:
```html
<script src="https://cdn.tailwindcss.com"></script>
```

Custom styles are defined in `<style>` blocks within HTML files.

---

## Key Styles

### Navigation
```css
.nav-link-highlight::after {
    background-color: #ffff00;
    /* Yellow underline on hover */
}
```

### Section Padding
```css
.section-padding { padding: 4rem 1.5rem; }
@media (min-width: 768px) { padding: 6rem 1.5rem; }
```

### Scroll Behavior
```css
html {
    scroll-behavior: smooth;
    scroll-padding-top: 80px; /* Account for sticky header */
}
```

---

## Internationalization

The site supports **English (EN)** and **Spanish (ES)** via language toggle buttons. Text content uses `data-key` attributes for translation lookup.

---

## Directory Structure

```
kwalia-website/
├── index.html          # Main landing page
├── assets/             # Images, logos, book covers, PDFs
├── fonts/              # Local font files
├── templates/          # HTML templates (essay-en.html, essay-es.html)
├── essays/             # Essay pages
├── stories/            # Fiction pages
├── press/              # Press releases
├── content/            # Content files
├── data/               # Data files
└── *.py                # Build scripts
```

---

## Google Drive Backup

Fonts are also stored on Google Drive:
```
G:/Shared drives/Compartido/ClaudeCode/kwalia-books/_assets/fonts/
```
