import os
import sys
import anthropic
import PyPDF2

def read_pdf(pdf_path):
    """Extract text from PDF file."""
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
    """Read the figure description from text file."""
    try:
        with open(desc_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except Exception as e:
        print(f"Error reading description file: {e}")
        sys.exit(1)

def get_contextual_explanation(paper_text, figure_desc, figure_number, full_figure_desc=None):
    """Get contextual explanation from Claude."""
    client = anthropic.Anthropic()
    
    if full_figure_desc:
        prompt = f"""Here is a scientific paper's content and a description of a panel of Figure {figure_number}. 
        Please provide a detailed explanation of this panel as if presenting to a blind journal club audience. Do not mention this.
        Focus on the following:

        Describe the layout of the panel and any axes and their labels.
        Paint a picture in the listener's mind of the panel.
        The user does not have the paper in front of them so cannot see the pictures, they can only hear your words. 
        Key findings or patterns visible in the if they are necessary for understanding.
        Maintain scientific detail, rigor and accuracy. Take your time. Use as many tokens as you need.

        The paper text, full figure, and panel are provided. Please only discuss the panel. The other two are provided only for your understanding and context.

        Paper text:
        {paper_text[:5000]}... 

        Full Figure {figure_number} description:
        {full_figure_desc}

        Panel description:
        {figure_desc}
        """
    else:
        prompt = f"""Here is a scientific paper's content and a description of Figure {figure_number}. 
        Please provide a detailed explanation of this figure as if presenting to a blind journal club audience. Do not mention this.
        Focus on the following:

        Describe the layout of the figure and any axes and their labels.
        Paint a picture in the listener's mind of the figure.
        The user does not have the paper in front of them so cannot see the pictures, they can only hear your words. 
        Key findings or patterns visible in the figure.
        Maintain scientific detail, rigor and accuracy. Take your time. Use as many tokens as you need.

        The paper text and figure are provided. Please only discuss the figure. The paper is only provided only for your understanding and context.

        Paper text:
        {paper_text[:5000]}... 

        Figure {figure_number} description:
        {figure_desc}
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
    """Save the contextual explanation to a file."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(explanation)
        print(f"\nContextual explanation saved to: {output_path}")
    except Exception as e:
        print(f"Error saving explanation to file: {e}")
        sys.exit(1)

def extract_figure_number(filename):
    """Extract figure number from filename."""
    try:
        # Handle both regular figures and panels
        if '_panel_' in filename:
            return int(filename.split('figure_')[1].split('_panel_')[0])
        elif '_full_' in filename:
            return int(filename.split('figure_')[1].split('_full_')[0])
        else:
            return int(filename.split('figure_')[1].split('_')[0])
    except:
        print(f"Warning: Could not extract figure number from {filename}")
        return 1

def main():
    if len(sys.argv) not in [3, 4]:
        print("Usage: python context.py <path_to_paper.pdf> <path_to_description.txt> [path_to_full_figure_description.txt]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    desc_path = sys.argv[2]
    full_desc_path = sys.argv[3] if len(sys.argv) == 4 else None

    # Check if files exist
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file '{pdf_path}' does not exist.")
        sys.exit(1)
    if not os.path.exists(desc_path):
        print(f"Error: Description file '{desc_path}' does not exist.")
        sys.exit(1)
    if full_desc_path and not os.path.exists(full_desc_path):
        print(f"Error: Full figure description file '{full_desc_path}' does not exist.")
        sys.exit(1)

    # Read input files
    paper_text = read_pdf(pdf_path)
    figure_desc = read_description(desc_path)
    full_figure_desc = read_description(full_desc_path) if full_desc_path else None
    
    # Get figure number from filename
    figure_number = extract_figure_number(os.path.basename(desc_path))

    # Get contextual explanation
    explanation = get_contextual_explanation(paper_text, figure_desc, figure_number, full_figure_desc)

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
