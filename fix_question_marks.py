#!/usr/bin/env python3
"""
Fix Spanish question and exclamation marks.
Adds missing opening marks (¿ and ¡).
"""

import re
from pathlib import Path


def add_opening_question_marks(text: str) -> str:
    """Add opening question marks to Spanish questions."""
    result = text

    # Pattern: sentence/tag boundary followed by question word, ending with ?
    # We need to find questions that end with ? but don't have ¿ at the start

    # Questions starting after HTML tags or at line start
    patterns = [
        # After <p> tag
        (r'(<p[^>]*>)([A-ZÁÉÍÓÚÜ][^<]*\?</p>)', add_question_mark_after_tag),
        # After other content in <p> - questions starting mid-sentence
        (r'(\. )([A-ZÁÉÍÓÚÜ][^.?!]*\?)', add_question_mark_inline),
    ]

    for pattern, handler in patterns:
        result = re.sub(pattern, handler, result)

    return result


def add_question_mark_after_tag(match):
    """Add ¿ after opening tag if question doesn't have it."""
    tag = match.group(1)
    content = match.group(2)

    # Check if already has ¿
    if content.startswith('¿'):
        return match.group(0)

    return f'{tag}¿{content}'


def add_question_mark_inline(match):
    """Add ¿ before inline question."""
    prefix = match.group(1)
    content = match.group(2)

    if content.startswith('¿'):
        return match.group(0)

    return f'{prefix}¿{content}'


def fix_spanish_punctuation(text: str) -> str:
    """Fix Spanish punctuation marks."""
    result = text

    # Fix questions - find text ending in ? that doesn't start with ¿
    # This is complex because we need to find the start of the question

    # Pattern for questions inside <p> tags
    def fix_p_questions(match):
        full = match.group(0)
        tag_open = match.group(1) or ''
        content = match.group(2)
        tag_close = match.group(3) or ''

        # If already has ¿, return as-is
        if '¿' in content:
            return full

        # If ends with ?, add ¿ at the start of the content
        if content.rstrip().endswith('?'):
            # Find where the question starts (after last sentence boundary or at start)
            # Look for ". " or start of content
            parts = re.split(r'(\. )', content)
            if len(parts) > 1:
                # Multiple sentences, only fix the last one
                last_idx = len(parts) - 1
                for i in range(last_idx, -1, -1):
                    if parts[i].strip().endswith('?') and not parts[i].strip().startswith('¿'):
                        parts[i] = '¿' + parts[i].lstrip()
                        break
                content = ''.join(parts)
            else:
                # Single sentence question
                content = '¿' + content.lstrip()

        return f'{tag_open}{content}{tag_close}'

    # Fix questions in paragraphs
    result = re.sub(
        r'(<p[^>]*>)([^<]+\?)(</p>)',
        fix_p_questions,
        result
    )

    # Fix exclamations - simpler pattern
    # Common Spanish exclamations that need ¡
    exclamation_words = ['Felicidades', 'Gracias', 'Anotado', 'Bienvenido', 'Excelente',
                         'Perfecto', 'Genial', 'Fantástico', 'Increíble', 'Bravo']

    for word in exclamation_words:
        # Pattern: word followed by ! without ¡ before
        pattern = rf'(?<![¡\w])({word}!)'
        result = re.sub(pattern, rf'¡\1', result)

    return result


def process_spanish_essays(essays_dir: Path, dry_run: bool = False) -> dict:
    """Process all Spanish essays and fix punctuation."""
    stats = {
        'processed': 0,
        'modified': 0,
        'errors': 0,
        'files': []
    }

    for filepath in sorted(essays_dir.glob("*.html")):
        if filepath.name == "index.html":
            continue

        try:
            content = filepath.read_text(encoding='utf-8')

            # Check if Spanish
            if 'lang="es"' not in content[:500]:
                continue

            stats['processed'] += 1

            # Apply fixes
            fixed_content = fix_spanish_punctuation(content)

            if fixed_content != content:
                stats['modified'] += 1
                stats['files'].append(filepath.name)

                if not dry_run:
                    filepath.write_text(fixed_content, encoding='utf-8')
                    print(f"  Fixed: {filepath.name}")
                else:
                    print(f"  Would fix: {filepath.name}")

        except Exception as e:
            stats['errors'] += 1
            print(f"  Error processing {filepath.name}: {e}")

    return stats


if __name__ == "__main__":
    import sys

    essays_dir = Path("essays")

    if not essays_dir.exists():
        print("Error: essays directory not found")
        sys.exit(1)

    dry_run = "--dry-run" in sys.argv

    print(f"Processing Spanish essays for punctuation {'(dry run)' if dry_run else ''}...")
    stats = process_spanish_essays(essays_dir, dry_run=dry_run)

    print(f"\nResults:")
    print(f"  Processed: {stats['processed']} Spanish essays")
    print(f"  Modified: {stats['modified']} files")
    print(f"  Errors: {stats['errors']}")

    if stats['files']:
        print(f"\nModified files:")
        for f in stats['files']:
            print(f"  - {f}")
