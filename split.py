import numpy as np
import json
import csv
import argparse
from pathlib import Path
import pandas as pd

def load_txt_data(input_file):
    """Load data from a text file."""
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    return lines

def load_json_data(input_file):
    """Load data from a JSON file."""
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle different JSON structures
    if isinstance(data, list):
        # If it's a list, convert each item to a line
        if all(isinstance(item, str) for item in data):
            # List of strings
            lines = [line + '\n' if not line.endswith('\n') else line for line in data]
        else:
            # List of objects, convert to JSON strings
            lines = [json.dumps(item, ensure_ascii=False) + '\n' for item in data]
    elif isinstance(data, dict):
        # If it's a single object, treat each value as a line or the whole object as one line
        if 'data' in data and isinstance(data['data'], list):
            # Common structure: {"data": [...]}
            lines = [json.dumps(item, ensure_ascii=False) + '\n' for item in data['data']]
        else:
            # Treat the entire object as one line
            lines = [json.dumps(data, ensure_ascii=False) + '\n']
    else:
        # Single value, treat as one line
        lines = [json.dumps(data, ensure_ascii=False) + '\n']
    
    return lines

def load_csv_data(input_file):
    """Load data from a CSV file."""
    # Try to read with pandas first for better handling
    try:
        df = pd.read_csv(input_file)
        # Convert each row to a JSON string
        lines = []
        for _, row in df.iterrows():
            line = json.dumps(row.to_dict(), ensure_ascii=False) + '\n'
            lines.append(line)
        return lines
    except ImportError:
        # Fallback to standard csv module if pandas is not available
        lines = []
        with open(input_file, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                line = json.dumps(row, ensure_ascii=False) + '\n'
                lines.append(line)
        return lines

def save_txt_data(data, output_file):
    """Save data to a text file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(data)

def save_json_data(data, output_file):
    """Save data to a JSON file."""
    # Convert lines back to JSON objects
    json_data = []
    for line in data:
        line = line.strip()
        if line:
            try:
                json_obj = json.loads(line)
                json_data.append(json_obj)
            except json.JSONDecodeError:
                # If it's not valid JSON, treat it as a string
                json_data.append(line)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

def save_csv_data(data, output_file):
    """Save data to a CSV file."""
    # Convert lines back to dictionaries
    rows = []
    for line in data:
        line = line.strip()
        if line:
            try:
                row_dict = json.loads(line)
                rows.append(row_dict)
            except json.JSONDecodeError:
                # If it's not valid JSON, create a simple row
                rows.append({'text': line})
    
    if rows:
        # Get all unique keys
        all_keys = set()
        for row in rows:
            if isinstance(row, dict):
                all_keys.update(row.keys())
        
        # Write CSV
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(all_keys))
            writer.writeheader()
            for row in rows:
                if isinstance(row, dict):
                    writer.writerow(row)

def load_and_split_data(input_file, train_ratio=0.9, random_seed=42, output_format=None):
    """
    Load data from various formats, shuffle it, split into train/validation sets, and save them.
    
    Parameters:
    input_file (str): Path to input file (.txt, .json, .csv)
    train_ratio (float): Ratio of data to use for training (default: 0.9)
    random_seed (int): Random seed for reproducibility (default: 42)
    output_format (str): Force output format ('txt', 'json', 'csv'). If None, uses input format.
    """
    input_path = Path(input_file)
    
    # Check if file exists
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Determine file format
    file_extension = input_path.suffix.lower()
    
    # Load data based on file format
    print(f"Loading data from: {input_file}")
    if file_extension == '.txt':
        lines = load_txt_data(input_file)
    elif file_extension == '.json':
        lines = load_json_data(input_file)
    elif file_extension == '.csv':
        lines = load_csv_data(input_file)
    else:
        raise ValueError(f"Unsupported file format: {file_extension}. Supported formats: .txt, .json, .csv")
    
    # Remove empty lines
    lines = [line for line in lines if line.strip()]
    
    if len(lines) == 0:
        raise ValueError("No data found in the input file")
    
    # Shuffle the data
    np.random.seed(random_seed)
    np.random.shuffle(lines)
    
    # Calculate split index
    split_idx = int(len(lines) * train_ratio)
    
    # Split the data
    train_data = lines[:split_idx]
    val_data = lines[split_idx:]
    
    # Determine output format
    if output_format is None:
        output_format = file_extension[1:]  # Remove the dot
    
    # Create output filenames with specified format
    output_extension = f".{output_format}"
    train_file = input_path.parent / f"{input_path.stem}_train{output_extension}"
    val_file = input_path.parent / f"{input_path.stem}_val{output_extension}"
    
    # Save the splits based on output format
    print(f"Saving splits in {output_format.upper()} format...")
    
    if output_format == 'txt':
        save_txt_data(train_data, train_file)
        save_txt_data(val_data, val_file)
    elif output_format == 'json':
        save_json_data(train_data, train_file)
        save_json_data(val_data, val_file)
    elif output_format == 'csv':
        save_csv_data(train_data, train_file)
        save_csv_data(val_data, val_file)
    else:
        raise ValueError(f"Unsupported output format: {output_format}")
    
    # Print statistics
    print(f"\nData split completed successfully!")
    print(f"Total lines: {len(lines)}")
    print(f"Training lines: {len(train_data)} ({train_ratio*100:.1f}%)")
    print(f"Validation lines: {len(val_data)} ({(1-train_ratio)*100:.1f}%)")
    print(f"\nFiles saved:")
    print(f"Training data: {train_file}")
    print(f"Validation data: {val_file}")
    
    return train_file, val_file

def main():
    parser = argparse.ArgumentParser(description='Split data files into train/validation sets')
    parser.add_argument('input_file', help='Input file path (.txt, .json, .csv)')
    parser.add_argument('--train-ratio', type=float, default=0.9,
                       help='Ratio of data to use for training (default: 0.9)')
    parser.add_argument('--random-seed', type=int, default=42,
                       help='Random seed for reproducibility (default: 42)')
    parser.add_argument('--output-format', choices=['txt', 'json', 'csv'],
                       help='Output format (default: same as input format)')
    
    args = parser.parse_args()
    
    try:
        # Validate train ratio
        if not 0 < args.train_ratio < 1:
            raise ValueError("Train ratio must be between 0 and 1")
        
        load_and_split_data(
            args.input_file,
            train_ratio=args.train_ratio,
            random_seed=args.random_seed,
            output_format=args.output_format
        )
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    # Example usage when run as script
    import sys
    sys.exit(main())