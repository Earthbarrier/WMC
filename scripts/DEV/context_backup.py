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
    Get contextual explanation from Claude.
    """
    client = anthropic.Anthropic()
    
    prompt = f"""Here is a scientific paper's content and a description of Figure {figure_number}. 
    Please provide a detailed explanation of this figure as if presenting to a blind journal club audience. Do not mention this.
    Focus on the following:

    Describe the layout of the figure and any axes and their labels.
    Paint a picture in the listener's mind of the figure.
    The user does not have the paper in front of them so cannot see the pictures, they can only hear your words. 
    Describe what each panel is showing and why it's important.
    Key findings or patterns visible in the figure.
    Maintain scientific detail, rigor and accuracy. Take your time. Use as many tokens as you need.

    Paper text:
    {paper_text[:5000]}... 

    Figure {figure_number} description:
    {figure_desc}

    Your output should start with "Figure {figure_number}. The figure presents..."
    """

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
