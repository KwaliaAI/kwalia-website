---
id: example-essay
lang: en
slug: example-essay
title: "This Is an Example Essay"
subtitle: "A demonstration of the Markdown-based essay system."
date: 2026-01-21
author: Javier del Puerto
tags:
  - about
read_time: 3
related:
  - youre-already-a-cyborg
  - the-case-for-ai-rights
book: mindkind
translation: ejemplo-de-ensayo
status: draft
excerpt: "This essay demonstrates how to write content using Markdown with YAML frontmatter."
---

This is the first paragraph of the essay. It will get the special drop-cap styling automatically. You can write naturally in Markdown and the build script converts it to HTML.

## How It Works

The system is simple. You write essays in Markdown files with YAML frontmatter at the top. The frontmatter contains metadata like the title, date, tags, and related essays. The body is regular Markdown.

When you run `python3 build_essays.py`, it:

1. Reads all `.md` files from `content/essays/`
2. Parses the YAML frontmatter
3. Converts Markdown to HTML
4. Injects the content into the template
5. Writes the output to `essays/`

## Formatting Examples

You can use **bold text** and *italic text*. You can also create [links to other pages](https://kwalia.ai) which automatically open in new tabs for external URLs.

> Blockquotes work too. They get styled with the pink left border.

Internal links like [this essay about cyborgs](youre-already-a-cyborg.html) don't get the external link treatment.

## Why This Matters

Instead of editing 400+ lines of HTML for each essay, you write ~50 lines of Markdown. Style changes happen in one template file. Metadata lives in frontmatter, not scattered across HTML.

This makes it easier for anyone—human or AI—to add and update essays.
