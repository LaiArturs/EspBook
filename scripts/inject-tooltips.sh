#!/usr/bin/env bash
set -euo pipefail

# inject-tooltips.sh
# Reads translations.yaml and injects {{< tooltip >}} shortcodes into markdown files
# Preserves original files and creates .bak backups
# Uses Python for reliable YAML parsing and regex substitution
# Usage: ./scripts/inject-tooltips.sh [work-dir]

WORK_DIR="${1:-.}"
CONTENT_DIR="$WORK_DIR/content"
TRANSLATIONS_FILE="$WORK_DIR/data/translations.yaml"
BACKUP_SUFFIX=".bak"

if [ ! -f "$TRANSLATIONS_FILE" ]; then
  echo "Error: Translations file not found at $TRANSLATIONS_FILE"
  exit 1
fi

if [ ! -d "$CONTENT_DIR" ]; then
  echo "Error: Content directory not found at $CONTENT_DIR"
  exit 1
fi

echo "Injecting tooltips into markdown files..."
echo "  Translations: $TRANSLATIONS_FILE"
echo "  Content dir: $CONTENT_DIR"

# Mode: 'hugo' (default) produces Hugo shortcodes; 'epub' produces pandoc footnotes
MODE="${2:-hugo}"

# Thin wrapper that delegates to the standalone Python script.
# Usage: ./scripts/inject-tooltips.sh [work_dir] [mode]

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required"
  exit 1
fi

python3 "$(dirname "$0")/inject_tooltips.py" "$WORK_DIR" "$MODE"
