# Download and Extract Files Guide

A comprehensive reference for downloading datasets and extracting various archive formats.

## Downloading Files with wget

### Basic Download
```bash
wget https://example.com/dataset.zip
```

### Download with Custom Filename
```bash
wget -O my_dataset.zip https://example.com/dataset.zip
```

### Download to Specific Directory
```bash
wget -P /path/to/directory https://example.com/dataset.zip
```

### Download with Progress Bar
```bash
wget --progress=bar https://example.com/dataset.zip
```

### Resume Interrupted Download
```bash
wget -c https://example.com/dataset.zip
```

### Download Quietly (No Output)
```bash
wget -q https://example.com/dataset.zip
```

### Download Multiple Files
```bash
wget https://example.com/file1.zip https://example.com/file2.tar.gz
```

### Download from File List
```bash
wget -i urls.txt
```

## Extracting Archives

### ZIP Files (.zip)

**Extract:**
```bash
unzip filename.zip
```

**Extract to specific directory:**
```bash
unzip filename.zip -d /path/to/destination
```

**List contents without extracting:**
```bash
unzip -l filename.zip
```

**Extract specific files:**
```bash
unzip filename.zip file1.txt file2.txt
```

**Extract with verbose output:**
```bash
unzip -v filename.zip
```

**Overwrite existing files without prompting:**
```bash
unzip -o filename.zip
```

### TAR Files (.tar)

**Extract:**
```bash
tar -xf filename.tar
```

**Extract with verbose output:**
```bash
tar -xvf filename.tar
```

**Extract to specific directory:**
```bash
tar -xf filename.tar -C /path/to/destination
```

**List contents without extracting:**
```bash
tar -tf filename.tar
```

### Compressed TAR Files (.tar.gz, .tgz)

**Extract:**
```bash
tar -xzf filename.tar.gz
# or
tar -xzf filename.tgz
```

**Extract with verbose output:**
```bash
tar -xzvf filename.tar.gz
```

**Extract to specific directory:**
```bash
tar -xzf filename.tar.gz -C /path/to/destination
```

**List contents without extracting:**
```bash
tar -tzf filename.tar.gz
```

### GZIP Files (.gz)

**Decompress:**
```bash
gunzip filename.gz
# or
gzip -d filename.gz
```

**Keep original file while decompressing:**
```bash
gzip -dk filename.gz
```

**View contents without decompressing:**
```bash
zcat filename.gz
```

### BZIP2 Files (.tar.bz2, .bz2)

**Extract tar.bz2:**
```bash
tar -xjf filename.tar.bz2
```

**Decompress .bz2:**
```bash
bunzip2 filename.bz2
# or
bzip2 -d filename.bz2
```

### XZ Files (.tar.xz, .xz)

**Extract tar.xz:**
```bash
tar -xJf filename.tar.xz
```

**Decompress .xz:**
```bash
unxz filename.xz
# or
xz -d filename.xz
```

### 7-Zip Files (.7z)

**Extract:**
```bash
7z x filename.7z
```

**Extract to specific directory:**
```bash
7z x filename.7z -o/path/to/destination
```

## Creating Archives

### Create ZIP
```bash
zip -r archive.zip directory_name/
```

### Create TAR
```bash
tar -cf archive.tar directory_name/
```

### Create compressed TAR
```bash
tar -czf archive.tar.gz directory_name/
```

### Create BZIP2 compressed TAR
```bash
tar -cjf archive.tar.bz2 directory_name/
```

## Common Workflows

### Download and Extract ZIP
```bash
wget https://example.com/dataset.zip
unzip dataset.zip
rm dataset.zip  # Optional: remove archive after extraction
```

### Download and Extract TAR.GZ
```bash
wget https://example.com/dataset.tar.gz
tar -xzf dataset.tar.gz
rm dataset.tar.gz  # Optional: remove archive after extraction
```

### Download to Temp Directory and Extract
```bash
mkdir temp_download
cd temp_download
wget https://example.com/dataset.zip
unzip dataset.zip
mv extracted_folder/ ../
cd ..
rm -rf temp_download/
```

### Download Large File with Progress and Resume
```bash
wget -c --progress=bar https://example.com/large_dataset.tar.gz
tar -xzf large_dataset.tar.gz
```

## Useful Tips

### Check Available Disk Space
```bash
df -h
```

### Check Archive Size Before Extracting
```bash
ls -lh filename.zip
```

### Extract and View Progress
```bash
tar -xzvf filename.tar.gz | pv -l > /dev/null
```

### Verify Download Integrity (if checksum provided)
```bash
wget https://example.com/dataset.zip
wget https://example.com/dataset.zip.sha256
sha256sum -c dataset.zip.sha256
```

### Extract Multiple Archives
```bash
for file in *.zip; do
    unzip "$file"
done

for file in *.tar.gz; do
    tar -xzf "$file"
done
```

## Troubleshooting

### Permission Denied
```bash
chmod +x filename
# or
sudo unzip filename.zip
```

### Archive Corrupted
```bash
# Test zip file
unzip -t filename.zip

# Test tar file
tar -tf filename.tar.gz > /dev/null
```

### Not Enough Space
```bash
# Extract to external drive
unzip filename.zip -d /mnt/external/

# Or use streaming extraction
wget -qO- https://example.com/dataset.tar.gz | tar -xzf -
```

### Network Issues with wget
```bash
# Retry failed downloads
wget --tries=3 --retry-connrefused https://example.com/dataset.zip

# Set timeout
wget --timeout=30 https://example.com/dataset.zip
```