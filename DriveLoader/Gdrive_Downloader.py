import os, time, requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from functions import *

class Gdrive_Bulker:
    def __init__(self, access_token) :
        self.access_token = access_token

        self.base_url = 'https://www.googleapis.com/drive/v3'
        self.folder_mime_type = 'application/vnd.google-apps.folder'

        self.root_folder_id = None  # Set the root folder ID here

        self.downloader_path = "Downloads"
        self.max_downloader_count = 3

    def get_headers(self):
        return {'Authorization': f'Bearer {self.access_token}'}

    def file_lister(self, folder_id, page_token=None):
        """Retrieve list of files in a Google Drive Folder"""
        url = f'{self.base_url}/files'
        params = {
            'q': f"'{folder_id}' in parents",
            'spaces': 'drive',
            'fields': 'nextPageToken, files(id, name, mimeType)',
            'pageToken': page_token
        }

        response = requests.get(url, headers=self.get_headers(), params=params)
        response.raise_for_status()

        file_lister_json = response.json()

        for file_name in [file['name'] for file in file_lister_json['files']]:
            print(f'File Found: {file_name}')

        return file_lister_json
    
    def file_size_finder(self, file_id):
        #fetch the file metadata to get the file size
        metadata_url = f'{self.base_url}/files/{file_id}?fields=size'
        metadata_response = requests.get(metadata_url, headers=self.get_headers())
        metadata_response.raise_for_status()
        total_size = int(metadata_response.json().get('size', 0))
        return total_size

    def file_downloader(self, file_id, file_name, folder_path, min_speed=1024, timeout=10, max_retries=5):
        """Download a file from Google Drive with retry logic automation."""

        file_name = sanitizer_names(file_name)
        file_path = os.path.join(folder_path, file_name)

        total_size = self.file_size_finder(file_id)
        #if the file exists, check if its size matches the expected size
        if os.path.exists(file_path):
            existing_size =  os.path.getsize(file_path)
            if existing_size == total_size:
                print('\n\n==========================================================')
                print(f'File  already downloaded and verified: {file_path}')
                print('==========================================================')
                return
            else:
                print(f'\nFile Size Mismatch for {file_path}. Deleting and redownloading....')
                os.remove(file_path)


        os.makedirs(folder_path, exist_ok=True)
        
        retry_count = 0  # Counting failed downloads
        
        while retry_count < max_retries:
            try:
                request_url = f'{self.base_url}/files/{file_id}?alt=media'
                response = requests.get(request_url, headers=self.get_headers(), stream=True)
                response.raise_for_status()
                #total_size = int(response.headers.get('Content-Length', 0))

                start_time = time.time()
                bytes_written = 0
                chunk_size = 0

                with open(file_path, 'wb') as out_file, tqdm(total=total_size, unit="B", unit_scale=True, desc=os.path.basename(file_path)) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            out_file.write(chunk)
                            pbar.update(len(chunk))
                            bytes_written += len(chunk)
                            chunk_size += len(chunk)
                            
                            # Chunk download speed
                            elapsed_time = time.time() - start_time
                            if elapsed_time > timeout:
                                current_speed = chunk_size / elapsed_time
                                if current_speed < min_speed:
                                    print(f"\nDownload speed too low ({current_speed:.2f} B/s). Retrying... (Attempt {retry_count + 1}/{max_retries})")
                                    break
                                chunk_size = 0
                                start_time = time.time()
                # If download completes successfully
                clear_console()
                print("\n\n==========================================")
                print(f"Downloaded: {file_path}")
                print("==========================================")
                return
            except requests.RequestException as e:
                print(f"\nError occurred while downloading {file_name}: {e}")
            
            retry_count += 1
            if os.path.exists(file_path):
                os.remove(file_path)
            print("Retrying...\n")
        
        print(f"Failed to download {file_name} after {max_retries} attempts.")
    
    def download_folder(self, folder_id=None, folder_path=None):
        """Recursively process Google Drive folders and download files."""
        
        #depricated will be patched soon from main.py
        if folder_id is None:
            folder_id = self.root_folder_id
        if folder_path is None:
            folder_path = self.downloader_path
        ########

        os.makedirs(folder_path, exist_ok=True)
        page_token = None

        while True:
            response = self.file_lister(folder_id, page_token)
            file_download_tasks = []

            # using threadpoolexecutor to manage concurrent downloads
            with ThreadPoolExecutor(max_workers=self.max_downloader_count) as executor:
                for file in response.get('files', []):
                    file_id = file['id']
                    file_name = file['name']
                    mime_type = file['mimeType']

                    if mime_type == self.folder_mime_type:
                        # Searching inside the folders
                        subfolder_path = os.path.join(folder_path, sanitizer_names(file_name))
                        self.download_folder(file_id, subfolder_path)
                    else:
                        # Start downloading the files if found
                        #self.file_downloader(file_id, file_name, folder_path)
                        future = executor.submit(self.file_downloader, file_id, file_name, folder_path)
                        file_download_tasks.append(future)
                # wait for all tasks to complete
                for future in as_completed(file_download_tasks):
                    try:
                        future.result()
                    except Exception as e:
                        print(f"An error occurred during download: {e}")
            
            page_token = response.get('nextPageToken')
            
            if not page_token:
                break
    
    def get_status(self):
        pass

    def download_single_file(self, file_id=None):
        '''downlod a single file froma google drive link.'''
        try:
            if file_id == None:
                file_id = self.root_folder_id
            metadata_url = f'{self.base_url}/files/{file_id}?fields=name'
            response = requests.get(metadata_url, headers=self.get_headers())
            response.raise_for_status()
            file_name = response.json()['name']
            self.file_downloader(file_id, file_name, self.downloader_path)
        except Exception as e:
            print(f'Failed to download file {file_name}: {e}')
