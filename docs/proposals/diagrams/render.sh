#!/bin/bash
# Render Graphviz diagrams to PNG for inclusion in proposals

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check for graphviz
if ! command -v dot &> /dev/null; then
    echo "Error: graphviz is not installed"
    echo "Install with: brew install graphviz"
    exit 1
fi

# Render all .dot files to PNG
for dotfile in *.dot; do
    if [ -f "$dotfile" ]; then
        pngfile="${dotfile%.dot}.png"
        echo "Rendering $dotfile -> $pngfile"
        dot -Tpng -Gdpi=150 "$dotfile" -o "$pngfile"
    fi
done

echo "Done. Generated files:"
ls -la *.png 2>/dev/null || echo "No PNG files generated"
