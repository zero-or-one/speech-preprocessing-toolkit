import os
import re
import argparse
import csv
import json
from pathlib import Path
import librosa
import soundfile as sf
from typing import List, Tuple, Optional, Dict

class TextGridProcessor:
    def __init__(self, textgrid_dir: str, wav_dir: str, output_dir: str, 
                 delete_originals: bool = False, min_duration: float = 0.5, 
                 max_filename_length: int = 50, verbose: bool = False,
                 save_manifest: bool = True, manifest_format: str = 'csv'):
        """
        Initialize the TextGrid processor.
        
        Args:
            textgrid_dir: Directory containing .TextGrid files
            wav_dir: Directory containing corresponding .wav files
            output_dir: Directory to save split audio files
            delete_originals: Whether to delete original files after processing
            min_duration: Minimum duration for audio segments in seconds
            max_filename_length: Maximum length for text part of filename
            verbose: Enable verbose output
            save_manifest: Whether to save a manifest file with paths and transcriptions
            manifest_format: Format for manifest file ('csv' or 'json')
        """
        self.textgrid_dir = Path(textgrid_dir)
        self.wav_dir = Path(wav_dir)
        self.output_dir = Path(output_dir)
        self.delete_originals = delete_originals
        self.min_duration = min_duration
        self.max_filename_length = max_filename_length
        self.verbose = verbose
        self.save_manifest = save_manifest
        self.manifest_format = manifest_format
        self.output_dir.mkdir(exist_ok=True)
        
        # Store all processed segments for manifest
        self.processed_segments = []
        
        # Patterns to identify non-speech segments
        self.noise_patterns = [
            r'<NOISE>',
            r'<IVER>',
            r'<VOCNOISE>',
            r'<LAUGH.*?>',
            r'<SIL>',
            r'<UNKNOWN>',
            r'<PRIVATE\.INFO>',
            r'^\s*$',  # Empty or whitespace-only text
        ]
        
    def is_clean_text(self, text: str) -> bool:
        """
        Check if the text is clean speech (no noise, laughter, etc.)
        
        Args:
            text: Text to check
            
        Returns:
            True if text is clean speech, False otherwise
        """
        text = text.strip()
        
        # Check against noise patterns
        for pattern in self.noise_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False
                
        # Must have actual content (not just punctuation or symbols)
        if len(text) < 2:
            return False
            
        return True
    
    def parse_textgrid_item4(self, textgrid_path: str) -> List[Tuple[float, float, str]]:
        """
        Parse TextGrid file and extract intervals from item[4].
        
        Args:
            textgrid_path: Path to the TextGrid file
            
        Returns:
            List of tuples (start_time, end_time, text)
        """
        intervals = []
        
        try:
            # Try different encodings
            encodings_to_try = ['utf-8', 'utf-16', 'utf-16-le', 'utf-16-be', 'latin-1', 'cp1252']
            content = None
            
            for encoding in encodings_to_try:
                try:
                    with open(textgrid_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    if self.verbose:
                        print(f"Successfully read file with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                print(f"Error: Could not decode {textgrid_path} with any supported encoding")
                return intervals
            
            # Find item[4] section
            item4_pattern = r'item \[4\]:(.*?)(?=item \[\d+\]:|$)'
            item4_match = re.search(item4_pattern, content, re.DOTALL)
            
            if not item4_match:
                if self.verbose:
                    print(f"Warning: item[4] not found in {textgrid_path}")
                return intervals
                
            item4_content = item4_match.group(1)
            
            # Extract intervals
            interval_pattern = r'intervals \[(\d+)\]:\s*xmin = ([\d.]+)\s*xmax = ([\d.]+)\s*text = "([^"]*)"'
            matches = re.findall(interval_pattern, item4_content, re.DOTALL)
            
            for match in matches:
                interval_num, xmin, xmax, text = match
                start_time = float(xmin)
                end_time = float(xmax)
                
                # Only include clean text intervals
                if self.is_clean_text(text):
                    intervals.append((start_time, end_time, text.strip()))
                    
        except Exception as e:
            print(f"Error parsing {textgrid_path}: {e}")
            
        return intervals
    
    def split_audio(self, wav_path: str, intervals: List[Tuple[float, float, str]], 
                   base_filename: str, original_textgrid: str, original_wav: str) -> bool:
        """
        Split audio file based on intervals.
        
        Args:
            wav_path: Path to the WAV file
            intervals: List of (start_time, end_time, text) tuples
            base_filename: Base name for output files
            original_textgrid: Path to original TextGrid file
            original_wav: Path to original WAV file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load audio file
            audio, sr = librosa.load(wav_path, sr=None)
            
            # Create output subdirectory for this file
            file_output_dir = self.output_dir / base_filename
            file_output_dir.mkdir(exist_ok=True)
            
            segments_saved = 0
            
            # Process each interval
            for i, (start_time, end_time, text) in enumerate(intervals):
                # Convert time to samples
                start_sample = int(start_time * sr)
                end_sample = int(end_time * sr)
                
                # Extract audio segment
                segment = audio[start_sample:end_sample]
                
                # Skip very short segments
                duration = len(segment) / sr
                if duration < self.min_duration:
                    if self.verbose:
                        print(f"Skipping short segment ({duration:.2f}s): '{text}'")
                    continue
                
                # Create safe filename
                safe_text = re.sub(r'[^\w\s-]', '', text)[:self.max_filename_length]
                safe_text = re.sub(r'\s+', '_', safe_text)
                
                output_filename = f"{base_filename}_{i:03d}.wav"
                output_path = file_output_dir / output_filename
                
                # Save audio segment
                sf.write(output_path, segment, sr)
                segments_saved += 1
                
                # Store segment info for manifest
                if self.save_manifest:
                    segment_info = {
                        'audio_path': str(output_path.resolve()),
                        'relative_path': str(output_path.relative_to(self.output_dir)),
                        'transcription': text,
                        'duration': round(duration, 3),
                        'start_time': round(start_time, 3),
                        'end_time': round(end_time, 3),
                        'original_textgrid': original_textgrid,
                        'original_wav': original_wav,
                        'base_filename': base_filename,
                        'segment_index': i,
                        'sample_rate': sr
                    }
                    self.processed_segments.append(segment_info)
                
                if self.verbose:
                    print(f"Saved: {output_filename} ({duration:.2f}s) - '{text}'")
                else:
                    print(f"Saved: {output_filename}")
            
            print(f"Successfully saved {segments_saved} audio segments from {base_filename}")
            return True
                
        except Exception as e:
            print(f"Error processing audio {wav_path}: {e}")
            return False
    
    def save_manifest_file(self) -> None:
        """
        Save manifest file with all processed segments information.
        """
        if not self.processed_segments:
            return
            
        if self.manifest_format.lower() == 'csv':
            manifest_path = self.output_dir / 'manifest.csv'
            
            with open(manifest_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'audio_path', 'relative_path', 'transcription', 'duration', 
                    'start_time', 'end_time', 'original_textgrid', 'original_wav',
                    'base_filename', 'segment_index', 'sample_rate'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.processed_segments)
                
        elif self.manifest_format.lower() == 'json':
            manifest_path = self.output_dir / 'manifest.json'
            
            manifest_data = {
                'metadata': {
                    'total_segments': len(self.processed_segments),
                    'total_duration': sum(seg['duration'] for seg in self.processed_segments),
                    'textgrid_dir': str(self.textgrid_dir.resolve()),
                    'wav_dir': str(self.wav_dir.resolve()),
                    'output_dir': str(self.output_dir.resolve()),
                    'min_duration': self.min_duration,
                    'processing_settings': {
                        'delete_originals': self.delete_originals,
                        'max_filename_length': self.max_filename_length,
                        'min_duration': self.min_duration
                    }
                },
                'segments': self.processed_segments
            }
            
            with open(manifest_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(manifest_data, jsonfile, indent=2, ensure_ascii=False)
        
        print(f"📄 Manifest saved: {manifest_path}")
        print(f"   Total segments: {len(self.processed_segments)}")
        print(f"   Total duration: {sum(seg['duration'] for seg in self.processed_segments):.2f} seconds")

    def process_all_files(self) -> int:
        """
        Process all TextGrid files in the directory.
        
        Returns:
            Number of successfully processed file pairs
        """
        textgrid_files = list(self.textgrid_dir.glob("*.TextGrid"))
        
        if not textgrid_files:
            print(f"No .TextGrid files found in {self.textgrid_dir}")
            return 0
            
        print(f"Found {len(textgrid_files)} TextGrid files")
        
        processed_files = []  # Track successfully processed files
        
        for textgrid_path in textgrid_files:
            base_name = textgrid_path.stem
            
            # Look for corresponding WAV file
            wav_path = self.wav_dir / f"{base_name}.wav"
            
            if not wav_path.exists():
                print(f"Warning: No corresponding WAV file found for {textgrid_path.name}")
                continue
                
            print(f"\nProcessing: {textgrid_path.name}")
            
            # Parse TextGrid file
            intervals = self.parse_textgrid_item4(str(textgrid_path))
            
            if not intervals:
                print(f"No clean intervals found in {textgrid_path.name}")
                continue
                
            print(f"Found {len(intervals)} clean speech intervals")
            
            # Split audio
            success = self.split_audio(str(wav_path), intervals, base_name, 
                                     str(textgrid_path.resolve()), str(wav_path.resolve()))
            
            if success:
                processed_files.append((textgrid_path, wav_path))
        
        # Delete original files if requested and processing was successful
        if self.delete_originals and processed_files:
            print(f"\nDeleting original files...")
            deleted_count = 0
            for textgrid_path, wav_path in processed_files:
                try:
                    textgrid_path.unlink()
                    wav_path.unlink()
                    deleted_count += 1
                    print(f"Deleted: {textgrid_path.name} and {wav_path.name}")
                except Exception as e:
                    print(f"Error deleting {textgrid_path.name}: {e}")
            
            print(f"Successfully deleted {deleted_count} pairs of original files")
        
        print(f"\nProcessing complete. Output saved to: {self.output_dir}")
        print(f"Successfully processed {len(processed_files)} file pairs")
        
        # Save manifest file
        if self.save_manifest and self.processed_segments:
            self.save_manifest_file()
        
        return len(processed_files)

def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Split audio files based on clean speech intervals from TextGrid files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -t ./textgrids -w ./audio -o ./split_audio
  %(prog)s -t /path/to/textgrids -w /path/to/wavs -o /path/to/output --delete-originals
  %(prog)s --textgrid-dir ./data/textgrids --wav-dir ./data/audio --output-dir ./output --verbose

Required dependencies:
  pip install librosa soundfile
        """
    )
    
    parser.add_argument(
        '-t', '--textgrid-dir',
        type=str,
        required=True,
        help='Directory containing .TextGrid files'
    )
    
    parser.add_argument(
        '-w', '--wav-dir',
        type=str,
        required=True,
        help='Directory containing corresponding .wav files'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        type=str,
        required=True,
        help='Directory to save split audio files'
    )
    
    parser.add_argument(
        '--delete-originals',
        action='store_true',
        help='Delete original TextGrid and WAV files after successful processing'
    )
    
    parser.add_argument(
        '--min-duration',
        type=float,
        default=0.5,
        help='Minimum duration (in seconds) for audio segments (default: 0.5)'
    )
    
    parser.add_argument(
        '--max-filename-length',
        type=int,
        default=50,
        help='Maximum length for text part of filename (default: 50)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--no-manifest',
        action='store_true',
        help='Do not save manifest file with paths and transcriptions'
    )
    
    parser.add_argument(
        '--manifest-format',
        type=str,
        choices=['csv', 'json'],
        default='csv',
        help='Format for manifest file (default: csv)'
    )
    
    return parser.parse_args()

def main():
    """
    Main function to run the TextGrid audio splitter.
    """
    args = parse_arguments()
    
    # Validate directories
    if not os.path.exists(args.textgrid_dir):
        print(f"Error: TextGrid directory does not exist: {args.textgrid_dir}")
        return 1
        
    if not os.path.exists(args.wav_dir):
        print(f"Error: WAV directory does not exist: {args.wav_dir}")
        return 1
    
    # Print configuration
    print("TextGrid Audio Splitter")
    print("======================")
    print(f"TextGrid directory: {args.textgrid_dir}")
    print(f"WAV directory: {args.wav_dir}")
    print(f"Output directory: {args.output_dir}")
    print(f"Delete originals: {args.delete_originals}")
    print(f"Minimum duration: {args.min_duration}s")
    print(f"Max filename length: {args.max_filename_length}")
    print(f"Verbose output: {args.verbose}")
    print(f"Save manifest: {not args.no_manifest}")
    if not args.no_manifest:
        print(f"Manifest format: {args.manifest_format}")
    print()
    
    # Safety confirmation for file deletion
    if args.delete_originals:
        print("⚠️  WARNING: Original files will be deleted after processing!")
        confirm = input("Continue? (y/N): ")
        if confirm.lower() not in ['y', 'yes']:
            print("Operation cancelled.")
            return 1
        print()
    
    # Create processor and run
    processor = TextGridProcessor(
        textgrid_dir=args.textgrid_dir,
        wav_dir=args.wav_dir,
        output_dir=args.output_dir,
        delete_originals=args.delete_originals,
        min_duration=args.min_duration,
        max_filename_length=args.max_filename_length,
        verbose=args.verbose,
        save_manifest=not args.no_manifest,
        manifest_format=args.manifest_format
    )
    
    try:
        processed_count = processor.process_all_files()
        
        if processed_count > 0:
            print(f"\n✅ Success! Processed {processed_count} file pairs.")
            return 0
        else:
            print(f"\n❌ No files were successfully processed.")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n⏹️  Operation cancelled by user.")
        return 1
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())