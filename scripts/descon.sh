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

# Directory containing figures
FIGS_DIR="figs"

# Check if figures directory exists
if [ ! -d "$FIGS_DIR" ]; then
    echo "Error: Figures directory '$FIGS_DIR' not found."
    exit 1
fi

echo "Step 1: Processing all figures with describe.py..."
echo "----------------------------------------"

# First, process all figures to generate descriptions
for fig in "$FIGS_DIR"/figure_*.png; do
    if [ -f "$fig" ]; then
        # Skip panel files in this initial pass
        if [[ ! "$fig" == *"panel"* ]]; then
            echo "Processing figure: $fig"
            python ../../scripts/describe.py "$fig"
            sleep 1
        fi
    fi
done

# Then process all panels
for fig in "$FIGS_DIR"/figure_*_panel_*.png; do
    if [ -f "$fig" ]; then
        echo "Processing panel: $fig"
        python ../../scripts/describe.py "$fig"
        sleep 1
    fi
done

echo -e "\nStep 2: Creating contextual descriptions..."
echo "----------------------------------------"

# Function to process a detailed figure and its panels
process_detailed_figure() {
    local base_num=$1
    local full_desc="$FIGS_DIR/figure_${base_num}_full_blind.txt"
    local temp_dir="$FIGS_DIR/temp_concat"
    mkdir -p "$temp_dir"
    
    # Process each panel for this figure
    for panel_desc in "$FIGS_DIR"/figure_${base_num}_panel_*_blind.txt; do
        if [ -f "$panel_desc" ]; then
            echo "Processing detailed figure ${base_num} with panel: $panel_desc"
            python ../../scripts/context.py "$PAPER_PATH" "$panel_desc" "$full_desc"
            sleep 1
        fi
    done

    # Create flowing narrative concatenation
    echo "Figure ${base_num} shows a series of experiments examining " > "$FIGS_DIR/figure_${base_num}_blind_contextual.txt"
    
    # Add each panel's contextual description in order, without headers or separators
    for panel_context in $(ls -v "$FIGS_DIR"/figure_${base_num}_panel_*_blind_contextual.txt 2>/dev/null); do
        if [ -f "$panel_context" ]; then
            # Remove any "Figure X..." prefix if present
            sed 's/^Figure [0-9]\+\.//' "$panel_context" >> "$FIGS_DIR/figure_${base_num}_blind_contextual.txt"
            echo -e "\n" >> "$FIGS_DIR/figure_${base_num}_blind_contextual.txt"
        fi
    done
}

# Process all figures
for desc in "$FIGS_DIR"/figure_*_blind.txt; do
    if [ -f "$desc" ]; then
        # Check if this is a full figure (part of a detailed figure)
        if [[ "$desc" == *"_full_blind.txt" ]]; then
            # Extract base figure number
            base_num=$(echo "$desc" | sed -n 's/.*figure_\([0-9]\+\)_full_blind.*/\1/p')
            process_detailed_figure "$base_num"
        # Process regular figures (not panels or full figures)
        elif [[ ! "$desc" == *"_panel_"* ]] && [[ ! "$desc" == *"_full_"* ]]; then
            echo "Processing regular figure: $desc"
            python ../../scripts/context.py "$PAPER_PATH" "$desc"
            sleep 1
        fi
    fi
done

echo -e "\nAll processing complete!"
echo "----------------------------------------"
echo "Generated files:"
echo "Description files:"
ls -1 "$FIGS_DIR"/*_blind.txt
echo -e "\nContextual files:"
ls -1 "$FIGS_DIR"/figure_*_blind_contextual.txt

# Optional: Clean up individual panel contextual files
# Uncomment the following lines if you want to remove individual panel files
echo -e "\nCleaning up individual panel contextual files..."
rm -f "$FIGS_DIR"/figure_*_panel_*_blind_contextual.txt
