from UserControl import UserControl
from DriveLoader.Drive_Browser import DriveBrowser
from functions import link_to_id, clear_console

# Setup logging


class GDriveManager:
    def __init__(self):
        self.ucontrol = UserControl()
        self.access_token = self.ucontrol.get_direct_access_token()

        self.drivebrowser = DriveBrowser(access_token=self.access_token)

    def get_download_folder(self):
        """Prompt user for the download folder name."""
        folder_name = input("Enter Download Folder Name: ").strip()
        if folder_name:
            self.drivebrowser.downloader.downloader_path = folder_name
        else:
            print("No folder name entered, default will be used.")

    def enter_bulk_links(self):
        """Prompt user to enter multiple Google Drive links."""
        links = []
        try:
            link_count = int(input("Enter the number of Google Drive links: "))
            for i in range(link_count):
                link = input(f"Enter Drive Link [{i + 1}]: ").strip()
                links.append(link)
        except ValueError:
            print("Invalid input. Please enter a valid number.")
            return self.enter_bulk_links()
        return links

    def get_folder_id(self, message="Enter Drive Folder Link"):
        """Prompt user to input a Google Drive folder link and extract the ID."""
        link = input(f"{message}: ").strip()
        return link_to_id(link) if link else None

    def download_folder(self):
        """Download a single Google Drive folder."""
        folder_id = self.get_folder_id()
        if folder_id:
            try:
                self.drivebrowser.browse_folder(parent_folder_id=folder_id)
            except Exception as e:
                print(f"Error downloading folder: {e}")

    def download_file(self):
        """Download a single Google Drive file."""
        file_id = self.get_folder_id("Enter Drive File Link")
        if file_id:
            try:
                self.drivebrowser.downloader.root_folder_id = file_id
                self.drivebrowser.downloader.download_single_file()
            except Exception as e:
                print(f"Error downloading file: {e}")

    def bulk_download_links(self):
        """Download multiple Google Drive links."""
        links = self.enter_bulk_links()
        for link in links:
            try:
                folder_id = link_to_id(link)
                print(f"Extracted ID: {folder_id} from link: {link}")
                self.drivebrowser.downloader.root_folder_id = folder_id
                self.drivebrowser.downloader.download_folder()
            except Exception as e:
                print(f"Error with link {link}: {e}")

    def display_menu(self):
        """Display the menu and return the user's choice."""

        #clear_console()
        menu = """
        ------------------------ Gdrive Manager ------------------------
        Options:

        User Access [GDrive]
        -> 1. Select Users
        -> 2. Add/Authenticate Account
        -> 0. Remove/Revoke Account
        
        User Drive [GDrive] [UPLOAD/DOWNLOAD]
        -> 3. Browse Main Drive
        
        Download [GDrive] [CUSTOM]
        -> 4. Set Max Concurrent Downloads
        -> 5. Bulk GDrive Links Download
        -> 6. Single Folder Download
        -> 7. Single File Download
        -> 8. Set Download Folder Name

        9. About
        10. Exit
        """
        print(menu)

        try:
            return int(input("Select an option (1-10): "))
        except ValueError:
            print("Invalid option selected.")
            return self.display_menu()

    def about(self):
        clear_console()
        """Display information about the tool."""
        print("GDrive Manager - A tool for managing Google Drive files and folders.")
        print("Developed by Kamruzzaman Tanvir - For learning purposes.")
        print("\n\nUserInformation: ")
        user_information = self.ucontrol.get_user_info(self.ucontrol.get_direct_access_token(email=self.ucontrol.current_email))
        print(f"Type: {user_information['user']['kind']}")
        print(f"Name: {user_information['user']['displayName']}")
        print(f"Email Address: {user_information['user']['emailAddress']}")
        #Patch Note: add user information details to load then use its email for this app to work
        input("\nEnter to go back.")
        
        
    def run(self):
        """Main program loop."""
        while True:
            option = self.display_menu()

            if option == 1:
                self.drivebrowser.token_reset(self.ucontrol.get_user_access_token())
            elif option == 2:
                self.ucontrol.generate_user_auth()
            elif option == 3:
                clear_console()
                self.drivebrowser.browse_folder()
            elif option == 0:
                self.ucontrol.revoke_token()
            elif option == 4:
                download_count = int(input("Enter Conc Download: "))
                if download_count:
                    self.drivebrowser.downloader.max_downloader_count = download_count
                else:
                    print('Something Went Wrong! Try again.') 
            elif option == 5:
                self.bulk_download_links()
            elif option == 6:
                self.download_folder()
            elif option == 7:
                self.download_file()
            elif option == 8:
                self.get_download_folder()
            elif option == 9:
                self.about()
            elif option == 10:
                print("Exiting program.")
                break
            else:
                print("Invalid option. Please try again.")
            clear_console()

if __name__ == "__main__":
    clear_console()
    GDriveManager().run()
