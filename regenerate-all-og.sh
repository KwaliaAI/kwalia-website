#!/bin/bash
#
# regenerate-all-og.sh — Regenerate all OG images and update HTML files
#
# Usage:
#   ./regenerate-all-og.sh
#
# What it does:
#   1. Runs batch OG generator for English essays
#   2. Runs batch OG generator for Spanish essays
#   3. Updates OG tags in all HTML files that have matching essays.json entries
#   4. Reports any HTML files without essays.json metadata

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Regenerating All OG Images ==="
echo ""

# Create output directory
mkdir -p assets/og

# Step 1: Generate EN images
echo "Generating English OG images..."
python3 og_generator.py --batch data/essays.json --output-dir assets/og/ --lang en

# Step 2: Generate ES images
echo ""
echo "Generating Spanish OG images..."
python3 og_generator.py --batch data/essays.json --output-dir assets/og/ --lang es

# Step 3: Update all HTML files
echo ""
echo "Updating OG tags in HTML files..."
python3 update_og_tags.py

# Summary
echo ""
echo "=== Complete ==="
IMAGE_COUNT=$(ls -1 assets/og/*.jpg 2>/dev/null | wc -l)
echo "Total OG images: $IMAGE_COUNT"
echo ""
echo "To commit all changes:"
echo "  git add assets/og/ essays/"
echo "  git commit -m \"Regenerate all OG images\""
echo "  git push"
