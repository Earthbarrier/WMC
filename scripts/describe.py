import os
import sys
import base64
import anthropic
import mimetypes

def get_mime_type(file_path):
    """
    Get the MIME type of the file based on its extension.
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        # Default to jpeg if we can't determine the type
        mime_type = 'image/jpeg'
    return mime_type

def encode_image(image_path):
    """
    Encode an image file to base64.
    """
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Error encoding image: {e}")
        sys.exit(1)

def describe_image(image_path):
    """
    Send a scientific figure to Claude and get a comprehensive, technical description.
    """
    client = anthropic.Anthropic()
    base64_image = encode_image(image_path)
    mime_type = get_mime_type(image_path)
    
    prompt = """Please provide an extremely detailed analysis of this scientific figure, following this structured approach:

1. Figure Overview
- Identify the figure number and title if present
- Summarize what the figure is demonstrating
- Note how many subpanels/sections (labeled a, b, c, etc.) are present

2. For Each Panel/Section (going through a, b, c, etc.):
- Describe the type of representation (diagram, chart, schematic, etc.)
- List all labeled components and their relationships
- Detail any color coding or special notation used
- Explain any arrows, lines, or other connecting elements
- Note any numerical values, scales, or units
- Describe any genetic notation, molecular structures, or specialized symbols
- Capture any annotations or callouts

3. Technical Details
- Document all text labels verbatim
- Note any mathematical expressions or equations
- Describe any legends or keys
- Capture any measurement units or scales
- Detail any experimental conditions or parameters shown

4. Relationships and Processes
- Explain any sequential steps or processes shown
- Describe comparative relationships between elements
- Note any transformations or changes illustrated
- Explain any feedback loops or cyclic processes
- Detail any cause-and-effect relationships shown

5. Figure-Specific Elements
- For genetic diagrams: detail all alleles, chromosomes, and genetic elements
- For molecular diagrams: describe all molecular components and interactions
- For cellular diagrams: note all cellular structures and processes
- For graphs: specify axes, data points, and trends
- For schematics: explain all mechanical or systematic components

6. Caption and Annotations
- Include any figure captions verbatim
- Note any reference citations
- Include any additional annotations or notes

Please provide complete technical detail, maintaining scientific precision. Use exact terminology and capture all numerical values, labels, and relationships precisely. List every labeled element and describe all visual representations of data or processes."""

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": base64_image
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        return message.content[0].text
        
    except Exception as e:
        print(f"Error getting description from Claude: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Detailed error: {e.response.text}")
        sys.exit(1)

def save_description(description, output_path):
    """
    Save the description to a text file.
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(description)
        print(f"\nDescription saved to: {output_path}")
    except Exception as e:
        print(f"Error saving description to file: {e}")
        sys.exit(1)

def get_output_filename(image_path):
    """
    Generate output text filename based on input image path.
    """
    base_path = os.path.splitext(image_path)[0]
    return f"{base_path}_blind.txt"

def main():
    # Check if image path is provided
    if len(sys.argv) != 2:
        print("Usage: python script.py <path_to_image>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    # Check if file exists
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' does not exist.")
        sys.exit(1)
    
    # Get and print the description
    description = describe_image(image_path)
    output_path = get_output_filename(image_path)
    save_description(description, output_path)

if __name__ == "__main__":
    main()
