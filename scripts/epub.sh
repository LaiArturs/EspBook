#!/usr/bin/env bash
set -euo pipefail

# Simple EPUB build script using pandoc
# - Collects markdown files under content/docs
# - Installs pandoc if missing (GitHub runners allow apt)

OUT_DIR="${OUT_DIR:-public}"
mkdir -p "$OUT_DIR"
OUT_FILE="$OUT_DIR/ebook.epub"

if ! command -v pandoc >/dev/null 2>&1; then
  echo "pandoc not found — installing pandoc"
  sudo apt-get update
  sudo apt-get install -y pandoc
fi

echo "Collecting markdown files from content/docs..."
mapfile -t files < <(find content/docs -type f -name '*.md' | sort)
if [ ${#files[@]} -eq 0 ]; then
  echo "No markdown files found under content/docs. Trying content/ root..."
  mapfile -t files < <(find content -maxdepth 2 -type f -name '*.md' | sort)
  if [ ${#files[@]} -eq 0 ]; then
    echo "No markdown files found. Aborting."
    exit 1
  fi
fi

echo "Files to include:"
for f in "${files[@]}"; do
  echo " - $f"
done

echo "Generating EPUB to $OUT_FILE"
pandoc --from markdown+yaml_metadata_block+smart --toc -o "$OUT_FILE" "${files[@]}"

echo "Done: $OUT_FILE"
