import requests
from UserControl import UserControl
from DriveLoader.Gdrive_Downloader import Gdrive_Bulker
from DriveLoader.Gdrive_Uploader import GdriveUploader
from functions import clear_console

class DriveBrowser:
    def __init__(self, access_token):
        self.access_token = access_token

        #object encap
        self.downloader = Gdrive_Bulker(access_token=self.access_token) #downloader object
        self.uploader = GdriveUploader(access_token=self.access_token) #uploader object
        
        self.folder_history = []  # To keep track of folder navigation
    
    def token_reset(self, access_token):
        self.access_token = access_token
        #re ref
        self.downloader.access_token = self.access_token
        self.uploader.access_token = self.access_token

    def get_list_files(self, parent_folder_id='root'):
        """Helper method to list files/folders by name within a parent folder."""
        try:
            url = f"https://www.googleapis.com/drive/v3/files?q='{parent_folder_id}' in parents and trashed=false&fields=files(kind,id,name,size,mimeType)"
            response = requests.get(url, headers={'Authorization': f'Bearer {self.access_token}'})
            response.raise_for_status()
            return response.json().get('files', [])
        except Exception as e:
            print(f"Error: {e}")

    def display_files(self, files):
        """Display files/folders in a structured order, with folders first."""
        folders = []
        other_files = []
        for file in files:
            if file['mimeType'] == "application/vnd.google-apps.folder":
                folders.append(file)
            else:
                other_files.append(file)
        
        # Combine folders and other files into a single list
        combined_files = folders + other_files

        # Number the files for selection and display their details
        for i, file in enumerate(combined_files):
            file_type = "Folder" if file['mimeType'] == "application/vnd.google-apps.folder" else file['mimeType']
            file_size = f"{round(int(file['size']) / (1024 * 1024), 2)} MB" if file_type != "Folder" and 'size' in file else "N/A" if file_type != "Folder" else ""

            print(f"{i+1}. {file['name']} (Type: {file_type}, Size: {file_size})")

        return folders, combined_files  # Returning folders separately for browsing

    def browse_folder(self, parent_folder_id='root'):
        """Function to allow users to browse into folders."""
        self.folder_history.append(parent_folder_id)  # Add the current folder to history

        while True:
            # Get and display the list of files/folders
            files = self.get_list_files(parent_folder_id)
            folders, combined_files = self.display_files(files)
            
            # Ask the user for an action
            print("\nOptions: [Enter the number to navigate into folder]")
            print("[v<number>] to view file details, [cf] to create a folder")
            print("[d<number>] to download a file, [dcf<number>] to download current folder")
            print("[usf<number>] to upload a single file, [u] to upload a folder")
            print("[del<number>] to delete a file/folder")
            print("'b' to go back, 'q' to quit")

            choice = input("\nYour choice: ").strip()
            #clear_console()

            if choice.lower() == 'q':
                print("Exiting...")
                break  # Exit the browser
            elif choice.lower() == 'b':
                if len(self.folder_history) > 1:
                    self.folder_history.pop()  # Go back to the previous folder
                    parent_folder_id = self.folder_history[-1]
                    clear_console()
                    print(f"Going back to parent folder...\n")
                else:
                    print("\nYou're already in the root folder.")
            elif choice.startswith('del'):  # Delete a folder
                clear_console()
                try:
                    choice_num = int(choice[3:])  # Get the folder number
                    selected_choice = combined_files[choice_num - 1]
                    if selected_choice['mimeType'] == "application/vnd.google-apps.folder":
                        self.delete_folder(selected_choice['id'])  # Delete the selected folder
                    else:
                        self.delete_folder(selected_choice['id'], file=True)
                
                except (IndexError, ValueError):
                    print("\nInvalid folder number.")

            elif choice.startswith('v'):  # View file details
                try:
                    choice_num = int(choice[1:])
                    selected_file = combined_files[choice_num - 1]
                    self.view_file_details(selected_file)
                    input("Enter To go back.")
                except (IndexError, ValueError):
                    print("\nInvalid file number.")
                clear_console()
            elif choice.startswith('d'):  # Download file
                if choice.startswith('dcf'):
                    try:
                        folder_name = input('Enter Folder Name to create and download: ')
                        self.downloader.download_folder(parent_folder_id, folder_name)
                    except (IndexError, ValueError):
                        print("\nInvalid file number.")
                else:
                    try:
                        choice_num = int(choice[1:])
                        selected_file = combined_files[choice_num - 1]
                        self.download_file_folder(selected_file)
                    except (IndexError, ValueError):
                        print("\nInvalid file number.")
            elif choice.lower() == 'u':  # Upload folder
                try:
                    self.upload_file_folder(parent_folder_id)
                except Exception as e:
                    print(f'Someting went wrong: {e}')
            
            elif choice.lower() == 'usf':
                try:
                    self.upload_file_folder(parent_folder_id, folder=False)
                except Exception as e:
                    print(f'Something went wrong: {e}')
            elif choice.startswith('cf'):  # Upload folder
                try:
                    self.create_folder(parent_folder_id)
                except Exception as e:
                    print(f'Someting went wrong: {e}')
            else:
                try:
                    choice_num = int(choice)
                    selected_file = combined_files[choice_num - 1]
                    if selected_file['mimeType'] == "application/vnd.google-apps.folder":
                        # Browse inside the selected folder
                        print(f"\nBrowsing inside folder: {selected_file['name']}\n")
                        parent_folder_id = selected_file['id']  # Update the parent folder ID to selected folder ID
                        self.folder_history.append(parent_folder_id)
                        clear_console()
                    else:
                        clear_console()
                        print(f"\n{selected_file['name']} is not a folder. Please select a valid folder.\n")
                except (IndexError, ValueError):
                    clear_console()
                    print("\nInvalid choice. Please select a valid folder number.\n")

    def view_file_details(self, file):
        """Display detailed information about a file."""
        print(f"\n--- File Details ---")
        print(f"Name: {file['name']}")
        print(f"ID: {file['id']}")
        print(f"Type: {file['mimeType']}")
        print(f"Size: {round(int(file.get('size')) / (1024 * 1024), 2)} MB" if file.get('size') else "Size: N/A")
        print(f"-------------------\n")


    def download_file_folder(self, file):
        """Simulate file download process (requires implementation)."""
        
        print(f"\nDownloading file: {file['name']} (ID: {file['id']})\n")
        if file['mimeType'] == "application/vnd.google-apps.folder": 
            self.downloader.download_folder(folder_id=file['id'], folder_path=file['name'])
        else:
            # downloader implementation
            self.downloader.download_single_file(file_id=file['id'])

    def upload_file_folder(self, folder_id, folder=True):
        """Placeholder for file upload functionality."""
        print(f"\nUploading file to folder ID: {folder_id}")
        # Prompt user for the file path and name
        path_dir = input(f"Enter the path to the {'Folder' if folder else 'File'} you want to upload: ").strip()
        if path_dir and folder:
            try:
                self.uploader.upload_folder(path_dir, folder_id)
            except Exception as e:
                print(f"error uploading folder: {e}")
        elif path_dir and not folder:
            try:
                self.uploader.upload_file(path_dir, folder_id)
            except Exception as e:
                print(f"error uploading file: {e}")
        else:
            print("No directory provided.")
    
    def create_folder(self, folder_id=None):
        """Create a folder in Google Drive."""
        folder_name = input("Enter Folder Name To Create: ").strip()
        if folder_name:
            try:
                folder_id = self.uploader.create_folder(folder_name, folder_id)
                print(f"Folder created with ID: {folder_id}")
            except Exception as e:
                print(f"Error creating folder: {e}")
        else:
            print("Enter correct folder id.")

    def delete_folder(self, folder_id, file=False):
        """Delete a folder from Google Drive."""
        try:
            url = f"https://www.googleapis.com/drive/v3/files/{folder_id}"
            response = requests.delete(url, headers={'Authorization': f'Bearer {self.access_token}'})
            response.raise_for_status()
            print(f"{'Folder' if not file else "File"} with ID: {folder_id} has been deleted successfully.")
        except Exception as e:
            print(f"Deletion Error: {e}")
