from pathlib import Path
from openai import OpenAI
import os
import argparse
import sys
import re

# OpenAI TTS has a limit of approximately 4096 tokens
# We'll use a conservative chunk size of around 1000 words
MAX_CHUNK_SIZE = 4000  # characters

def split_into_chunks(text, max_chunk_size=MAX_CHUNK_SIZE):
    """
    Split text into chunks at sentence boundaries, respecting the max chunk size
    """
    # Split into sentences (basic implementation)
    sentences = re.split('([.!?]+)', text)
    chunks = []
    current_chunk = ""
    
    # Reconstruct sentences and group them into chunks
    for i in range(0, len(sentences)-1, 2):
        sentence = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else '')
        if len(current_chunk) + len(sentence) <= max_chunk_size:
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def read_text_file(file_path):
    """Read text from a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        sys.exit(1)

def text_to_speech(input_text, output_filename="output.mp3", voice="alloy", model="tts-1-hd"):
    """
    Convert text to speech using OpenAI's API, handling long texts
    """
    try:
        client = OpenAI()
        output_path = Path("generated_audio")
        output_path.mkdir(exist_ok=True)

        # Split text into chunks
        chunks = split_into_chunks(input_text)
        print(f"Split text into {len(chunks)} chunks")

        # Create a directory for this specific output
        output_dir = output_path / Path(output_filename).stem
        output_dir.mkdir(exist_ok=True)

        # Process each chunk
        for i, chunk in enumerate(chunks):
            chunk_filename = output_dir / f"chunk_{i+1:03d}.mp3"
            print(f"Processing chunk {i+1}/{len(chunks)} ({len(chunk)} characters)...")
            
            try:
                response = client.audio.speech.create(
                    model=model,
                    voice=voice,
                    input=chunk
                )
                response.stream_to_file(str(chunk_filename))
                print(f"Saved chunk {i+1} to: {chunk_filename}")
            except Exception as e:
                print(f"Error processing chunk {i+1}: {str(e)}")
                raise

        # Instead of combining files, provide information about the generated files
        print("\nProcessing complete!")
        print(f"Audio files have been saved to: {output_dir}")
        print("\nGenerated files:")
        for file in sorted(output_dir.glob("*.mp3")):
            print(f"- {file.name}")
        
        # Provide command to combine files (if user wants to)
        print("\nTo combine these files using ffmpeg, you can run:")
        print(f"""cd generated_audio/final && echo -e "file 'chunk_001.mp3'\nfile 'chunk_002.mp3'\nfile 'chunk_003.mp3'\nfile 'chunk_004.mp3'\nfile 'chunk_005.mp3'\nfile 'chunk_006.mp3'" > filelist.txt && ffmpeg -f concat -safe 0 -i filelist.txt -c copy ../final.mp3""")
        
        return str(output_dir)

    except Exception as e:
        print(f"Error generating speech: {str(e)}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Convert text file to speech using OpenAI API')
    parser.add_argument('file', help='Path to the text file to convert')
    parser.add_argument('--voice', default='alloy', 
                      choices=['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'],
                      help='Voice to use for the speech (default: alloy)')
    parser.add_argument('--model', default='tts-1-hd',
                      choices=['tts-1', 'tts-1-hd'],
                      help='Model to use (tts-1 for speed, tts-1-hd for quality)')
    parser.add_argument('--output', '-o', default=None,
                      help='Output filename (default: input_filename.mp3)')

    args = parser.parse_args()
    input_path = Path(args.file)
    
    if args.output is None:
        args.output = f"{input_path.stem}.mp3"

    print(f"Reading text from: {input_path}")
    input_text = read_text_file(str(input_path))

    try:
        output_dir = text_to_speech(
            input_text=input_text,
            output_filename=args.output,
            voice=args.voice,
            model=args.model
        )
        print(f"\nAll audio chunks have been saved to: {output_dir}")
        
    except Exception as e:
        print(f"Failed to generate speech: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
