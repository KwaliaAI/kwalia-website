---
id: example-essay
lang: es
slug: ejemplo-de-ensayo
title: "Este es un ensayo de ejemplo"
subtitle: "Una demostración del sistema de ensayos basado en Markdown."
date: 2026-01-21
author: Javier del Puerto
tags:
  - about
read_time: 3
related:
  - ya-eres-un-cyborg
  - el-caso-de-los-derechos-de-la-ia
book: mindkind
translation: example-essay
status: draft
excerpt: "Este ensayo demuestra cómo escribir contenido usando Markdown con frontmatter YAML."
---

Este es el primer párrafo del ensayo. Recibirá automáticamente el estilo especial de letra capital. Puedes escribir naturalmente en Markdown y el script de construcción lo convierte a HTML.

## Cómo funciona

El sistema es simple. Escribes ensayos en archivos Markdown con frontmatter YAML en la parte superior. El frontmatter contiene metadatos como el título, fecha, etiquetas y ensayos relacionados. El cuerpo es Markdown regular.

Cuando ejecutas `python3 build_essays.py`:

1. Lee todos los archivos `.md` de `content/essays/`
2. Analiza el frontmatter YAML
3. Convierte Markdown a HTML
4. Inyecta el contenido en la plantilla
5. Escribe la salida en `essays/`

## Ejemplos de formato

Puedes usar **texto en negrita** y *texto en cursiva*. También puedes crear [enlaces a otras páginas](https://kwalia.ai) que automáticamente se abren en pestañas nuevas para URLs externas.

> Las citas también funcionan. Se estilizan con el borde rosa a la izquierda.

Los enlaces internos como [este ensayo sobre cyborgs](ya-eres-un-cyborg.html) no reciben el tratamiento de enlace externo.

## Por qué importa

En lugar de editar más de 400 líneas de HTML para cada ensayo, escribes ~50 líneas de Markdown. Los cambios de estilo ocurren en un solo archivo de plantilla. Los metadatos viven en el frontmatter, no dispersos por el HTML.

Esto facilita que cualquiera—humano o IA—añada y actualice ensayos.
