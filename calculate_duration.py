import os
import wave
import json
import csv
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from tqdm import tqdm
import statistics

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False
    print("Warning: soundfile not available. Only WAV files will be supported.")

class DatasetDurationCalculator:
    """A class to calculate duration statistics for audio datasets."""
    
    def __init__(self, audio_base_dir: str, supported_formats: Optional[List[str]] = None):
        """
        Initialize the calculator.
        
        Args:
            audio_base_dir: Base directory containing audio files
            supported_formats: List of supported audio formats
        """
        self.audio_base_dir = Path(audio_base_dir)
        
        if supported_formats is None:
            if SOUNDFILE_AVAILABLE:
                self.supported_formats = ['.wav', '.flac', '.mp3', '.ogg', '.m4a', '.aac']
            else:
                self.supported_formats = ['.wav']
        else:
            self.supported_formats = [fmt.lower() if fmt.startswith('.') else f'.{fmt.lower()}' 
                                    for fmt in supported_formats]
    
    def get_audio_duration(self, file_path: str) -> Optional[float]:
        """
        Get duration of an audio file.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Duration in seconds or None if error
        """
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.wav':
                # Use wave module for WAV files
                with wave.open(file_path, 'rb') as wav_file:
                    n_frames = wav_file.getnframes()
                    framerate = wav_file.getframerate()
                    return n_frames / float(framerate)
            
            elif SOUNDFILE_AVAILABLE and file_ext in self.supported_formats:
                # Use soundfile for other formats
                info = sf.info(file_path)
                return info.duration
            
            else:
                return None
                
        except Exception as e:
            return None
    
    def parse_transcription_line(self, line: str, separator: str = '::') -> Optional[str]:
        """
        Parse a transcription line to extract the file path.
        
        Args:
            line: Line from transcription file
            separator: Separator between file and transcription
            
        Returns:
            File path or None if not found
        """
        line = line.strip()
        if not line:
            return None
        
        # Try the specified separator first
        if separator in line:
            return line.split(separator)[0].strip()
        
        # Try common separators
        for sep in ['::', ':', '\t', '|']:
            if sep in line:
                return line.split(sep)[0].strip()
        
        # If no separator found, assume the entire line is a file path
        return line
    
    def find_audio_file(self, file_path: str) -> Optional[str]:
        """
        Find the actual audio file, checking different extensions if needed.
        
        Args:
            file_path: Original file path from transcription
            
        Returns:
            Full path to existing audio file or None
        """
        # Try the original path first
        full_path = self.audio_base_dir / file_path
        if full_path.exists():
            return str(full_path)
        
        # Try different extensions
        base_path = full_path.with_suffix('')
        for ext in self.supported_formats:
            candidate_path = base_path.with_suffix(ext)
            if candidate_path.exists():
                return str(candidate_path)
        
        return None
    
    def calculate_from_txt_file(self, transcription_file: str, separator: str = '::') -> Dict:
        """
        Calculate duration from a text transcription file.
        
        Args:
            transcription_file: Path to transcription file
            separator: Separator between file and transcription
            
        Returns:
            Dictionary with duration statistics
        """
        with open(transcription_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        return self._process_file_list(lines, separator, 'text')
    
    def calculate_from_json_file(self, json_file: str) -> Dict:
        """
        Calculate duration from a JSON file.
        
        Args:
            json_file: Path to JSON file
            
        Returns:
            Dictionary with duration statistics
        """
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        file_entries = []
        if isinstance(data, list):
            file_entries = data
        elif isinstance(data, dict) and 'data' in data:
            file_entries = data['data']
        else:
            file_entries = [data]
        
        return self._process_file_list(file_entries, None, 'json')
    
    def calculate_from_csv_file(self, csv_file: str) -> Dict:
        """
        Calculate duration from a CSV file.
        
        Args:
            csv_file: Path to CSV file
            
        Returns:
            Dictionary with duration statistics
        """
        with open(csv_file, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            file_entries = list(reader)
        
        return self._process_file_list(file_entries, None, 'csv')
    
    def _extract_file_path_from_entry(self, entry, entry_type: str) -> Optional[str]:
        """Extract file path from different entry types."""
        if entry_type == 'text':
            return entry.strip() if isinstance(entry, str) else None
        
        elif entry_type == 'json':
            if isinstance(entry, str):
                return entry
            elif isinstance(entry, dict):
                # Look for common file path keys
                for key in ['file', 'filename', 'audio', 'path', 'wav_file', 'audio_file']:
                    if key in entry:
                        return entry[key]
                # If no specific key found, try the first string value
                for value in entry.values():
                    if isinstance(value, str) and any(ext in value.lower() 
                                                   for ext in self.supported_formats):
                        return value
        
        elif entry_type == 'csv':
            if isinstance(entry, dict):
                # Look for common file path keys
                for key in ['file', 'filename', 'audio', 'path', 'wav_file', 'audio_file']:
                    if key in entry and entry[key]:
                        return entry[key]
                # Try first column that looks like a file path
                for value in entry.values():
                    if isinstance(value, str) and any(ext in value.lower() 
                                                   for ext in self.supported_formats):
                        return value
        
        return None
    
    def _process_file_list(self, entries: List, separator: Optional[str], 
                          entry_type: str) -> Dict:
        """
        Process a list of entries to calculate duration statistics.
        
        Args:
            entries: List of entries (lines, dicts, etc.)
            separator: Separator for text entries
            entry_type: Type of entries ('text', 'json', 'csv')
            
        Returns:
            Dictionary with duration statistics
        """
        total_duration = 0
        processed_files = 0
        error_files = []
        durations = []
        file_info = []
        
        for entry in tqdm(entries, desc="Processing files"):
            # Extract file path based on entry type
            if entry_type == 'text':
                file_path = self.parse_transcription_line(entry, separator or '::')
            else:
                file_path = self._extract_file_path_from_entry(entry, entry_type)
            
            if not file_path:
                continue
            
            # Find the actual audio file
            full_audio_path = self.find_audio_file(file_path)
            
            if not full_audio_path:
                error_files.append(f"File not found: {file_path}")
                continue
            
            # Get duration
            duration = self.get_audio_duration(full_audio_path)
            
            if duration is not None:
                total_duration += duration
                durations.append(duration)
                processed_files += 1
                file_info.append({
                    'path': file_path,
                    'full_path': full_audio_path,
                    'duration': duration
                })
            else:
                error_files.append(f"Could not process: {full_audio_path}")
        
        # Calculate statistics
        stats = self._calculate_statistics(total_duration, durations, processed_files, 
                                         error_files, file_info)
        
        return stats
    
    def _calculate_statistics(self, total_duration: float, durations: List[float], 
                            processed_files: int, error_files: List[str], 
                            file_info: List[Dict]) -> Dict:
        """Calculate comprehensive statistics."""
        # Format total duration
        hours = int(total_duration // 3600)
        minutes = int((total_duration % 3600) // 60)
        seconds = total_duration % 60
        
        stats = {
            'total_duration_seconds': total_duration,
            'total_duration_formatted': f"{hours:02d}:{minutes:02d}:{seconds:06.3f}",
            'total_files_processed': processed_files,
            'total_files_errors': len(error_files),
            'error_files': error_files,
            'file_details': file_info
        }
        
        # Add statistical measures if we have durations
        if durations:
            stats.update({
                'average_duration': statistics.mean(durations),
                'median_duration': statistics.median(durations),
                'min_duration': min(durations),
                'max_duration': max(durations),
                'std_deviation': statistics.stdev(durations) if len(durations) > 1 else 0
            })
            
            # Duration distribution
            stats['duration_distribution'] = {
                'under_1s': len([d for d in durations if d < 1]),
                '1s_to_5s': len([d for d in durations if 1 <= d < 5]),
                '5s_to_10s': len([d for d in durations if 5 <= d < 10]),
                '10s_to_30s': len([d for d in durations if 10 <= d < 30]),
                'over_30s': len([d for d in durations if d >= 30])
            }
        
        return stats
    
    def calculate_dataset_duration(self, input_file: str, separator: str = '::') -> Dict:
        """
        Calculate duration for any supported file format.
        
        Args:
            input_file: Path to input file
            separator: Separator for text files
            
        Returns:
            Dictionary with duration statistics
        """
        file_path = Path(input_file)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        file_ext = file_path.suffix.lower()
        
        if file_ext == '.txt':
            return self.calculate_from_txt_file(input_file, separator)
        elif file_ext == '.json':
            return self.calculate_from_json_file(input_file)
        elif file_ext == '.csv':
            return self.calculate_from_csv_file(input_file)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")

def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

def print_results(results: Dict, verbose: bool = False, output_file: Optional[str] = None):
    """Print formatted results."""
    output_lines = []
    
    output_lines.append("="*60)
    output_lines.append("DATASET DURATION ANALYSIS")
    output_lines.append("="*60)
    output_lines.append(f"Total Duration: {results['total_duration_formatted']}")
    output_lines.append(f"Total Files Processed: {results['total_files_processed']}")
    output_lines.append(f"Files with Errors: {results['total_files_errors']}")
    
    if 'average_duration' in results:
        output_lines.append("\nSTATISTICS:")
        output_lines.append(f"Average Duration: {format_duration(results['average_duration'])}")
        output_lines.append(f"Median Duration: {format_duration(results['median_duration'])}")
        output_lines.append(f"Min Duration: {format_duration(results['min_duration'])}")
        output_lines.append(f"Max Duration: {format_duration(results['max_duration'])}")
        output_lines.append(f"Standard Deviation: {results['std_deviation']:.3f}s")
        
        output_lines.append("\nDURATION DISTRIBUTION:")
        dist = results['duration_distribution']
        output_lines.append(f"Under 1s: {dist['under_1s']} files")
        output_lines.append(f"1s to 5s: {dist['1s_to_5s']} files")
        output_lines.append(f"5s to 10s: {dist['5s_to_10s']} files")
        output_lines.append(f"10s to 30s: {dist['10s_to_30s']} files")
        output_lines.append(f"Over 30s: {dist['over_30s']} files")
    
    if results['error_files']:
        output_lines.append("\nERROR FILES:")
        for error_file in results['error_files']:
            output_lines.append(f"  {error_file}")
    
    if verbose and results['file_details']:
        output_lines.append("\nFILE DETAILS:")
        for file_info in results['file_details'][:10]:  # Show first 10
            output_lines.append(f"  {file_info['path']}: {format_duration(file_info['duration'])}")
        if len(results['file_details']) > 10:
            output_lines.append(f"  ... and {len(results['file_details']) - 10} more files")
    
    # Print to console
    for line in output_lines:
        print(line)
    
    # Save to file if requested
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        print(f"\nResults saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Calculate total duration of audio dataset')
    parser.add_argument('transcription_file', help='Path to transcription file (.txt, .json, .csv)')
    parser.add_argument('audio_base_dir', help='Base directory containing audio files')
    parser.add_argument('-s', '--separator', default='::',
                       help='Separator between file and transcription for text files (default: ::)')
    parser.add_argument('-f', '--formats', nargs='+', 
                       default=['wav', 'flac', 'mp3', 'ogg', 'm4a', 'aac'],
                       help='Supported audio formats (default: wav flac mp3 ogg m4a aac)')
    parser.add_argument('-o', '--output', help='Save results to file')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show detailed file information')
    parser.add_argument('--json-output', help='Save detailed results as JSON')
    
    args = parser.parse_args()
    
    try:
        # Initialize calculator
        calculator = DatasetDurationCalculator(args.audio_base_dir, args.formats)
        
        # Calculate duration
        print(f"Analyzing dataset: {args.transcription_file}")
        print(f"Audio base directory: {args.audio_base_dir}")
        
        results = calculator.calculate_dataset_duration(args.transcription_file, args.separator)
        
        # Print results
        print_results(results, args.verbose, args.output)
        
        # Save JSON output if requested
        if args.json_output:
            with open(args.json_output, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
            print(f"Detailed results saved to: {args.json_output}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())