#!/bin/bash
#
# publish-essay.sh — Publish a new essay with OG image generation
#
# Usage:
#   ./publish-essay.sh \
#     --slug-en "my-essay" \
#     --slug-es "mi-ensayo" \
#     --title-en "My Essay Title" \
#     --title-es "Título de Mi Ensayo" \
#     --subtitle-en "A compelling subtitle" \
#     --subtitle-es "Un subtítulo convincente" \
#     --category "AI Rights"
#
# What it does:
#   1. Generates EN OG image → assets/og/{slug-en}.jpg
#   2. Generates ES OG image → assets/og/{slug-es}.jpg
#   3. Verifies HTML files exist in essays/
#   4. Updates OG meta tags in both HTML files
#   5. Stages all changed files for git
#   6. Prints summary

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --slug-en) SLUG_EN="$2"; shift 2 ;;
        --slug-es) SLUG_ES="$2"; shift 2 ;;
        --title-en) TITLE_EN="$2"; shift 2 ;;
        --title-es) TITLE_ES="$2"; shift 2 ;;
        --subtitle-en) SUBTITLE_EN="$2"; shift 2 ;;
        --subtitle-es) SUBTITLE_ES="$2"; shift 2 ;;
        --category) CATEGORY="$2"; shift 2 ;;
        --help|-h)
            echo "Usage: $0 --slug-en SLUG --slug-es SLUG --title-en TITLE --title-es TITLE [--subtitle-en TEXT] [--subtitle-es TEXT] [--category CAT]"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Validate required arguments
if [[ -z "$SLUG_EN" || -z "$SLUG_ES" || -z "$TITLE_EN" || -z "$TITLE_ES" ]]; then
    echo "Error: --slug-en, --slug-es, --title-en, and --title-es are required"
    echo "Run with --help for usage"
    exit 1
fi

SUBTITLE_EN="${SUBTITLE_EN:-}"
SUBTITLE_ES="${SUBTITLE_ES:-}"
CATEGORY="${CATEGORY:-}"

echo "=== Publishing Essay ==="
echo "EN: $SLUG_EN - $TITLE_EN"
echo "ES: $SLUG_ES - $TITLE_ES"
echo ""

# Step 1 & 2: Generate OG images
echo "Generating OG images..."
mkdir -p assets/og

python3 og_generator.py \
    --title "$TITLE_EN" \
    --subtitle "$SUBTITLE_EN" \
    --slug "$SLUG_EN" \
    --category "$CATEGORY" \
    --output "assets/og/${SLUG_EN}.jpg"

python3 og_generator.py \
    --title "$TITLE_ES" \
    --subtitle "$SUBTITLE_ES" \
    --slug "$SLUG_ES" \
    --category "$CATEGORY" \
    --output "assets/og/${SLUG_ES}.jpg"

echo "  ✓ Generated assets/og/${SLUG_EN}.jpg"
echo "  ✓ Generated assets/og/${SLUG_ES}.jpg"

# Step 3: Verify HTML files exist
HTML_EN="essays/${SLUG_EN}.html"
HTML_ES="essays/${SLUG_ES}.html"

if [[ ! -f "$HTML_EN" ]]; then
    echo "  ⚠ Warning: $HTML_EN not found (create it first with build_essays.py)"
fi

if [[ ! -f "$HTML_ES" ]]; then
    echo "  ⚠ Warning: $HTML_ES not found (create it first with build_essays.py)"
fi

# Step 4: Update OG tags in HTML files
echo ""
echo "Updating OG tags..."
if [[ -f "$HTML_EN" ]]; then
    python3 update_og_tags.py "$HTML_EN"
fi
if [[ -f "$HTML_ES" ]]; then
    python3 update_og_tags.py "$HTML_ES"
fi

# Step 5: Stage files for git
echo ""
echo "Staging files..."
git add "assets/og/${SLUG_EN}.jpg" "assets/og/${SLUG_ES}.jpg" 2>/dev/null || true

if [[ -f "$HTML_EN" ]]; then
    git add "$HTML_EN" 2>/dev/null || true
fi
if [[ -f "$HTML_ES" ]]; then
    git add "$HTML_ES" 2>/dev/null || true
fi

# Step 6: Summary
echo ""
echo "=== Summary ==="
echo "Created:"
echo "  - assets/og/${SLUG_EN}.jpg"
echo "  - assets/og/${SLUG_ES}.jpg"
echo ""
echo "Updated:"
[[ -f "$HTML_EN" ]] && echo "  - $HTML_EN"
[[ -f "$HTML_ES" ]] && echo "  - $HTML_ES"
echo ""
echo "Files staged for commit. Run:"
echo "  git commit -m \"Add OG images for: $TITLE_EN\""
echo "  git push"
