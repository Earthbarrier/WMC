import os
import sys
import re
import anthropic
import logging
from pathlib import Path
import pdfplumber
from pytesseract import image_to_string
from PIL import Image
import time
import textwrap

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class PaperCleaner:
    def __init__(self):
        self.client = anthropic.Anthropic()
        
    def clean_paper(self, text: str) -> str:
        """Clean the paper text by removing metadata and formatting."""
        # First apply basic cleaning
        text = self._basic_cleanup(text)
        
        # Then use Claude for more sophisticated cleaning
        cleaned = self._process_with_claude(text)
        return cleaned
        
    def _basic_cleanup(self, text: str) -> str:
        """Apply basic text cleanup rules."""
        # Remove URLs and DOIs
        text = re.sub(r'https?://\S+|doi\.org/\S+|www\.\S+', '', text)
        
        # Remove headers, footers, page numbers
        text = re.sub(r'^.*?Scientific\s+Reports.*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
        
        # Remove submission dates
        text = re.sub(r'Received:.*?Published:.*?xxxx', '', text, flags=re.DOTALL)
        
        # Remove author affiliations
        text = re.sub(r'^\d+Department.*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'Correspondence.*$', '', text, flags=re.MULTILINE)
        
        # Remove citation numbers
        text = re.sub(r'\[\d+(?:[-–]\d+)?(?:,\s*\d+)*\]', '', text)
        text = re.sub(r'\d+,\d+', '', text)
        
        # Fix formatting
        text = re.sub(r'- ([a-z])', r'\1', text)  # Fix hyphenation
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = re.sub(r' +', ' ', text)  # Remove multiple spaces
        
        return text.strip()
        
    def _process_with_claude(self, text: str) -> str:
        """Use Claude to clean and format the text, handling text in chunks."""
        # Split text into chunks of roughly 4000 characters (leaving room for prompt)
        chunks = textwrap.wrap(text, 4000, break_long_words=False, break_on_hyphens=False)
        cleaned_chunks = []
        
        for chunk in chunks:
            prompt = f"""Clean this scientific text by removing metadata and formatting while preserving scientific content. Remove citations, references, headers, footers, page numbers, and formatting artifacts.  Maintain all technical details and data. Return ONLY the cleaned text with no additional commentary or metadata. 
            Additionally, please spell out the full words for any use of acronyms and please describe in spoken language any math equations or scientific notations to the best of your ability. This is for a listening audience via text-to-speech so the outputs must all be easily interpreted by a TTS engine. 
Again, please adhere to the original text. Do not mention this prompt. 

Scientific Text:

{chunk}. """
            try:
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=8192,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                if response and response.content:
                    if isinstance(response.content, list):
                        cleaned_text = response.content[0].text.strip()
                    else:
                        cleaned_text = response.content.strip()
                    
                    # Remove any added commentary
                    cleaned_text = re.sub(r'^Here\'s.*?:\n*', '', cleaned_text)
                    cleaned_chunks.append(cleaned_text)
                
                # Add small delay between API calls
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error cleaning text chunk: {e}")
                cleaned_chunks.append(chunk)
            
        return "\n\n".join(cleaned_chunks)
            
    def process_pdf(self, pdf_path: str) -> str:
        """Extract and clean text from a PDF file."""
        try:
            # Extract text from PDF
            raw_text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        raw_text += text + "\n"
            
            # Clean the extracted text
            cleaned_text = self.clean_paper(raw_text)
            return cleaned_text
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            raise

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <path_to_paper.pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"Error: File '{pdf_path}' not found.")
        sys.exit(1)

    try:
        cleaner = PaperCleaner()
        logger.info("Processing PDF...")
        cleaned_text = cleaner.process_pdf(pdf_path)
        
        # Save cleaned text
        output_path = Path(pdf_path).with_suffix('.txt')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_text)
            
        logger.info(f"Cleaned text saved to: {output_path}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
