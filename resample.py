import os
import numpy as np
import soundfile as sf
from scipy import interpolate
from pathlib import Path
import argparse

def upsample_audio(audio_data, original_rate, target_rate):
    """
    Upsample audio using high-quality interpolation.
    
    :param audio_data: Input audio numpy array
    :param original_rate: Original sample rate
    :param target_rate: Target sample rate
    :return: Upsampled audio numpy array
    """
    if original_rate == target_rate:
        return audio_data
    
    # Calculate time arrays
    original_time = np.linspace(0, len(audio_data)/original_rate, len(audio_data))
    target_time = np.linspace(0, original_time[-1], int(len(audio_data) * target_rate / original_rate))
    
    # Create interpolation function
    interpolator = interpolate.interp1d(original_time, audio_data, kind='cubic')
    
    # Interpolate to new sample rate
    upsampled_audio = interpolator(target_time)
    
    return upsampled_audio

def downsample_audio(audio_data, original_rate, target_rate):
    """
    Downsample audio using high-quality interpolation.
    
    :param audio_data: Input audio numpy array
    :param original_rate: Original sample rate
    :param target_rate: Target sample rate
    :return: Downsampled audio numpy array
    """
    if original_rate == target_rate:
        return audio_data
    
    # Calculate time arrays
    original_time = np.linspace(0, len(audio_data)/original_rate, len(audio_data))
    target_time = np.linspace(0, original_time[-1], int(len(audio_data) * target_rate / original_rate))
    
    # Create interpolation function
    interpolator = interpolate.interp1d(original_time, audio_data, kind='cubic')
    
    # Interpolate to new sample rate
    downsampled_audio = interpolator(target_time)
    
    return downsampled_audio

def resample_audio(audio_data, original_rate, target_rate):
    """
    Resample audio to target sample rate (up or down).
    
    :param audio_data: Input audio numpy array
    :param original_rate: Original sample rate
    :param target_rate: Target sample rate
    :return: Resampled audio numpy array
    """
    if original_rate == target_rate:
        return audio_data
    
    # Calculate time arrays
    original_time = np.linspace(0, len(audio_data)/original_rate, len(audio_data))
    target_time = np.linspace(0, original_time[-1], int(len(audio_data) * target_rate / original_rate))
    
    # Create interpolation function
    interpolator = interpolate.interp1d(original_time, audio_data, kind='cubic')
    
    # Interpolate to new sample rate
    resampled_audio = interpolator(target_time)
    
    return resampled_audio

def resample_wav_file(input_path, output_path, target_rate):
    """
    Resample a single WAV file to target sample rate.
    
    :param input_path: Path to the input WAV file
    :param output_path: Path for the output WAV file
    :param target_rate: Target sample rate
    """
    try:
        # Read the WAV file
        audio_data, original_rate = sf.read(input_path)
        
        # Handle stereo audio (resample each channel separately)
        if len(audio_data.shape) > 1:
            resampled_channels = []
            for channel in range(audio_data.shape[1]):
                channel_data = audio_data[:, channel]
                resampled_channel = resample_audio(channel_data, original_rate, target_rate)
                resampled_channels.append(resampled_channel)
            resampled_audio = np.column_stack(resampled_channels)
        else:
            # Mono audio
            resampled_audio = resample_audio(audio_data, original_rate, target_rate)
        
        # Save the resampled audio
        sf.write(output_path, resampled_audio, target_rate)
        
        return True, original_rate, len(audio_data), len(resampled_audio)
    
    except Exception as e:
        print(f"Error resampling {input_path}: {e}")
        return False, None, None, None

def resample_all_wav_files(input_dir, target_rate=16000, output_suffix="_resampled", 
                          overwrite=False, recursive=True):
    """
    Resample all WAV files in a directory to target sample rate.
    
    :param input_dir: Directory containing WAV files
    :param target_rate: Target sample rate (default 16000 Hz)
    :param output_suffix: Suffix to add to output filenames (default "_resampled")
    :param overwrite: If True, overwrite original files instead of creating new ones
    :param recursive: If True, search subdirectories recursively
    """
    # Ensure the input directory exists
    if not os.path.isdir(input_dir):
        print(f"Error: {input_dir} is not a valid directory.")
        return
    
    resampled_count = 0
    skipped_count = 0
    error_count = 0
    
    # Use os.walk for recursive or just listdir for non-recursive
    if recursive:
        file_iterator = os.walk(input_dir)
    else:
        file_iterator = [(input_dir, [], os.listdir(input_dir))]
    
    for dirpath, dirnames, filenames in file_iterator:
        for filename in filenames:
            # Check if the file is a WAV file
            if filename.lower().endswith('.wav'):
                input_path = os.path.join(dirpath, filename)
                
                # Determine output path
                if overwrite:
                    output_path = input_path
                else:
                    name_without_ext = os.path.splitext(filename)[0]
                    output_filename = f"{name_without_ext}{output_suffix}.wav"
                    output_path = os.path.join(dirpath, output_filename)
                
                # Skip if output file already exists (unless overwriting)
                if not overwrite and os.path.exists(output_path):
                    print(f"Skipping {filename} - resampled file already exists")
                    skipped_count += 1
                    continue
                
                print(f"Processing: {filename}")
                
                # Resample the file
                success, original_rate, original_length, resampled_length = resample_wav_file(
                    input_path, output_path, target_rate
                )
                
                if success:
                    if original_rate == target_rate:
                        print(f"  ✓ Already at target rate ({target_rate} Hz)")
                        skipped_count += 1
                    else:
                        resampled_count += 1
                        print(f"  ✓ Resampled: {original_rate} Hz → {target_rate} Hz")
                        print(f"  ✓ Length: {original_length} → {resampled_length} samples")
                        if not overwrite:
                            print(f"  ✓ Saved as: {os.path.basename(output_path)}")
                else:
                    error_count += 1
                    # Log the error
                    with open('resampling_errors.log', 'a') as log_file:
                        log_file.write(f"Error resampling {filename} in {dirpath}\n")
    
    print(f"\nResampling complete!")
    print(f"Successfully resampled: {resampled_count} files")
    print(f"Already at target rate: {skipped_count} files")
    print(f"Errors encountered: {error_count} files")
    if error_count > 0:
        print("Check resampling_errors.log for details")

def main():
    parser = argparse.ArgumentParser(description='Resample WAV files to target sample rate')
    parser.add_argument('input_dir', help='Input directory containing WAV files')
    parser.add_argument('--target-rate', type=int, default=16000, 
                       help='Target sample rate in Hz (default: 16000)')
    parser.add_argument('--output-suffix', default='_resampled',
                       help='Suffix for output filenames (default: _resampled)')
    parser.add_argument('--overwrite', action='store_true',
                       help='Overwrite original files instead of creating new ones')
    parser.add_argument('--no-recursive', action='store_true',
                       help='Do not search subdirectories recursively')
    
    args = parser.parse_args()
    
    resample_all_wav_files(
        args.input_dir,
        target_rate=args.target_rate,
        output_suffix=args.output_suffix,
        overwrite=args.overwrite,
        recursive=not args.no_recursive
    )

if __name__ == '__main__':
    main()