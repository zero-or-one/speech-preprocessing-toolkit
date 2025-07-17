import re
import json
import csv
import argparse
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional

class TranscriptionNormalizer:
    """A class to normalize transcription files in various formats."""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the normalizer with optional configuration.
        
        Args:
            config: Dictionary with normalization settings
        """
        self.config = config or {}
        self.setup_patterns()
    
    def setup_patterns(self):
        """Setup regex patterns for normalization."""
        # Pattern for extracting written numbers from (number)/(written_number)
        self.number_pattern = re.compile(r'\(.*?\)\/\((.*?)\)')
        
        # Pattern for replacing number options with written numbers
        self.number_replacement_pattern = re.compile(r'\(.*?\)\/\((.*?)\)')
        
        # Pattern for removing markers (customizable)
        marker_chars = self.config.get('marker_chars', 'blnourw')
        self.marker_pattern = re.compile(f'[{marker_chars}]/', re.IGNORECASE)
        
        # Pattern for removing special characters
        special_chars = self.config.get('special_chars', r'[\/*\+]')
        self.special_char_pattern = re.compile(special_chars)
        
        # Pattern for normalizing multiple spaces
        self.multiple_space_pattern = re.compile(r' +')
        
        # Pattern for file extension replacement
        self.extension_replacements = self.config.get('extension_replacements', {
            '.pcm': '.wav',
            '.raw': '.wav'
        })
    
    def extract_written_number(self, text: str) -> str:
        """
        Extract the number in written form from (number)/(written_number) pattern.
        
        Args:
            text: Input text
            
        Returns:
            Extracted written number or original text if no match
        """
        match = self.number_pattern.search(text)
        return match.group(1) if match else text
    
    def normalize_file_extensions(self, file_part: str) -> str:
        """
        Normalize file extensions according to configuration.
        
        Args:
            file_part: File path/name part
            
        Returns:
            Normalized file path/name
        """
        for old_ext, new_ext in self.extension_replacements.items():
            if file_part.endswith(old_ext):
                file_part = file_part.replace(old_ext, new_ext)
        return file_part
    
    def normalize_transcription_text(self, transcription: str) -> str:
        """
        Normalize transcription text by applying various cleanup rules.
        
        Args:
            transcription: Raw transcription text
            
        Returns:
            Normalized transcription text
        """
        # Replace number options with written numbers
        while self.number_replacement_pattern.search(transcription):
            transcription = self.number_replacement_pattern.sub(r'\1', transcription)
        
        # Remove markers (b/, l/, o/, n/, etc.)
        transcription = self.marker_pattern.sub('', transcription)
        
        # Remove special characters (/, *, +)
        transcription = self.special_char_pattern.sub('', transcription)
        
        # Replace multiple spaces with single space
        transcription = self.multiple_space_pattern.sub(' ', transcription)
        
        # Additional custom normalizations
        if 'custom_replacements' in self.config:
            for old, new in self.config['custom_replacements'].items():
                transcription = transcription.replace(old, new)
        
        return transcription.strip()
    
    def parse_line(self, line: str, separator: str = '::') -> Tuple[str, str]:
        """
        Parse a line into file part and transcription part.
        
        Args:
            line: Input line
            separator: Separator between file and transcription
            
        Returns:
            Tuple of (file_part, transcription_part)
        """
        if separator in line:
            parts = line.split(separator, 1)
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()
        
        # Fallback: try other common separators
        for sep in ['::', ':', '\t', '|']:
            if sep in line and sep != separator:
                parts = line.split(sep, 1)
                if len(parts) == 2:
                    return parts[0].strip(), parts[1].strip()
        
        # If no separator found, assume entire line is transcription
        return '', line.strip()
    
    def normalize_single_entry(self, file_part: str, transcription_part: str, 
                             separator: str = '::') -> str:
        """
        Normalize a single transcription entry.
        
        Args:
            file_part: File path/name
            transcription_part: Transcription text
            separator: Separator to use in output
            
        Returns:
            Normalized entry
        """
        # Normalize file extensions
        if file_part:
            file_part = self.normalize_file_extensions(file_part)
        
        # Normalize transcription text
        transcription_part = self.normalize_transcription_text(transcription_part)
        
        # Combine back
        if file_part:
            return f"{file_part} {separator} {transcription_part}"
        else:
            return transcription_part
    
    def normalize_txt_file(self, input_file: str, output_file: str, 
                          separator: str = '::') -> None:
        """
        Normalize a text file with transcriptions.
        
        Args:
            input_file: Input file path
            output_file: Output file path
            separator: Separator between file and transcription
        """
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            normalized_lines = []
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                
                try:
                    file_part, transcription_part = self.parse_line(line, separator)
                    normalized_line = self.normalize_single_entry(
                        file_part, transcription_part, separator
                    )
                    normalized_lines.append(normalized_line)
                except Exception as e:
                    print(f"Warning: Error processing line {i}: {e}")
                    continue
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(normalized_lines))
            
        except Exception as e:
            raise Exception(f"Error processing text file {input_file}: {e}")
    
    def normalize_json_file(self, input_file: str, output_file: str) -> None:
        """
        Normalize a JSON file with transcriptions.
        
        Args:
            input_file: Input file path
            output_file: Output file path
        """
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            def normalize_json_entry(entry):
                if isinstance(entry, dict):
                    normalized_entry = {}
                    for key, value in entry.items():
                        if key.lower() in ['file', 'filename', 'audio', 'path']:
                            normalized_entry[key] = self.normalize_file_extensions(str(value))
                        elif key.lower() in ['transcription', 'text', 'transcript']:
                            normalized_entry[key] = self.normalize_transcription_text(str(value))
                        else:
                            normalized_entry[key] = value
                    return normalized_entry
                elif isinstance(entry, str):
                    # Assume it's a line with separator
                    file_part, transcription_part = self.parse_line(entry)
                    return self.normalize_single_entry(file_part, transcription_part)
                else:
                    return entry
            
            if isinstance(data, list):
                normalized_data = [normalize_json_entry(entry) for entry in data]
            elif isinstance(data, dict):
                normalized_data = normalize_json_entry(data)
            else:
                normalized_data = data
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(normalized_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            raise Exception(f"Error processing JSON file {input_file}: {e}")
    
    def normalize_csv_file(self, input_file: str, output_file: str) -> None:
        """
        Normalize a CSV file with transcriptions.
        
        Args:
            input_file: Input file path
            output_file: Output file path
        """
        try:
            with open(input_file, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                
                rows = []
                for row in reader:
                    normalized_row = {}
                    for key, value in row.items():
                        if key and value:
                            if key.lower() in ['file', 'filename', 'audio', 'path']:
                                normalized_row[key] = self.normalize_file_extensions(str(value))
                            elif key.lower() in ['transcription', 'text', 'transcript']:
                                normalized_row[key] = self.normalize_transcription_text(str(value))
                            else:
                                normalized_row[key] = value
                        else:
                            normalized_row[key] = value
                    rows.append(normalized_row)
            
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
                
        except Exception as e:
            raise Exception(f"Error processing CSV file {input_file}: {e}")
    
    def normalize_file(self, input_file: str, output_file: Optional[str] = None, 
                      separator: str = '::') -> str:
        """
        Normalize a transcription file (auto-detects format).
        
        Args:
            input_file: Input file path
            output_file: Output file path (optional)
            separator: Separator for text files
            
        Returns:
            Output file path
        """
        input_path = Path(input_file)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        # Determine output file if not provided
        if output_file is None:
            output_file = str(input_path.parent / f"{input_path.stem}_normalized{input_path.suffix}")
        
        # Determine file format
        file_extension = input_path.suffix.lower()
        
        print(f"Normalizing: {input_file} -> {output_file}")
        
        if file_extension == '.txt':
            self.normalize_txt_file(input_file, output_file, separator)
        elif file_extension == '.json':
            self.normalize_json_file(input_file, output_file)
        elif file_extension == '.csv':
            self.normalize_csv_file(input_file, output_file)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
        
        print(f"Normalized transcription saved to: {output_file}")
        return output_file

def load_config_file(config_file: str) -> Dict:
    """Load configuration from a JSON file."""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Error loading config file {config_file}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Normalize transcription files')
    parser.add_argument('input_files', nargs='+', help='Input file(s) to normalize')
    parser.add_argument('-o', '--output', help='Output file (for single input file)')
    parser.add_argument('-s', '--separator', default='::',
                       help='Separator between file and transcription (default: ::)')
    parser.add_argument('-c', '--config', help='Configuration file (JSON)')
    parser.add_argument('--suffix', default='_normalized',
                       help='Suffix for output files when processing multiple files')
    parser.add_argument('--recursive', action='store_true',
                       help='Process files recursively in directories')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be processed without actually doing it')
    
    args = parser.parse_args()
    
    # Load configuration
    config = {}
    if args.config:
        config = load_config_file(args.config)
    
    # Initialize normalizer
    normalizer = TranscriptionNormalizer(config)
    
    # Collect files to process
    files_to_process = []
    
    for input_path in args.input_files:
        path = Path(input_path)
        
        if path.is_file():
            files_to_process.append(str(path))
        elif path.is_dir() and args.recursive:
            # Find supported files recursively
            for ext in ['.txt', '.json', '.csv']:
                files_to_process.extend([str(f) for f in path.rglob(f'*{ext}')])
        elif path.is_dir():
            # Find supported files in directory only
            for ext in ['.txt', '.json', '.csv']:
                files_to_process.extend([str(f) for f in path.glob(f'*{ext}')])
        else:
            print(f"Warning: {input_path} not found or not a supported file")
    
    if not files_to_process:
        print("No files to process")
        return 1
    
    # Process files
    processed_count = 0
    error_count = 0
    
    for input_file in files_to_process:
        try:
            if args.dry_run:
                print(f"Would process: {input_file}")
                continue
            
            # Determine output file
            if len(files_to_process) == 1 and args.output:
                output_file = args.output
            else:
                input_path = Path(input_file)
                output_file = str(input_path.parent / f"{input_path.stem}{args.suffix}{input_path.suffix}")
            
            normalizer.normalize_file(input_file, output_file, args.separator)
            processed_count += 1
            
        except Exception as e:
            print(f"Error processing {input_file}: {e}")
            error_count += 1
    
    if not args.dry_run:
        print(f"\nProcessing complete!")
        print(f"Successfully processed: {processed_count} files")
        print(f"Errors encountered: {error_count} files")
    
    return 0 if error_count == 0 else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())