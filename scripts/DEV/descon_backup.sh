#!/bin/bash

# Check if PDF file argument is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path_to_paper.pdf>"
    exit 1
fi

PAPER_PATH="$1"

# Check if paper exists
if [ ! -f "$PAPER_PATH" ]; then
    echo "Error: Paper file '$PAPER_PATH' not found."
    exit 1
fi

# Directory containing figures (assuming it's 'figs')
FIGS_DIR="figs"

# Check if figures directory exists
if [ ! -d "$FIGS_DIR" ]; then
    echo "Error: Figures directory '$FIGS_DIR' not found."
    exit 1
fi

echo "Step 1: Processing all figures with describe.py..."
echo "----------------------------------------"

# Process each figure file
for fig in "$FIGS_DIR"/figure_*.png; do
    if [ -f "$fig" ]; then
        echo "Processing figure: $fig"
        python ../../scripts/describe.py "$fig"
        # Add small delay to prevent API rate limiting
        sleep 1
    fi
done

echo -e "\nStep 2: Creating contextual descriptions..."
echo "----------------------------------------"

# Process each description file
for desc in "$FIGS_DIR"/figure_*_blind.txt; do
    if [ -f "$desc" ]; then
        echo "Processing description: $desc"
        python ../../scripts/context.py "$PAPER_PATH" "$desc"
        # Add small delay to prevent API rate limiting
        sleep 1
    fi
done

echo -e "\nAll processing complete!"
echo "----------------------------------------"
echo "Generated files:"
echo "Description files:"
ls -1 "$FIGS_DIR"/*_blind.txt
echo -e "\nContextual files:"
ls -1 "$FIGS_DIR"/*_contextual.txt
