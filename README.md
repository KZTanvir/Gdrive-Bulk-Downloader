# Gdrive Bulk Downloader

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.7%2B-blue)

## Overview
The **Gdrive Bulk Downloader** is a Python-based tool designed for efficient and easy downloading of bulk files from Google Drive. It provides a user-friendly interface and robust functionality to manage and control your Google Drive downloads seamlessly.

## Features
- Bulk download files and folders from Google Drive.
- User authentication and access control.
- Modular structure with reusable functions.
- Customizable and easy to integrate with other projects.

## Requirements
- Python 3.7 or higher
- Required Python libraries (install using `pip install -r requirements.txt` if a requirements file is available):
  - `google-auth`
  - `google-api-python-client`
  - `oauth2client`

## Installation
1. Clone or download this repository:
   ```bash
   git clone https://github.com/yourusername/Gdrive-Bulk-Downloader.git
   cd Gdrive-Bulk-Downloader
   ```
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Ensure you have Google Drive API credentials. Place them in the appropriate location (e.g., `DriveLoader/Client_Credentials.py`).

## Usage
Run the `main.py` file to start the program:
```bash
python main.py
```

### Menu Options
1. **Specify Download Folder**
   - Prompts the user to input a folder name where downloaded files will be saved.
2. **Enter Bulk Links**
   - Accepts multiple Google Drive links for batch downloading.
3. **Download Folder**
   - Downloads a single folder from Google Drive based on a provided link.
4. **Download File**
   - Downloads a single file from Google Drive based on a provided link.
5. **Bulk Download Links**
   - Processes multiple links entered earlier and downloads their corresponding files/folders.
6. **About**
   - Displays information about the tool.

## Code Structure
- **`main.py`**: The entry point of the program, managing the main loop and user interactions.
- **`UserControl.py`**: Handles user authentication and token management.
- **`DriveLoader/`**:
  - `Drive_Browser.py`: Contains functionality for browsing Google Drive.
  - `Gdrive_Downloader.py`: Implements downloading of files and folders.
  - `Client_Credentials.py`: Manages API credentials.

## Example Workflow
1. **Specify a download folder:** Input a folder name to save files.
2. **Enter multiple links:** Paste Google Drive links into the program.
3. **Download:** Select from menu options to download files or folders individually or in bulk.

## Error Handling
- Invalid links: Prompts the user to re-enter valid links.
- Authentication errors: Displays clear messages and guides users to re-authenticate.

## Contribution
Contributions are welcome! To contribute:
1. Fork this repository.
2. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes and push them to your forked repository.
4. Open a pull request explaining your changes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

---
For further assistance, please refer to the comments in the code or raise an issue in the repository.

---
### Repository Structure
```plaintext
Gdrive-Bulk-Downloader/
├── main.py
├── README.md
├── requirements.txt
├── UserControl.py
├── DriveLoader/
│   ├── Client_Credentials.py
│   ├── Drive_Browser.py
│   ├── Gdrive_Downloader.py
│   ├── Gdrive_Uploader.py
└── functions.py
```

