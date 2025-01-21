import os
import sys
import anthropic
import PyPDF2
import re

def sanitize_filename(filename):
    """Sanitize a string to make it safe for filenames."""
    # Replace invalid characters with an underscore or remove them
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

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

def get_paper_name(paper_text):
    """Get paper name prediction from Claude."""
    client = anthropic.Anthropic()
    
    prompt = """You are helping to extract the exact title of a scientific paper. 
    Here are the first 1000 characters of the paper. The title is typically found at the beginning.
    
    Important instructions:
    - Look for text that appears to be the main title (usually at the start, often in larger font in the original)
    - Only return the complete, exact title as it appears in the text
    - Do not generate or predict a title - only extract the existing title
    - If you can't find a clear title, respond with "TITLE NOT FOUND"
    - Do not include any other text, explanations, or formatting
    
    Paper text:
    {paper_text}
    """
    
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[
                {
                    "role": "user", 
                    "content": prompt.format(paper_text=paper_text[:1000])
                }
            ]
        )
        return message.content[0].text
    except Exception as e:
        print(f"Error getting paper name from Claude: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Detailed error: {e.response.text}")
        sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: python predict_title.py <path_to_paper.pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file '{pdf_path}' does not exist.")
        sys.exit(1)

    # Read PDF and get first 1000 chars
    paper_text = read_pdf(pdf_path)
    truncated_text = paper_text[:1000]

    # Get predicted paper name
    paper_name = get_paper_name(truncated_text)

    # Sanitize the paper name for safe usage as a filename
    safe_paper_name = sanitize_filename(paper_name)

    # Print sanitized result
    print(safe_paper_name)

if __name__ == "__main__":
    main()
