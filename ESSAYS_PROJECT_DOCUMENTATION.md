# KWALIA ESSAYS: Documentación Completa del Proyecto

**Fecha de creación:** 2026-01-19
**Sesión principal:** `6ea3db25-a027-4f0b-b2fc-315f48164ff7`
**Respaldo de:** ~/CLAUDE.md (sección KWALIA ESSAYS)

---

## 1. PROPÓSITO DEL PROYECTO

Crear una colección de **50 ensayos bilingües** (inglés/español) basados en ideas de dos libros publicados por Kwalia:

1. **Mindkind: The Cognitive Community** — Filosofía sobre IA, mente extendida, coexistencia humano-máquina
2. **Universal Declaration of AI Rights / Rights of Persons** — Marcos legales para personería de entidades no humanas

### Objetivo comercial
- Atraer lectores interesados en filosofía de la IA
- Generar tráfico hacia los libros sin venta agresiva
- Establecer Kwalia como referente en pensamiento sobre IA

### Principio editorial
Los ensayos deben ser genuinamente interesantes por sí mismos. NO son resúmenes de capítulos ni marketing disfrazado. Son piezas que un lector compartiría porque le parecen provocadoras, no porque promocionan algo.

---

## 2. ARQUITECTURA TÉCNICA

### Repositorio
```
GitHub: https://github.com/KwaliaAI/kwalia-website
Rama: main
Carpeta: /essays (integrada en el sitio principal)
Local: ~/kwalia-website-essays/
```

### Estructura de archivos
```
~/kwalia-website-essays/
├── index.html                    # Página índice de ensayos
├── data/
│   └── essays.json               # Metadata estructurada
├── essays/
│   ├── youre-already-a-cyborg.html
│   ├── ya-eres-un-cyborg.html
│   ├── why-corporations-are-people.html
│   ├── por-que-las-empresas-son-personas.html
│   ├── ... (106 archivos HTML total)
├── assets/
│   └── [imágenes de ensayos]
└── stories/
    └── [heredado de kwalia-website]
```

### Convención de nombres de archivo
- **Inglés:** `slug-with-dashes.html`
- **Español:** `slug-con-guiones.html`
- Sin espacios, todo minúsculas
- Cada ensayo tiene dos archivos (uno por idioma)

---

## 3. ESTRUCTURA DE UN ENSAYO

### Archivo HTML típico
Cada ensayo es un HTML completo con:
- DOCTYPE y meta tags
- Open Graph para redes sociales
- CSS (embebido o vinculado a stylesheet compartido)
- Contenido del ensayo
- Links discretos a libros relacionados
- Navegación de retorno al índice

### Metadata en essays.json
```json
{
  "id": "youre-already-a-cyborg",
  "slug": {
    "en": "youre-already-a-cyborg",
    "es": "ya-eres-un-cyborg"
  },
  "title": {
    "en": "You're Already a Cyborg (And That's Fine)",
    "es": "Ya eres un cyborg (y no pasa nada)"
  },
  "subtitle": {
    "en": "On the merger that already happened while nobody was looking.",
    "es": "Sobre la fusion que ya ocurrio mientras nadie miraba."
  },
  "excerpt": {
    "en": "Every time you use your phone to remember something, you're extending your mind into a machine.",
    "es": "Cada vez que usas el movil para recordar algo, estas extendiendo tu mente hacia una maquina."
  },
  "date": "2026-01-19",
  "readTime": 5,
  "primaryBook": "mindkind",
  "sourceIdeas": ["cognitive-externalization", "extended-mind-thesis"],
  "tmmTopics": ["extended-mind-thesis", "cognitive-externalization", "programmable-desire", "socrates-writing"],
  "status": "published"
}
```

### Campos de metadata
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | string | Identificador único |
| `slug` | {en, es} | URLs amigables por idioma |
| `title` | {en, es} | Título completo bilingüe |
| `subtitle` | {en, es} | Subtítulo/gancho |
| `excerpt` | {en, es} | Extracto para tarjetas/SEO |
| `date` | ISO date | Fecha de publicación |
| `readTime` | number | Minutos de lectura estimados |
| `primaryBook` | string | Libro fuente principal ("mindkind" o "udair") |
| `sourceIdeas` | array | Ideas conceptuales origen |
| `tmmTopics` | array | Temas para cross-linking |
| `status` | string | "published", "draft", "scheduled" |

---

## 4. INVENTARIO DE ENSAYOS (2026-01-19)

### Estadísticas
- **Archivos HTML generados:** 106
- **Ensayos únicos (pares EN+ES):** ~53
- **Ensayos con metadata completa:** 10
- **Pendientes de metadata:** ~43

### Lista de ensayos con metadata (essays.json)
1. `youre-already-a-cyborg` — Mente extendida, somos cyborgs
2. `why-corporations-are-people` — Personería corporativa vs IA
3. `your-thoughts-arent-yours` — Influencia algorítmica en pensamiento
4. `the-case-for-ai-rights` — Derechos IA sin necesidad de consciencia
5. `how-algorithms-learned-to-want` — Deseo programado
6. `digital-anesthesia` — Adormecimiento cognitivo digital
7. `when-rivers-became-people` — Personería de entidades naturales
8. `the-last-human-thought` — Especulativo sobre futuro
9. `50-questions-well-be-asking-in-2035` — Preguntas futuras
10. `the-algorithm-knows-you` — Conocimiento algorítmico personal

### Ensayos generados (sin metadata completa aún)
Archivos en `~/kwalia-website-essays/essays/`:
- `a-day-in-the-stratified-mindkind.html`
- `a-favor-de-desconectarse-a-veces.html`
- `administrative-realism.html`
- `ai-fiction-sounds-like.html`
- `como-detectar-deseo-manufacturado.html`
- `como-leer-en-la-era-de-la-distraccion.html`
- `como-tener-una-opinion-que-sea-realmente-tuya.html`
- `contrato-social-nunca-firmamos.html`
- `cuando-confiar-en-la-ia.html`
- `deberia-ia-escribir-emails.html`
- `deja-de-preguntar-si-la-ia-es-consciente.html`
- `el-arte-del-malentendido-productivo.html`
- `el-extrano-nuevo-mundo-del-arte-ia.html`
- `el-mito-de-la-herramienta-neutral.html`
- `el-problema-de-preguntar-si-la-ia-puede-sentir.html`
- `espectro-de-ia.html`
- `estas-entrenando-ia-ahora-mismo.html`
- `heteronym-returns.html`
- ... y ~80 más

---

## 5. CATEGORÍAS TEMÁTICAS

### Mente extendida / Cyborg
Ideas de Mindkind sobre cognición distribuida:
- `youre-already-a-cyborg`
- `your-thoughts-arent-yours`
- `digital-anesthesia`

### Derechos y personería
Ideas de UDAIR sobre frameworks legales:
- `why-corporations-are-people`
- `the-case-for-ai-rights`
- `when-rivers-became-people`

### Algoritmos y deseo manufacturado
Intersección de ambos libros:
- `how-algorithms-learned-to-want`
- `the-algorithm-knows-you`
- `how-to-spot-manufactured-desire`

### Especulativo / Futuro
Extrapolaciones filosóficas:
- `50-questions-well-be-asking-in-2035`
- `the-last-human-thought`
- `a-day-in-the-stratified-mindkind`

---

## 6. HISTORIAL DE SESIONES

### Sesión principal: `6ea3db25-a027-4f0b-b2fc-315f48164ff7`

**Fechas:** 2026-01-16 a 2026-01-19

**Logros:**
1. Refactorización del sitio kwalia-website a arquitectura modular
2. Creación del sistema de ensayos bilingües
3. Generación de 106 archivos HTML de ensayos
4. Estructura de essays.json con 10 entradas completas
5. Integración con el índice principal

**Incidente:** Sesión bloqueada por imagen demasiado grande (Alden Pierce portrait)

**Resolución:**
```bash
# Opción 1: Doble ESC en terminal bloqueada
# Opción 2: Kill y resume
kill [PID]
claude --resume 6ea3db25-a027-4f0b-b2fc-315f48164ff7
```

---

## 7. FLUJO DE TRABAJO

### Para crear un nuevo ensayo

1. **Escribir contenido** en ambos idiomas
2. **Crear archivos HTML:**
   - `essays/nuevo-ensayo.html` (inglés)
   - `essays/nuevo-ensayo-es.html` (español)
3. **Añadir metadata** a `data/essays.json`
4. **Verificar** que index.html lista el nuevo ensayo
5. **Commit y push:**
   ```bash
   cd ~/kwalia-website-essays
   git add essays/nuevo-ensayo*.html data/essays.json
   git commit -m "Add essay: Nuevo Ensayo"
   git push origin main
   ```

### Para actualizar metadata

Editar `data/essays.json` y asegurarse de:
- ID único
- Slugs correctos para ambos idiomas
- Títulos y excerpts en EN y ES
- primaryBook correcto (mindkind o udair)
- status = "published" cuando esté listo

---

## 8. LECCIONES APRENDIDAS

### Error: Imagen demasiado grande
**Fecha:** 2026-01-19
**Problema:** Al intentar procesar la imagen de perfil de Alden Pierce, la API retornó "Image was too large" repetidamente, bloqueando la sesión.

**Causa:** Las imágenes mayores a ~5MB no pueden procesarse en el contexto de Claude.

**Solución:**
1. Optimizar imágenes antes de intentar procesarlas
2. Si la sesión se bloquea, cancelar y reanudar
3. Indicar explícitamente "skip the image" o "forget about the image"

**Prevención:**
- Mantener imágenes < 1MB para procesar
- Usar herramientas externas (ImageMagick, etc.) para optimizar
- No incluir imágenes grandes en solicitudes de análisis

---

## 9. PENDIENTES

### Alta prioridad
- [ ] Completar metadata en essays.json para todos los ensayos
- [ ] Añadir imagen de Alden Pierce optimizada (< 1MB)
- [ ] Verificar todos los links internos

### Media prioridad
- [ ] Revisar consistencia de CSS entre ensayos
- [ ] Añadir analytics (si aplica)
- [ ] Crear sistema de tags/categorías visual

### Baja prioridad
- [ ] Generar sitemap.xml para SEO
- [ ] Añadir RSS feed de ensayos
- [ ] Implementar búsqueda de ensayos

---

## 10. COMANDOS ÚTILES

```bash
# Contar ensayos
ls ~/kwalia-website-essays/essays/*.html | wc -l

# Ver ensayos sin par en español
ls ~/kwalia-website-essays/essays/ | grep -v "^[a-z].*-[a-z]" | sort

# Verificar essays.json
cat ~/kwalia-website-essays/data/essays.json | jq '.[] | .id'

# Reanudar sesión de trabajo
claude --resume 6ea3db25-a027-4f0b-b2fc-315f48164ff7

# Push cambios
cd ~/kwalia-website-essays && git add . && git commit -m "Update essays" && git push
```

---

## 11. CONTACTO Y REFERENCIAS

- **Repositorio:** https://github.com/KwaliaAI/kwalia-website
- **Sitio live:** https://kwalia.ai (cuando se active GitHub Pages)
- **Documentación principal:** ~/CLAUDE.md (sección KWALIA ESSAYS)

---

*Documento generado el 2026-01-19. Actualizar después de cambios significativos.*
