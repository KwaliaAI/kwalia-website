#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "fetch"


def _display_time(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%d-%b-%Y %H:%M")


def _line(name: str, href: str, stamp: str, size: str) -> str:
    return f'<a href="{href}">{name}</a>{" " * max(1, 40 - len(name))}{stamp}   {size}'


def _render_directory(path: Path) -> None:
    rel = path.relative_to(ROOT)
    web_path = "/fetch/" if rel == Path(".") else f"/fetch/{rel.as_posix().rstrip('/')}/"

    entries: list[tuple[str, str, str, str]] = []
    if rel != Path("."):
        entries.append(("../", "../", "", "-"))

    children = sorted(path.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
    for child in children:
        if child.name == "index.html":
            continue
        if child.is_dir():
            name = f"{child.name}/"
            entries.append((name, name, _display_time(child), "-"))
        else:
            entries.append((child.name, child.name, _display_time(child), str(child.stat().st_size)))

    lines = [_line(name, href, stamp, size) for name, href, stamp, size in entries]
    html = (
        "<!DOCTYPE html>\n"
        "<html>\n"
        "<head>\n"
        f"  <title>Index of {web_path}</title>\n"
        '  <meta charset="utf-8"/>\n'
        "</head>\n"
        "<body>\n"
        f"  <h1>Index of {web_path}</h1>\n"
        "  <pre>\n"
        + ("\n".join(lines) if lines else "")
        + "\n  </pre>\n"
        "</body>\n"
        "</html>\n"
    )
    (path / "index.html").write_text(html, encoding="utf-8")


def main() -> None:
    if not ROOT.exists():
        raise SystemExit(f"Fetch root not found: {ROOT}")

    dirs = sorted((path for path in ROOT.rglob("*") if path.is_dir()), key=lambda item: len(item.parts), reverse=True)
    for directory in dirs:
        _render_directory(directory)
    _render_directory(ROOT)


if __name__ == "__main__":
    main()
