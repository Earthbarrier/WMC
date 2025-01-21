import re
import os
import glob

def read_figure_descriptions(figures_dir):
    """
    Read figure descriptions from text files in a directory.
    Files should be named like 'figure_1_blind_contextual.txt'
    
    Args:
        figures_dir (str): Path to directory containing figure description files
    
    Returns:
        list: List of figure descriptions in order
    """
    # Get all figure files
    pattern = os.path.join(figures_dir, 'figure_*_blind_contextual.txt')
    figure_files = glob.glob(pattern)
    
    # Sort by figure number
    figure_files.sort(key=lambda x: int(re.search(r'figure_(\d+)_', x).group(1)))
    
    # Read descriptions
    descriptions = []
    for file_path in figure_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                descriptions.append(f.read().strip())
        except Exception as e:
            print(f"Error reading figure file {file_path}: {e}")
            descriptions.append(f"[Error reading figure description for {os.path.basename(file_path)}]")
    
    return descriptions

def split_text_for_figures(text, num_figures):
    """
    Split text into chunks to intersperse with figures while preserving paragraphs.
    Returns num_figures + 1 chunks of roughly equal size.
    
    Args:
        text (str): The full text to split
        num_figures (int): Number of figures to intersperse
    
    Returns:
        list: List of text chunks
    """
    # Split into paragraphs (preserve empty lines)
    paragraphs = re.split(r'(\n\s*\n)', text)
    
    # Recombine empty lines with paragraphs
    full_paragraphs = []
    for i in range(0, len(paragraphs), 2):
        para = paragraphs[i]
        if i + 1 < len(paragraphs):
            para += paragraphs[i + 1]
        if para.strip():  # Only keep non-empty paragraphs
            full_paragraphs.append(para)
    
    # Calculate target size for each chunk
    total_length = sum(len(p) for p in full_paragraphs)
    target_chunk_size = total_length / (num_figures + 1)
    
    # Create chunks
    chunks = []
    current_chunk = []
    current_length = 0
    
    for paragraph in full_paragraphs:
        # If adding this paragraph would make the chunk too large and we haven't 
        # just started a new chunk, start a new chunk
        if (current_length + len(paragraph) > target_chunk_size * 1.1 and 
            len(chunks) < num_figures):
            chunks.append(''.join(current_chunk))
            current_chunk = []
            current_length = 0
        
        current_chunk.append(paragraph)
        current_length += len(paragraph)
    
    # Add the final chunk
    if current_chunk:
        chunks.append(''.join(current_chunk))
    
    # Ensure the last chunk contains the remaining main text
    while len(chunks) <= num_figures:
        chunks.append("")
    
    return chunks

def intersperse_figures_with_text(text, figures_dir):
    """
    Intersperse figure descriptions within text chunks.
    
    Args:
        text (str): The full text to split
        figures_dir (str): Directory containing figure description files
    
    Returns:
        str: Text with interspersed figures
    """
    # Read figure descriptions
    figure_descriptions = read_figure_descriptions(figures_dir)
    
    if not figure_descriptions:
        print("No figure descriptions found!")
        return text
        
    # Split text into chunks
    chunks = split_text_for_figures(text, len(figure_descriptions))
    
    # Combine text chunks with figure descriptions
    result = []
    for i, chunk in enumerate(chunks):
        result.append(chunk.strip())
        if i < len(figure_descriptions):
            result.append(f"\n\nFigure {i+1}: {figure_descriptions[i]}\n\n")
    
    # Ensure the final main text is appended after the last figure if needed
    if len(chunks) > len(figure_descriptions):
        result.append(chunks[len(figure_descriptions)].strip())
    
    return '\n'.join(result)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Intersperse figure descriptions in text')
    parser.add_argument('input_text', help='Path to input text file')
    parser.add_argument('figures_dir', help='Directory containing figure description files')
    parser.add_argument('output_file', help='Path to output file')
    
    args = parser.parse_args()
    
    # Read input text
    try:
        with open(args.input_text, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        print(f"Error reading input file: {e}")
        return
    
    # Process text and figures
    result = intersperse_figures_with_text(text, args.figures_dir)
    
    # Save result
    try:
        with open(args.output_file, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"Successfully wrote output to {args.output_file}")
    except Exception as e:
        print(f"Error writing output file: {e}")

if __name__ == "__main__":
    main()

