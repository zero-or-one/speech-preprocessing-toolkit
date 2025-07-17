#!/usr/bin/env python3
"""
Script to convert CSV or JSON file to JSON format with train/test/validation split.
Reads CSV or JSON with audio segments data including paths, transcriptions, timing, and metadata.
"""

import csv
import json
import argparse
import os
import random
from pathlib import Path
from collections import defaultdict


def load_data_from_file(input_file):
    """
    Load data from CSV or JSON file and convert to standard format.
    
    Args:
        input_file (str): Path to input file (CSV or JSON)
    
    Returns:
        list: List of data entries in dictionary format
    """
    file_extension = Path(input_file).suffix.lower()
    
    if file_extension == '.csv':
        return load_data_from_csv(input_file)
    elif file_extension == '.json':
        return load_data_from_json(input_file)
    else:
        raise ValueError(f"Unsupported file format: {file_extension}. Supported formats: .csv, .json")


def load_data_from_csv(input_file):
    """Load data from CSV file."""
    data = []
    with open(input_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row)
    return data


def load_data_from_json(input_file):
    """Load data from JSON file."""
    with open(input_file, 'r', encoding='utf-8') as jsonfile:
        data = json.load(jsonfile)
    
    # Handle different JSON formats
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        # If it's a single entry, wrap in list
        return [data]
    else:
        raise ValueError("JSON file must contain a list of objects or a single object")


def process_data_entry(row, audio_base_path="", use_relative_path=True, use_original_sampling_rate=True):
    """
    Process a single data entry and convert to standard JSON format.
    
    Args:
        row (dict): Data entry (from CSV or JSON)
        audio_base_path (str): Base path to prepend to audio file paths
        use_relative_path (bool): Whether to use relative_path instead of audio_path
        use_original_sampling_rate (bool): Whether to use sample_rate from data or default 16000
    
    Returns:
        dict: Processed JSON entry
    """
    # Handle different input formats - get audio path
    audio_path = row.get('audio_path', '')
    relative_path = row.get('relative_path', '')
    
    # If input is already in processed JSON format, extract path from audio object
    if not audio_path and not relative_path:
        if 'audio' in row and isinstance(row['audio'], dict):
            audio_path = row['audio'].get('path', '')
    
    # Extract other fields with fallbacks
    transcription = row.get('transcription', row.get('sentence', ''))
    duration = row.get('duration', '')
    start_time = row.get('start_time', '')
    end_time = row.get('end_time', '')
    base_filename = row.get('base_filename', row.get('speaker', ''))
    segment_index = row.get('segment_index', '')
    sample_rate = row.get('sample_rate', '')
    
    # If input is already processed JSON, extract from audio object
    if 'audio' in row and isinstance(row['audio'], dict):
        if not sample_rate:
            sample_rate = row['audio'].get('sampling_rate', '')
        if not duration:
            duration = row['audio'].get('duration', '')
    
    # Choose which path to use
    chosen_path = relative_path if (use_relative_path and relative_path) else audio_path
    
    # Create full audio path
    if audio_base_path:
        full_audio_path = os.path.join(audio_base_path, chosen_path)
    else:
        full_audio_path = chosen_path
    
    # Determine sampling rate
    if use_original_sampling_rate and sample_rate:
        try:
            sampling_rate = int(float(sample_rate))
        except (ValueError, TypeError):
            sampling_rate = 16000
    else:
        sampling_rate = 16000
    
    # Create speaker ID from base filename or existing speaker field
    speaker_id = base_filename
    
    # Create JSON entry
    json_entry = {
        "audio": {
            "path": full_audio_path,
            "sampling_rate": sampling_rate
        },
        "sentence": transcription,
        "speaker": speaker_id
    }
    
    return json_entry


def process_data_entry_with_metadata(row, audio_base_path="", use_relative_path=True, use_original_sampling_rate=True):
    """
    Process a single data entry and convert to JSON format with metadata.
    
    Args:
        row (dict): Data entry (from CSV or JSON)
        audio_base_path (str): Base path to prepend to audio file paths
        use_relative_path (bool): Whether to use relative_path instead of audio_path
        use_original_sampling_rate (bool): Whether to use sample_rate from data or default 16000
    
    Returns:
        dict: Processed JSON entry with metadata
    """
    # Handle different input formats
    audio_path = row.get('audio_path', '')
    relative_path = row.get('relative_path', '')
    
    # If input is already in processed JSON format, extract from audio object
    if not audio_path and not relative_path:
        if 'audio' in row and isinstance(row['audio'], dict):
            audio_path = row['audio'].get('path', '')
        # Try to get paths from metadata if available
        if 'metadata' in row and isinstance(row['metadata'], dict):
            if not audio_path:
                audio_path = row['metadata'].get('full_audio_path', '')
            if not relative_path:
                relative_path = row['metadata'].get('relative_path', '')
    
    # Extract other fields
    transcription = row.get('transcription', row.get('sentence', ''))
    duration = row.get('duration', '')
    start_time = row.get('start_time', '')
    end_time = row.get('end_time', '')
    original_textgrid = row.get('original_textgrid', '')
    original_wav = row.get('original_wav', '')
    base_filename = row.get('base_filename', row.get('speaker', ''))
    segment_index = row.get('segment_index', '')
    sample_rate = row.get('sample_rate', '')
    
    # Extract from existing JSON structure if present
    if 'audio' in row and isinstance(row['audio'], dict):
        if not sample_rate:
            sample_rate = row['audio'].get('sampling_rate', '')
        if not duration:
            duration = row['audio'].get('duration', '')
    
    if 'metadata' in row and isinstance(row['metadata'], dict):
        metadata = row['metadata']
        if not start_time:
            start_time = metadata.get('start_time', '')
        if not end_time:
            end_time = metadata.get('end_time', '')
        if not segment_index:
            segment_index = metadata.get('segment_index', '')
        if not original_textgrid:
            original_textgrid = metadata.get('original_textgrid', '')
        if not original_wav:
            original_wav = metadata.get('original_wav', '')
    
    # Choose which path to use
    chosen_path = relative_path if (use_relative_path and relative_path) else audio_path
    
    # Create full audio path
    if audio_base_path:
        full_audio_path = os.path.join(audio_base_path, chosen_path)
    else:
        full_audio_path = chosen_path
    
    # Determine sampling rate
    if use_original_sampling_rate and sample_rate:
        try:
            sampling_rate = int(float(sample_rate))
        except (ValueError, TypeError):
            sampling_rate = 16000
    else:
        sampling_rate = 16000
    
    # Create speaker ID
    speaker_id = base_filename
    
    # Create JSON entry with metadata
    json_entry = {
        "audio": {
            "path": full_audio_path,
            "sampling_rate": sampling_rate,
            "duration": float(duration) if duration else None
        },
        "sentence": transcription,
        "speaker": speaker_id,
        "metadata": {
            "segment_index": int(segment_index) if segment_index else None,
            "start_time": float(start_time) if start_time else None,
            "end_time": float(end_time) if end_time else None,
            "original_textgrid": original_textgrid,
            "original_wav": original_wav,
            "full_audio_path": audio_path,
            "relative_path": relative_path
        }
    }
    
    return json_entry


def split_data_by_speaker(json_data, train_ratio=0.8, test_ratio=0.1, valid_ratio=0.1, random_seed=42):
    """
    Split data into train/test/valid sets by speaker to avoid data leakage.
    
    Args:
        json_data (list): List of JSON entries
        train_ratio (float): Ratio for training set
        test_ratio (float): Ratio for test set
        valid_ratio (float): Ratio for validation set
        random_seed (int): Random seed for reproducibility
    
    Returns:
        tuple: (train_data, test_data, valid_data)
    """
    # Set random seed for reproducibility
    random.seed(random_seed)
    
    # Group data by speaker
    speaker_data = defaultdict(list)
    for entry in json_data:
        speaker_id = entry['speaker']
        speaker_data[speaker_id].append(entry)
    
    # Get list of speakers and shuffle
    speakers = list(speaker_data.keys())
    random.shuffle(speakers)
    
    # Calculate split indices
    total_speakers = len(speakers)
    train_end = int(total_speakers * train_ratio)
    test_end = train_end + int(total_speakers * test_ratio)
    
    # Split speakers
    train_speakers = speakers[:train_end]
    test_speakers = speakers[train_end:test_end]
    valid_speakers = speakers[test_end:]
    
    # Create data splits
    train_data = []
    test_data = []
    valid_data = []
    
    for speaker in train_speakers:
        train_data.extend(speaker_data[speaker])
    
    for speaker in test_speakers:
        test_data.extend(speaker_data[speaker])
    
    for speaker in valid_speakers:
        valid_data.extend(speaker_data[speaker])
    
    return train_data, test_data, valid_data


def split_data_random(json_data, train_ratio=0.8, test_ratio=0.1, valid_ratio=0.1, random_seed=42):
    """
    Split data randomly into train/test/valid sets.
    
    Args:
        json_data (list): List of JSON entries
        train_ratio (float): Ratio for training set
        test_ratio (float): Ratio for test set
        valid_ratio (float): Ratio for validation set
        random_seed (int): Random seed for reproducibility
    
    Returns:
        tuple: (train_data, test_data, valid_data)
    """
    # Set random seed for reproducibility
    random.seed(random_seed)
    
    # Shuffle the data
    shuffled_data = json_data.copy()
    random.shuffle(shuffled_data)
    
    # Calculate split indices
    total_samples = len(shuffled_data)
    train_end = int(total_samples * train_ratio)
    test_end = train_end + int(total_samples * test_ratio)
    
    # Split data
    train_data = shuffled_data[:train_end]
    test_data = shuffled_data[train_end:test_end]
    valid_data = shuffled_data[test_end:]
    
    return train_data, test_data, valid_data


def convert_csv_to_json(input_file, output_dir, audio_base_path="", use_relative_path=True, 
                       use_original_sampling_rate=True, split_by_speaker=True, 
                       train_ratio=0.8, test_ratio=0.1, valid_ratio=0.1, random_seed=42):
    """
    Convert CSV or JSON file to JSON format with train/test/valid split.
    
    Args:
        input_file (str): Path to input file (CSV or JSON)
        output_dir (str): Directory to save output JSON files
        audio_base_path (str): Base path to prepend to audio file paths (optional)
        use_relative_path (bool): Whether to use relative_path instead of audio_path
        use_original_sampling_rate (bool): Whether to use sample_rate from data or default 16000
        split_by_speaker (bool): Whether to split by speaker or randomly
        train_ratio (float): Ratio for training set
        test_ratio (float): Ratio for test set
        valid_ratio (float): Ratio for validation set
        random_seed (int): Random seed for reproducibility
    """
    
    try:
        # Load data from file (CSV or JSON)
        raw_data = load_data_from_file(input_file)
        print(f"Loaded {len(raw_data)} entries from {input_file}")
        
        # Process each entry
        json_data = []
        for row in raw_data:
            json_entry = process_data_entry(
                row, audio_base_path, use_relative_path, use_original_sampling_rate
            )
            json_data.append(json_entry)
    
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        return False
    except Exception as e:
        print(f"Error reading input file: {e}")
        return False
    
    # Split the data
    if split_by_speaker:
        train_data, test_data, valid_data = split_data_by_speaker(
            json_data, train_ratio, test_ratio, valid_ratio, random_seed
        )
        print(f"Split by speaker: {len(set(entry['speaker'] for entry in train_data))} train speakers, "
              f"{len(set(entry['speaker'] for entry in test_data))} test speakers, "
              f"{len(set(entry['speaker'] for entry in valid_data))} valid speakers")
    else:
        train_data, test_data, valid_data = split_data_random(
            json_data, train_ratio, test_ratio, valid_ratio, random_seed
        )
        print("Split randomly")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Write JSON outputs
    try:
        # Write train set
        train_file = os.path.join(output_dir, 'train.json')
        with open(train_file, 'w', encoding='utf-8') as jsonfile:
            json.dump(train_data, jsonfile, ensure_ascii=False, indent=2)
        
        # Write test set
        test_file = os.path.join(output_dir, 'test.json')
        with open(test_file, 'w', encoding='utf-8') as jsonfile:
            json.dump(test_data, jsonfile, ensure_ascii=False, indent=2)
        
        # Write validation set
        valid_file = os.path.join(output_dir, 'valid.json')
        with open(valid_file, 'w', encoding='utf-8') as jsonfile:
            json.dump(valid_data, jsonfile, ensure_ascii=False, indent=2)
        
        print(f"Successfully converted and split {len(json_data)} entries:")
        print(f"  Train: {len(train_data)} entries -> {train_file}")
        print(f"  Test: {len(test_data)} entries -> {test_file}")
        print(f"  Valid: {len(valid_data)} entries -> {valid_file}")
        return True
        
    except Exception as e:
        print(f"Error writing JSON files: {e}")
        return False


def convert_csv_to_json_with_metadata(input_file, output_dir, audio_base_path="", use_relative_path=True, 
                                    use_original_sampling_rate=True, split_by_speaker=True,
                                    train_ratio=0.8, test_ratio=0.1, valid_ratio=0.1, random_seed=42):
    """
    Convert CSV or JSON file to JSON format with additional metadata fields and train/test/valid split.
    
    Args:
        input_file (str): Path to input file (CSV or JSON)
        output_dir (str): Directory to save output JSON files
        audio_base_path (str): Base path to prepend to audio file paths (optional)
        use_relative_path (bool): Whether to use relative_path instead of audio_path
        use_original_sampling_rate (bool): Whether to use sample_rate from data or default 16000
        split_by_speaker (bool): Whether to split by speaker or randomly
        train_ratio (float): Ratio for training set
        test_ratio (float): Ratio for test set
        valid_ratio (float): Ratio for validation set
        random_seed (int): Random seed for reproducibility
    """
    
    try:
        # Load data from file (CSV or JSON)
        raw_data = load_data_from_file(input_file)
        print(f"Loaded {len(raw_data)} entries from {input_file}")
        
        # Process each entry
        json_data = []
        for row in raw_data:
            json_entry = process_data_entry_with_metadata(
                row, audio_base_path, use_relative_path, use_original_sampling_rate
            )
            json_data.append(json_entry)
    
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        return False
    except Exception as e:
        print(f"Error reading input file: {e}")
        return False
    
    # Split the data
    if split_by_speaker:
        train_data, test_data, valid_data = split_data_by_speaker(
            json_data, train_ratio, test_ratio, valid_ratio, random_seed
        )
        print(f"Split by speaker: {len(set(entry['speaker'] for entry in train_data))} train speakers, "
              f"{len(set(entry['speaker'] for entry in test_data))} test speakers, "
              f"{len(set(entry['speaker'] for entry in valid_data))} valid speakers")
    else:
        train_data, test_data, valid_data = split_data_random(
            json_data, train_ratio, test_ratio, valid_ratio, random_seed
        )
        print("Split randomly")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Write JSON outputs
    try:
        # Write train set
        train_file = os.path.join(output_dir, 'train.json')
        with open(train_file, 'w', encoding='utf-8') as jsonfile:
            json.dump(train_data, jsonfile, ensure_ascii=False, indent=2)
        
        # Write test set
        test_file = os.path.join(output_dir, 'test.json')
        with open(test_file, 'w', encoding='utf-8') as jsonfile:
            json.dump(test_data, jsonfile, ensure_ascii=False, indent=2)
        
        # Write validation set
        valid_file = os.path.join(output_dir, 'valid.json')
        with open(valid_file, 'w', encoding='utf-8') as jsonfile:
            json.dump(valid_data, jsonfile, ensure_ascii=False, indent=2)
        
        print(f"Successfully converted and split {len(json_data)} entries:")
        print(f"  Train: {len(train_data)} entries -> {train_file}")
        print(f"  Test: {len(test_data)} entries -> {test_file}")
        print(f"  Valid: {len(valid_data)} entries -> {valid_file}")
        return True
        
    except Exception as e:
        print(f"Error writing JSON files: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Convert CSV or JSON file to JSON format with train/test/valid split')
    parser.add_argument('input_file', help='Input file path (CSV or JSON)')
    parser.add_argument('output_dir', help='Output directory for JSON files')
    parser.add_argument('--audio-base-path', default='', 
                       help='Base path to prepend to audio file paths (optional)')
    parser.add_argument('--use-absolute-path', action='store_true',
                       help='Use absolute audio_path instead of relative_path')
    parser.add_argument('--default-sampling-rate', action='store_true',
                       help='Use default 16000 sampling rate instead of file sample_rate')
    parser.add_argument('--include-metadata', action='store_true',
                       help='Include additional metadata fields in output')
    parser.add_argument('--random-split', action='store_true',
                       help='Split randomly instead of by speaker (not recommended for speaker verification)')
    parser.add_argument('--train-ratio', type=float, default=0.9,
                       help='Training set ratio (default: 0.9)')
    parser.add_argument('--test-ratio', type=float, default=0.05,
                       help='Test set ratio (default: 0.05)')
    parser.add_argument('--valid-ratio', type=float, default=0.05,
                       help='Validation set ratio (default: 0.05)')
    parser.add_argument('--random-seed', type=int, default=42,
                       help='Random seed for reproducibility (default: 42)')
    
    args = parser.parse_args()
    
    # Validate ratios
    if abs(args.train_ratio + args.test_ratio + args.valid_ratio - 1.0) > 1e-6:
        print("Error: Train, test, and validation ratios must sum to 1.0")
        return
    
    # Check if input file exists
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' does not exist.")
        return
    
    # Check file format
    file_extension = Path(args.input_file).suffix.lower()
    if file_extension not in ['.csv', '.json']:
        print(f"Error: Unsupported file format '{file_extension}'. Supported formats: .csv, .json")
        return
    
    print(f"Processing {file_extension.upper()} file: {args.input_file}")
    
    # Set options
    use_relative_path = not args.use_absolute_path
    use_original_sampling_rate = not args.default_sampling_rate
    split_by_speaker = False
    
    # Choose conversion function based on metadata flag
    if args.include_metadata:
        success = convert_csv_to_json_with_metadata(
            args.input_file, 
            args.output_dir, 
            args.audio_base_path, 
            use_relative_path,
            use_original_sampling_rate,
            split_by_speaker,
            args.train_ratio,
            args.test_ratio,
            args.valid_ratio,
            args.random_seed
        )
    else:
        success = convert_csv_to_json(
            args.input_file, 
            args.output_dir, 
            args.audio_base_path, 
            use_relative_path,
            use_original_sampling_rate,
            split_by_speaker,
            args.train_ratio,
            args.test_ratio,
            args.valid_ratio,
            args.random_seed
        )
    
    if success:
        print("Conversion and splitting completed successfully!")
    else:
        print("Conversion failed!")


if __name__ == "__main__":
    main()