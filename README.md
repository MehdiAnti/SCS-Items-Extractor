# SCS Items Extractor

**SCS Items Extractor** is a Python-based tool for processing and extracting some files from `.scs` files used in Euro Truck Simulator 2 (ETS2) and American Truck Simulator (ATS). It allows you to safely backup, clean, and package the result.


## Features

- Process `.scs` files for ETS2 and ATS to detect needed files with Regex.
- Automatically backup required detected accessory folders.
- Clean unwanted files while keeping necessary assets.
- Extract game version from `version.scs`.
- Zip processed files for easy storage or distribution.

## Requirements

- **Python 3.10+**
- **Windows OS** (tested)
- `tkinter` (usually included with Python)
- `converter_pix.exe` (included in `data/` folder)
- SCS files list configuration (`data/scs_files.txt`)

## Installation
Go into [**Releases**](https://github.com/MehdiAnti/SCS-Items-Extractor/releases) and **Download** the ZIP file from there, then Extract.

OR

1. Clone the repository:
```bash
git clone https://github.com/MehdiAnti/SCS-Items-Extractor.git
cd scs-items-extractor
```
2. Ensure **Python 3.10+** is installed.
3. Make sure `converter_pix.exe` and `scs_files.txt` are in the data/ folder.
4. Run the program:
```bash
python main.py
```

## Usage

1. Click “Select Folder” to choose the directory containing your .scs files.
2. The program will process the files, clean unnecessary folders, and zip the results.
3. View progress on the progress bar and check log.txt for detailed logs.

      ⚠️ Only run one instance at a time to avoid conflicts in temporary folders and log files.


## Thanks to

[**mwl4**](https://github.com/mwl4) - [Converter PIX](https://github.com/mwl4/ConverterPIX) project

## License

This project is licensed under the [**GNU General Public License v3.0**](https://github.com/MehdiAnti/SCS-Items-Extractor/blob/main/LICENSE).

## Contributing

Contributions are welcome! Please submit bug reports, feature requests, or pull requests via GitHub.

## Disclaimer

This tool is provided as-is. The author is not responsible for any damage or data loss resulting from its use. Always backup your files before processing.
