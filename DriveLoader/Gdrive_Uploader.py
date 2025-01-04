import mimetypes
import os
import time
from googleapiclient.http import MediaFileUpload
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import requests
from functions import sanitizer_names

class GdriveUploader:
    def __init__(self, access_token, max_retries=5, min_chunk_size=512 * 1024, max_chunk_size=12 * 1024 * 1024):
        self.access_token = access_token
        self.base_url = 'https://www.googleapis.com/upload/drive/v3/files'
        self.folder_mime_type = 'application/vnd.google-apps.folder'
        self.max_retries = max_retries
        self.min_chunk_size = min_chunk_size  # Minimum chunk size (512 KB)
        self.max_chunk_size = max_chunk_size  # Maximum chunk size (12 MB)
        self.root_filefolder_id = None
        self.max_uploader_count = 2
    
    def get_headers(self):
        return {'Authorization': f'Bearer {self.access_token}'}

    def _resumable_upload(self, upload_url, file_path):
        """Optimized file upload with dynamic chunk size adjustment based on speed."""
        file_size = os.path.getsize(file_path)
        current_chunk_size = self.min_chunk_size

        retries = 0
        upload_successful = False

        # Create a persistent session for network efficiency
        session = requests.Session()

        with open(file_path, 'rb') as f, tqdm(total=file_size, unit='B', unit_scale=True, desc=os.path.basename(file_path)) as pbar:
            bytes_uploaded = 0

            while not upload_successful and retries < self.max_retries:
                try:
                    f.seek(bytes_uploaded)
                    start_time = time.time()

                    while bytes_uploaded < file_size:
                        chunk = f.read(current_chunk_size)
                        if not chunk:
                            break  # End of file

                        headers = {
                            'Authorization': f'Bearer {self.access_token}',
                            'Content-Length': str(len(chunk)),
                            'Content-Range': f'bytes {bytes_uploaded}-{bytes_uploaded + len(chunk) - 1}/{file_size}'
                        }

                        # Upload chunk
                        response = session.put(upload_url, headers=headers, data=chunk)
                        if response.status_code not in (200, 201, 308):
                            raise requests.RequestException(f"Unexpected response: {response.status_code}")

                        # Update progress
                        bytes_uploaded += len(chunk)
                        pbar.update(len(chunk))

                        # Measure time taken and adjust chunk size
                        elapsed_time = time.time() - start_time
                        if elapsed_time > 0:
                            speed = len(chunk) / elapsed_time  # bytes per second

                            # Adjust chunk size based on speed
                            if speed > 200 * 1024:  # > 200 KB/s
                                current_chunk_size = min(self.max_chunk_size, current_chunk_size * 2)
                            elif speed < 190 * 1024 and current_chunk_size > self.min_chunk_size:  # < 190 KB/s
                                current_chunk_size = max(self.min_chunk_size, current_chunk_size // 2)

                        start_time = time.time()  # Reset start time for next chunk

                    upload_successful = True

                    print(f"\nFile '{os.path.basename(file_path)}' uploaded successfully!\n")

                except requests.RequestException as e:
                    retries += 1
                    print(f"Upload error: {e}. Retrying... ({retries}/{self.max_retries})")
                    time.sleep(min(2 ** retries, 60))  # Exponential backoff, capped at 60 seconds

        if not upload_successful:
            raise Exception(f"Failed to upload file after {self.max_retries} attempts")


    def list_files(self, name, parent_folder_id='root'):
        '''heler method to list file/folders by name within a parent folder.'''
        url = f"https://www.googleapis.com/drive/v3/files?q=name='{name}' and '{parent_folder_id}' in parents and trashed=false&fields=files(kind,id,name,size,mimeType)"
        response = requests.get(url, headers=self.get_headers())
        response.raise_for_status()
        return response.json().get('files', [])
    
    def delete_file(self, file_id):
        '''delete a file from google drive by id.'''
        url = f'https://www.googleapis.com/drive/v3/files/{file_id}'
        response = requests.delete(url, headers=self.get_headers())
        response.raise_for_status()
        print(f"deleted file with id: {file_id}")

    def create_folder(self, folder_name, parent_folder_id='root'):
        """Create a new folder in Google Drive."""
        existing_folders = self.list_files(folder_name, parent_folder_id)
        if existing_folders:
            folder_id = existing_folders[0]['id']
            print(f"Folder '{folder_name}' already exists with ID: {folder_id}")
            return folder_id
        
        folder_metadata = {
            'name': folder_name,
            'mimeType': self.folder_mime_type,
            'parents': [parent_folder_id]
        }

        url = 'https://www.googleapis.com/drive/v3/files'

        response = requests.post(url, headers=self.get_headers(), json=folder_metadata)
        response.raise_for_status()

        folder_id = response.json()['id']
        print(f"Created folder: {folder_name} with ID: {folder_id}")
        return folder_id

    def upload_file(self, file_path, folder_id='root'):
        """Upload a single file to Google Drive with automatic chunk size adjustment."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist")

        file_name = sanitizer_names(filename=os.path.basename(file_path))
        mime_type, _ = mimetypes.guess_type(file_path)
        file_size = os.path.getsize(file_path)

        #chekc if the file already exists in the folder
        existing_files = self.list_files(file_name, folder_id)
        #print(existing_files)
        if existing_files:
            drive_file = existing_files[0] #kind
            drive_file_id = drive_file['id'] #file id
            drive_file_size = int(drive_file['size']) #file_size

            if drive_file_size == file_size:
                print(f"File '{file_name}' already exists and matches in size.")
                return
            else:
                print(f"file '{file_name}' exists but size differs. Deleting and re-uploading.")
                self.delete_file(drive_file_id)

        # File metadata
        file_metadata = {
            'name': file_name,
            'mimeType': mime_type,
            'parents' : [folder_id]
        }

        # Media upload
        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)

        # Build the request URL
        upload_url = f'{self.base_url}?uploadType=resumable'
        response = requests.post(upload_url, headers=self.get_headers(), json=file_metadata)
        response.raise_for_status()

        # Extract the upload URL from the response
        upload_url = response.headers['Location']

        # Upload file content
        self._resumable_upload(upload_url, file_path)

    def upload_folder(self, folder_path, parent_folder_id='root'):
        """Upload an entire folder to Google Drive, preserving the folder structure."""
        # Step 1: Create folder structure on Google Drive and map local paths to Google Drive folder IDs
        folder_map = {}
        
        # Create the main folder on Google Drive
        folder_name = os.path.basename(folder_path)
        folder_id = self.create_folder(folder_name, parent_folder_id)
        folder_map[folder_path] = folder_id

        # Walk through the local directory to create folder structure on Google Drive
        for root, dirs, files in os.walk(folder_path):
            # Compute the parent folder ID in Google Drive for the current directory
            parent_folder_id = folder_map.get(root, folder_id)
            
            # Create subdirectories on Google Drive and update the folder_map
            for dir_name in dirs:
                current_folder_path = os.path.join(root, dir_name)
                if current_folder_path not in folder_map:
                    current_folder_id = self.create_folder(dir_name, parent_folder_id)
                    folder_map[current_folder_path] = current_folder_id

        # Step 2: Upload files into the corresponding Google Drive folders
        with ThreadPoolExecutor(max_workers=self.max_uploader_count) as executor:
            #store  futures for asunc exec of  uploader
            futures = []

            for root, dirs, files in os.walk(folder_path):
                # Compute the parent folder ID for files in this directory
                parent_folder_id = folder_map.get(root, folder_id)

                # Upload all files in the current directory
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    #SUBMIT FILE UPLOAD TASKS TO  BE EXECUTED CONC
                    futures.append(executor.submit(self.upload_file, file_path, parent_folder_id))
            
            #wait for all uploads to complete
            for future in as_completed(futures):
                try:
                    future.result() #raise exeptions
                except Exception as e:
                    print(f'Error uploading file: {e}')

        print(f"Uploaded folder: {folder_name} to Google Drive")
