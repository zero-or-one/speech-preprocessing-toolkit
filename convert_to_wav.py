import os
import numpy as np
import soundfile as sf
from pathlib import Path
import argparse

def convert_pcm_to_wav(pcm_path, output_path, sample_rate=16000):
    """
    Convert a single PCM file to WAV format.
    
    :param pcm_path: Path to the PCM file
    :param output_path: Path for the output WAV file
    :param sample_rate: Sample rate for the PCM data (default 16000 Hz)
    """
    try:
        # Read the PCM file (16-bit PCM)
        with open(pcm_path, 'rb') as pcm_file:
            file_content = pcm_file.read()
            
            # Ensure file size is a multiple of 2 (16-bit)
            if len(file_content) % 2 != 0:
                file_content = file_content[:-1]
            
            # Convert to numpy array
            pcm_data = np.frombuffer(file_content, dtype=np.int16)
        
        # Normalize the audio data
        audio = pcm_data.astype(np.float32) / 32768.0
        
        # Save as WAV file
        sf.write(output_path, audio, sample_rate)
        
        return True
    except Exception as e:
        print(f"Error converting PCM {pcm_path}: {e}")
        return False

def convert_audio_file(input_path, output_path):
    """
    Convert various audio formats to WAV using soundfile.
    
    :param input_path: Path to the input audio file
    :param output_path: Path for the output WAV file
    """
    try:
        # Read the audio file
        audio_data, sample_rate = sf.read(input_path)
        
        # Save as WAV file
        sf.write(output_path, audio_data, sample_rate)
        
        return True
    except Exception as e:
        print(f"Error converting {input_path}: {e}")
        return False

def convert_all_to_wav(input_dir, delete_original=False, recursive=True):
    """
    Convert all supported audio files in a directory to WAV format.
    
    :param input_dir: Directory containing audio files
    :param delete_original: If True, delete original files after conversion
    :param recursive: If True, search subdirectories recursively
    """
    # Supported audio formats
    supported_formats = {
        '.pcm': 'pcm',
        '.mp3': 'audio',
        '.flac': 'audio',
        '.ogg': 'audio',
        '.m4a': 'audio',
        '.aac': 'audio',
        '.wma': 'audio',
        '.aiff': 'audio',
        '.au': 'audio',
        '.raw': 'audio'
    }
    
    # Ensure the input directory exists
    if not os.path.isdir(input_dir):
        print(f"Error: {input_dir} is not a valid directory.")
        return
    
    conversion_count = 0
    error_count = 0
    
    # Use os.walk for recursive or just listdir for non-recursive
    if recursive:
        file_iterator = os.walk(input_dir)
    else:
        file_iterator = [(input_dir, [], os.listdir(input_dir))]
    
    for dirpath, dirnames, filenames in file_iterator:
        for filename in filenames:
            file_ext = Path(filename).suffix.lower()
            
            # Check if the file is a supported audio format
            if file_ext in supported_formats:
                input_path = os.path.join(dirpath, filename)
                output_filename = os.path.splitext(filename)[0] + '.wav'
                output_path = os.path.join(dirpath, output_filename)
                
                # Skip if output file already exists
                if os.path.exists(output_path):
                    print(f"Skipping {filename} - WAV file already exists")
                    continue
                
                print(f"Converting: {filename}")
                
                # Handle different file types
                if file_ext == '.pcm':
                    success = convert_pcm_to_wav(input_path, output_path)
                else:
                    success = convert_audio_file(input_path, output_path)
                
                if success:
                    conversion_count += 1
                    print(f"  ✓ Converted to: {output_filename}")
                    
                    # Delete original file if specified
                    if delete_original:
                        try:
                            os.remove(input_path)
                            print(f"  ✓ Deleted original file: {filename}")
                        except Exception as e:
                            print(f"  ✗ Error deleting {filename}: {e}")
                else:
                    error_count += 1
                    # Log the error
                    with open('conversion_errors.log', 'a') as log_file:
                        log_file.write(f"Error converting {filename} in {dirpath}\n")
    
    print(f"\nConversion complete!")
    print(f"Successfully converted: {conversion_count} files")
    print(f"Errors encountered: {error_count} files")
    if error_count > 0:
        print("Check conversion_errors.log for details")

def main():
    parser = argparse.ArgumentParser(description='Convert audio files to WAV format')
    parser.add_argument('input_dir', help='Input directory containing audio files')
    parser.add_argument('--delete-original', action='store_true', 
                       help='Delete original files after conversion')
    parser.add_argument('--no-recursive', action='store_true', 
                       help='Do not search subdirectories recursively')
    
    args = parser.parse_args()
    
    convert_all_to_wav(
        args.input_dir, 
        delete_original=args.delete_original,
        recursive=not args.no_recursive
    )

if __name__ == '__main__':
    main()