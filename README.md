# Speech Preprocessing Toolkit
Reusable preprocessing pipelines for speech datasets. \
Below is written by claude

-------
A comprehensive collection of reusable preprocessing pipelines for speech datasets, designed to streamline audio processing, transcription normalization, and dataset preparation for machine learning projects.

## 🚀 Features

- **Multi-format audio conversion** to WAV
- **Audio resampling** with high-quality interpolation
- **Transcription normalization** across multiple formats
- **Dataset splitting** for train/validation sets
- **Duration analysis** and dataset statistics
- **Flexible CLI interfaces** for all tools

## 📁 Tools Overview

### 🎵 Audio Processing

**`convert_to_wav.py`** - Universal Audio Format Converter
- Converts PCM, MP3, FLAC, OGG, M4A, AAC, and other formats to WAV
- Batch processing with recursive directory support
- Error logging and progress tracking

**`resample.py`** - Audio Resampling Tool
- High-quality cubic interpolation resampling
- Default target: 16kHz (configurable)
- Handles mono and stereo audio
- Batch processing with optional file overwriting

### 📝 Text Processing

**`normalize_transcript.py`** - Transcription Normalizer
- Supports TXT, JSON, and CSV formats
- Removes audio markers (b/, l/, o/, n/, etc.)
- Normalizes number formats and special characters
- Configurable rules via JSON config files

**`split.py`** - Data Splitting Tool
- Splits datasets into train/validation sets
- Supports TXT, JSON, and CSV formats
- Customizable ratios and random seeds
- Cross-format conversion capabilities

### 📊 Analysis

**`calculate_duration.py`** - Dataset Duration Calculator
- Comprehensive audio duration analysis
- Statistical metrics (mean, median, std dev)
- Duration distribution analysis
- Multi-format transcription file support
- Detailed error reporting

## 🛠️ Installation

```bash
# Clone the repository
git clone <repository-url>
cd speech-preprocessing-toolkit

# Install dependencies
pip install numpy scipy soundfile tqdm pandas

# Optional: For additional audio format support
pip install librosa pydub
```

## 🚀 Quick Start

### 1. Download and Extract Dataset
```bash
# Follow the guide for dataset preparation
cat download_extract_guide.md
```

### 2. Convert Audio Files
```bash
# Convert all audio files to WAV format
python convert_to_wav.py /path/to/audio/directory

# Delete original files after conversion
python convert_to_wav.py /path/to/audio --delete-original
```

### 3. Resample Audio
```bash
# Resample all WAV files to 16kHz
python resample.py /path/to/wav/files

# Custom target rate with file overwriting
python resample.py /path/to/wav/files --target-rate 22050 --overwrite
```

### 4. Normalize Transcriptions
```bash
# Normalize transcription file
python normalize_transcript.py transcripts.txt

# Process multiple formats with custom config
python normalize_transcript.py data.json data.csv -c config.json
```

### 5. Split Dataset
```bash
# Split into 90% train, 10% validation
python split.py dataset.txt

# Custom ratio and format conversion
python split.py data.csv --train-ratio 0.85 --output-format json
```

### 6. Analyze Dataset
```bash
# Calculate total duration and statistics
python calculate_duration.py transcripts.txt /path/to/audio

# Detailed analysis with output file
python calculate_duration.py data.csv /audio --verbose -o analysis.txt
```

## 📋 Usage Examples

### Complete Pipeline Example
```bash
# 1. Convert audio files
python convert_to_wav.py ./raw_audio --delete-original

# 2. Resample to 16kHz
python resample.py ./raw_audio --target-rate 16000 --overwrite

# 3. Normalize transcriptions
python normalize_transcript.py raw_transcripts.txt

# 4. Split dataset
python split.py raw_transcripts_normalized.txt --train-ratio 0.9

# 5. Analyze final dataset
python calculate_duration.py raw_transcripts_train.txt ./raw_audio
```

### Batch Processing Multiple Datasets
```bash
# Process all transcription files in directory
python normalize_transcript.py /data/transcripts --recursive

# Convert and resample entire audio collection
python convert_to_wav.py /data/audio --recursive
python resample.py /data/audio --recursive --target-rate 16000
```

## ⚙️ Configuration

### Transcription Normalization Config
Create `config.json` for custom normalization rules:
```json
{
  "marker_chars": "blnourw",
  "special_chars": "[\\/*\\+]",
  "extension_replacements": {
    ".pcm": ".wav",
    ".raw": ".wav"
  },
  "custom_replacements": {
    "old_text": "new_text"
  }
}
```

## 📖 Documentation

Each tool includes comprehensive help:
```bash
python <tool_name>.py --help
```

### Common Options
- `--recursive`: Process subdirectories
- `--dry-run`: Preview operations without executing
- `--verbose`: Detailed output and logging
- `-o, --output`: Specify output file/directory

## 🔧 Dependencies

**Core Requirements:**
- `numpy` - Numerical computations
- `scipy` - Audio interpolation
- `soundfile` - Audio I/O operations
- `tqdm` - Progress bars
- `pandas` - Data manipulation (optional)

**Optional:**
- `librosa` - Advanced audio processing
- `pydub` - Additional format support

## 📄 File Structure

```
speech-preprocessing-toolkit/
├── README.md                    # This file
├── LICENSE                      # License information
├── download_extract_guide.md    # Dataset download guide
├── convert_to_wav.py           # Audio format converter
├── resample.py                 # Audio resampling tool
├── normalize_transcript.py     # Transcription normalizer
├── split.py                    # Dataset splitting tool
└── calculate_duration.py       # Duration analysis tool
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## 📜 License

See [LICENSE](LICENSE) file for details.

## 🆘 Support

For questions or issues:
1. Check the tool-specific help: `python <tool>.py --help`
2. Review error logs generated by each tool
3. Open an issue with detailed error information

---

**Happy preprocessing! 🎤✨**