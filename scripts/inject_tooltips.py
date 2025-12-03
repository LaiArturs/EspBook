#!/usr/bin/env python3
"""
inject_tooltips.py

Read `data/translations.yaml` and inject tooltip markers into Markdown files
under `content/`.

Usage:
  ./scripts/inject_tooltips.py [work_dir] [mode]

Arguments:
  work_dir  Directory containing `content/` and `data/` (default: current dir)
  mode      'hugo' to inject Hugo shortcodes (default), 'epub' to inject
            pandoc-style footnotes for EPUB generation.

This script creates a backup file for each modified markdown file with a
`.bak` suffix.
"""
import argparse
import re
from pathlib import Path
import sys

try:
    import yaml
except Exception:
    yaml = None


def load_translations(yaml_path):
    if yaml:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("tooltips", []) if data else []

    # Fallback simple parser if PyYAML is not available
    tooltips = []
    current = {}
    with open(yaml_path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if line.startswith("- word:"):
                # new entry
                if current:
                    tooltips.append(current)
                current = {}
                word = line.split(":", 1)[1].strip().strip('"')
                current["word"] = word
            elif line.startswith("definition:") or line.startswith("- definition:"):
                definition = line.split(":", 1)[1].strip().strip('"')
                current["definition"] = definition
        if current:
            tooltips.append(current)
    return tooltips


def inject_into_file(path: Path, tooltip_list, mode: str, backup_suffix: str = ".bak",
                     dry_run: bool = False, skip_front_matter: bool = False, limit_first: int = None):
    text = path.read_text(encoding="utf-8")

    # Split front matter (YAML) if requested
    front = ""
    body = text
    if skip_front_matter and text.startswith("---"):
        parts = text.split("\n---\n", 1)
        if len(parts) == 2:
            front = parts[0] + "\n---\n"
            body = parts[1]

    total_replacements = 0
    out_lines = []
    in_code = False
    # Track occurrences per word
    word_counts = {}

    # Prepare combined regex for all words (longest first)
    words = [w for w, _ in tooltip_list]
    if words:
        words_sorted = sorted(words, key=lambda x: len(x), reverse=True)
        combined_pattern = re.compile(r"\b(" + "|".join(re.escape(w) for w in words_sorted) + r")\b")
        repl_map = {w: d for w, d in tooltip_list}
    else:
        combined_pattern = None
        repl_map = {}

    for line in body.splitlines(keepends=True):
        stripped = line.lstrip()
        # toggle code block state for ``` or ~~~ fences
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code = not in_code
            out_lines.append(line)
            continue

        if in_code:
            out_lines.append(line)
            continue

        # find shortcode ranges {{< ... >}} in the line and skip replacements inside them
        shortcode_ranges = []
        start_pos = 0
        while True:
            i = line.find("{{<", start_pos)
            if i == -1:
                break
            j = line.find(">}}", i)
            if j == -1:
                break
            shortcode_ranges.append((i, j + 3))
            start_pos = j + 3

        def in_shortcode(pos):
            for a, b in shortcode_ranges:
                if a <= pos < b:
                    return True
            return False

        if combined_pattern is None:
            out_lines.append(line)
            continue

        # replacement function that skips matches inside existing shortcodes and limits per word
        def _replacer(m):
            nonlocal total_replacements
            st = m.start()
            if in_shortcode(st):
                return m.group(0)
            word = m.group(1)
            
            # Track and limit occurrences per word
            if word not in word_counts:
                word_counts[word] = 0
            if limit_first is not None and word_counts[word] >= limit_first:
                return m.group(0)
            
            word_counts[word] += 1
            total_replacements += 1
            
            definition = repl_map.get(word, "")
            if mode == "epub":
                rep = f"{word}^[{definition}]"
            else:
                rep = f"{{{{< tooltip word=\"{word}\" def=\"{definition}\" >}}}}"
            return rep

        modified_line = combined_pattern.sub(_replacer, line)
        out_lines.append(modified_line)

    new_text = front + "".join(out_lines)

    if total_replacements == 0:
        return 0

    if dry_run:
        print(f"Dry-run: {path} would have {total_replacements} replacements")
        return total_replacements

    # backup and write
    (path.parent / (path.name + backup_suffix)).write_text(text, encoding="utf-8")
    path.write_text(new_text, encoding="utf-8")
    return total_replacements


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("work_dir", nargs="?", default=".")
    parser.add_argument("mode", nargs="?", default="hugo", choices=["hugo", "epub"],
                        help="Injection mode: 'hugo' for shortcodes, 'epub' for pandoc footnotes")
    parser.add_argument("--dry-run", action="store_true", help="Do not write files; report changes")
    parser.add_argument("--skip-front-matter", action="store_true", help="Do not modify YAML front matter")
    parser.add_argument("--limit-first", type=int, default=None, help="Limit to first N occurrences of each word per file")
    args = parser.parse_args()

    work_dir = Path(args.work_dir)
    content_dir = work_dir / "content"
    translations_file = work_dir / "data" / "translations.yaml"

    if not translations_file.exists():
        print(f"Translations file not found: {translations_file}")
        sys.exit(1)
    if not content_dir.exists():
        print(f"Content directory not found: {content_dir}")
        sys.exit(1)

    tooltips = load_translations(translations_file)
    tooltip_list = [(t["word"], t.get("definition", "")) for t in tooltips]
    tooltip_list.sort(key=lambda x: len(x[0]), reverse=True)

    print(f"Found {len(tooltip_list)} tooltip definitions")

    for md in content_dir.rglob("*.md"):
        print(f"Processing: {md}")
        n = inject_into_file(md, tooltip_list, args.mode, dry_run=args.dry_run,
                             skip_front_matter=args.skip_front_matter,
                             limit_first=args.limit_first)
        if n:
            if args.dry_run:
                print(f"  would change: {n} replacements")
            else:
                print(f"  ✓ Updated ({n} replacements)")
        else:
            print("  no changes")

    print("Done! Tooltips injected.")


if __name__ == "__main__":
    main()
