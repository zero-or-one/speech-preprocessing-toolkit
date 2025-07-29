import json
import os
from pathlib import Path
from typing import List, Dict, Any, Union

def load_json_file(file_path: str) -> Union[List, Dict]:
    """Load a JSON file and return its contents."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: File not found: {file_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {file_path}: {e}")
        return []
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return []

def combine_json_datasets(directories: List[str], output_dir: str = "combined_data"):
    """
    Combine train, test, and validation JSON files from multiple directories.
    
    Args:
        directories: List of directory paths containing the JSON files
        output_dir: Directory to save the combined files
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Initialize combined data containers
    combined_train = []
    combined_test = []
    combined_valid = []
    
    # Possible filenames for each split
    train_files = ['train.json', 'training.json', 'train_data.json']
    test_files = ['test.json', 'testing.json', 'test_data.json']
    valid_files = ['valid.json', 'validation.json', 'val.json', 'valid_data.json']
    
    print(f"Processing {len(directories)} directories...")
    
    for directory in directories:
        dir_path = Path(directory)
        
        if not dir_path.exists():
            print(f"Warning: Directory does not exist: {directory}")
            continue
            
        print(f"\nProcessing directory: {directory}")
        
        # Find and load train files
        train_loaded = False
        for train_file in train_files:
            train_path = dir_path / train_file
            if train_path.exists():
                print(f"  Loading {train_file}...")
                data = load_json_file(str(train_path))
                if isinstance(data, list):
                    combined_train.extend(data)
                elif isinstance(data, dict):
                    combined_train.append(data)
                train_loaded = True
                break
        
        if not train_loaded:
            print(f"  No train file found in {directory}")
        
        # Find and load test files
        test_loaded = False
        for test_file in test_files:
            test_path = dir_path / test_file
            if test_path.exists():
                print(f"  Loading {test_file}...")
                data = load_json_file(str(test_path))
                if isinstance(data, list):
                    combined_test.extend(data)
                elif isinstance(data, dict):
                    combined_test.append(data)
                test_loaded = True
                break
        
        if not test_loaded:
            print(f"  No test file found in {directory}")
        
        # Find and load validation files
        valid_loaded = False
        for valid_file in valid_files:
            valid_path = dir_path / valid_file
            if valid_path.exists():
                print(f"  Loading {valid_file}...")
                data = load_json_file(str(valid_path))
                if isinstance(data, list):
                    combined_valid.extend(data)
                elif isinstance(data, dict):
                    combined_valid.append(data)
                valid_loaded = True
                break
        
        if not valid_loaded:
            print(f"  No validation file found in {directory}")
    
    # Save combined datasets
    output_files = {
        'train.json': combined_train,
        'test.json': combined_test,
        'valid.json': combined_valid
    }
    
    print(f"\nSaving combined datasets to {output_dir}/")
    
    for filename, data in output_files.items():
        if data:  # Only save if there's data
            output_path = Path(output_dir) / filename
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"  Saved {filename} with {len(data)} items")
            except Exception as e:
                print(f"  Error saving {filename}: {e}")
        else:
            print(f"  No data found for {filename}, skipping...")
    
    print(f"\nCombination complete!")
    print(f"Train samples: {len(combined_train)}")
    print(f"Test samples: {len(combined_test)}")
    print(f"Validation samples: {len(combined_valid)}")

# Example usage
if __name__ == "__main__":
    # Example directories containing JSON files
    directories = ['/home/ali/dataset_common/kss', '/home/ali/dataset_common/zeroth-korean', #'KoreanReadSpeechCorpus',
            '/home/ali/dataset_common/KsponSpeech','/home/ali/dataset_common/common_voice', # 'pansori', 
            '/home/ali/dataset_common/seoul_corpus', '/home/ali/dataset_common/fleurs']
    
    # Combine all datasets
    combine_json_datasets(directories, output_dir="/home/ali/dataset_common/combined_datasets")
    
    # Alternative: Specify exact file paths if needed
    def combine_specific_files(file_paths: Dict[str, List[str]], output_dir: str = "combined_data"):
        """
        Combine specific JSON files by category.
        
        Args:
            file_paths: Dict with keys 'train', 'test', 'valid' and lists of file paths
            output_dir: Directory to save combined files
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        for split_name, paths in file_paths.items():
            combined_data = []
            
            print(f"\nCombining {split_name} files...")
            for path in paths:
                print(f"  Loading {path}...")
                data = load_json_file(path)
                if isinstance(data, list):
                    combined_data.extend(data)
                elif isinstance(data, dict):
                    combined_data.append(data)
            
            # Save combined file
            if combined_data:
                output_path = Path(output_dir) / f"{split_name}.json"
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(combined_data, f, indent=2, ensure_ascii=False)
                print(f"  Saved {split_name}.json with {len(combined_data)} items")
    
    # Example of combining specific files
    # specific_files = {
    #     'train': ['dir1/train.json', 'dir2/training.json', 'dir3/train_data.json'],
    #     'test': ['dir1/test.json', 'dir2/test.json'],
    #     'valid': ['dir1/valid.json', 'dir2/validation.json']
    # }
    # combine_specific_files(specific_files)