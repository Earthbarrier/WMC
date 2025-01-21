#!/bin/bash

# Directory containing your audio files
audio_dir="generated_audio/chunks"
output_dir="../../../../output_audio"
filename=$1
output_file="$output_dir/$filename.mp3"
filelist="filelist.txt"

# Navigate to the directory
cd "$audio_dir"

# Generate the file list
> "$filelist" # Clear or create filelist.txt
for file in chunk_*.mp3; do
  echo "file '$file'" >> "$filelist"
done

# Ensure the output directory exists
mkdir -p "$output_dir"

# Use ffmpeg to concatenate the files
ffmpeg -f concat -safe 0 -i "$filelist" -c copy "$output_file"

# Cleanup
#rm "$filelist"

echo "All files concatenated into $output_file"
