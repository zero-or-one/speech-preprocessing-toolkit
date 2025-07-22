import json
import re
import os
from typing import List, Dict, Any

def contains_english_or_numbers(text: str) -> bool:
    """
    Check if text contains English characters (a-z, A-Z) or numbers (0-9)
    
    Args:
        text: The text to check
        
    Returns:
        True if text contains English characters or numbers, False otherwise
    """
    # Pattern to match English letters and numbers
    pattern = r'[a-zA-Z0-9]'
    return bool(re.search(pattern, text))

def clean_json_file(input_path: str, output_path: str) -> tuple[int, int]:
    """
    Clean a JSON file by removing samples with English characters or numbers
    
    Args:
        input_path: Path to input JSON file
        output_path: Path to output JSON file
        
    Returns:
        Tuple of (original_count, cleaned_count)
    """
    try:
        # Read the JSON file
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        original_count = len(data)
        
        # Filter out samples with English characters or numbers
        cleaned_data = []
        for sample in data:
            if 'text' in sample and not contains_english_or_numbers(sample['text']):
                cleaned_data.append(sample)
        
        cleaned_count = len(cleaned_data)
        
        # Write the cleaned data to output file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
        
        return original_count, cleaned_count
        
    except FileNotFoundError:
        print(f"Error: File {input_path} not found")
        return 0, 0
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file {input_path}")
        return 0, 0
    except Exception as e:
        print(f"Error processing {input_path}: {str(e)}")
        return 0, 0

def main():
    """
    Main function to process train, valid, and test JSON files
    """
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Give a directory of dataser")
    parser.add_argument('directory')

    args = parser.parse_args()

    # Define file paths
    files_to_process = ['train.json', 'valid.json', 'test.json']
    
    total_original = 0
    total_cleaned = 0
    
    print("Starting text cleaning process...")
    print("Removing samples with English characters or numbers from text field\n")
    
    for filename in files_to_process:
        input_path = os.path.join(args.directory, filename)
        output_path = os.path.join(args.directory, f"{filename[:-5]}_cleaned" + '.json')
        
        print(f"Processing {filename}...")
        
        if not os.path.exists(input_path):
            print(f"  Warning: {filename} not found, skipping...")
            continue
        
        original_count, cleaned_count = clean_json_file(input_path, output_path)
        removed_count = original_count - cleaned_count
        
        if original_count > 0:
            removal_percentage = (removed_count / original_count) * 100
            print(f"  Original samples: {original_count}")
            print(f"  Cleaned samples: {cleaned_count}")
            print(f"  Removed samples: {removed_count} ({removal_percentage:.1f}%)")
            print(f"  Output saved to: {output_path}")
        
        total_original += original_count
        total_cleaned += cleaned_count
        print()
    
    # Print summary
    if total_original > 0:
        total_removed = total_original - total_cleaned
        total_percentage = (total_removed / total_original) * 100
        print("="*50)
        print("SUMMARY:")
        print(f"Total original samples: {total_original}")
        print(f"Total cleaned samples: {total_cleaned}")
        print(f"Total removed samples: {total_removed} ({total_percentage:.1f}%)")
        print("="*50)
    else:
        print("No files were processed successfully.")

if __name__ == "__main__":
    main()