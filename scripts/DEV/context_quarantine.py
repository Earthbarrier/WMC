import os
import sys
import anthropic
import PyPDF2

def read_pdf(pdf_path):
    """
    Extract text from PDF file.
    """
    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        sys.exit(1)

def read_description(desc_path):
    """
    Read the figure description from text file.
    """
    try:
        with open(desc_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except Exception as e:
        print(f"Error reading description file: {e}")
        sys.exit(1)

def get_contextual_explanation(paper_text, figure_desc, figure_number):
    """
    Get detailed contextual explanation from Claude, combining figure description with paper context.
    """
    client = anthropic.Anthropic()
    
    prompt = f"""You are helping explain a scientific figure in detail to researchers who cannot see the figure. Given the paper text and figure description, provide a comprehensive explanation that:

Detailed Visual & Technical Explanation
- Walk through each panel (a, b, c, etc.) systematically
- Explain the experimental setup shown in each panel
- Describe the control conditions and experimental variables
- Detail any genetic constructs, molecular mechanisms, or technical approaches shown
- Explain the significance of different colors, shapes, or patterns
- Define any specialized notation or symbols

Data Interpretation
- Explain what patterns or trends are visible in the data
- Compare different conditions or treatments shown
- Highlight any statistical significance indicated

Please maintain rigorous scientific accuracy while making the explanation accessible. Assume an expert audience who cannot see the figure but needs to understand all technical details.

Paper text:
{paper_text[:5000]}...

Figure {figure_number} description:
{figure_desc}

Begin your response with "Figure {figure_number}. This figure demonstrates..." and proceed systematically through the elements above."""

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8000,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        return message.content[0].text
    except Exception as e:
        print(f"Error getting explanation from Claude: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Detailed error: {e.response.text}")
        sys.exit(1)

def save_explanation(explanation, output_path):
    """
    Save the contextual explanation to a file.
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(explanation)
        print(f"\nContextual explanation saved to: {output_path}")
    except Exception as e:
        print(f"Error saving explanation to file: {e}")
        sys.exit(1)

def extract_figure_number(filename):
    """
    Extract figure number from filename or description.
    """
    # This is a simple implementation - adjust based on your naming convention
    try:
        return int(filename.split('figure_')[1].split('_')[0])
    except:
        return 1  # Default to figure 1 if can't parse

def main():
    if len(sys.argv) != 3:
        print("Usage: python explain_figure.py <path_to_paper.pdf> <path_to_figure_description.txt>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    desc_path = sys.argv[2]

    # Check if files exist
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file '{pdf_path}' does not exist.")
        sys.exit(1)
    if not os.path.exists(desc_path):
        print(f"Error: Description file '{desc_path}' does not exist.")
        sys.exit(1)

    # Read input files
    paper_text = read_pdf(pdf_path)
    figure_desc = read_description(desc_path)
    
    # Get figure number from filename
    figure_number = extract_figure_number(os.path.basename(desc_path))

    # Get contextual explanation
    explanation = get_contextual_explanation(paper_text, figure_desc, figure_number)

    # Generate output filename and save explanation
    output_path = os.path.splitext(desc_path)[0] + "_contextual.txt"
    save_explanation(explanation, output_path)

    # Also print to console
    print("\nContextual Figure Explanation:")
    print("-" * 50)
    print(explanation)
    print("-" * 50)

if __name__ == "__main__":
    main()
