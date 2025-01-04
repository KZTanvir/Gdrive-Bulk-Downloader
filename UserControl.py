import os, json, requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from DriveLoader.Client_Credentials import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, USER_AUTH_FILE, TOKEN_FILE

class UserControl:
    def __init__(self):
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.redirect_uri = REDIRECT_URI
        self.current_email = None

    def save_to_file(self, file_path, data):
        """Helper function to save data to a JSON file."""
        with open(file_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)

    def load_from_file(self, file_path):
        """Helper function to load data from a JSON file."""
        if os.path.exists(file_path):
            with open(file_path, 'r') as json_file:
                return json.load(json_file)
        return {}

    def get_user_info(self, access_token):
        """Retrieve user information using the Google UserInfo API."""
        userinfo_url = "https://www.googleapis.com/drive/v3/about/?fields=user"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(userinfo_url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError("Failed to fetch user information from Google UserInfo API.")
        
    def generate_user_auth(self, scopes=['https://www.googleapis.com/auth/drive']):
        """Generate a new user auth entry and store refresh token in user_auth.json."""
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri],
                }
            },
            scopes
        )
        creds = flow.run_local_server(port=0)
        #print(creds.to_json()) for debug
        # Retrieve email using the UserInfo API
        user_info = self.get_user_info(creds.token)['user']
        user_email = user_info['emailAddress']

        if user_email:
            user_auth_data = self.load_from_file(USER_AUTH_FILE)
            user_auth_data[user_email] = {'refresh_token': creds.refresh_token}
            self.save_to_file(USER_AUTH_FILE, user_auth_data)
            print(f"Saved credentials for {user_email} to {USER_AUTH_FILE}")
        else:
            raise ValueError("Could not retrieve email from UserInfo API response.")

    def select_user_email(self):
        """Prompt the user to select an email from the available users."""
        user_auth_data = self.load_from_file(USER_AUTH_FILE)
        if not user_auth_data:
            print(f"{USER_AUTH_FILE} is empty or missing.")
            auth_choice = input("Do you want to add account?(y/n): ").lower()
            if auth_choice == 'y':
                self.generate_user_auth()
            exit()

        emails = list(user_auth_data.keys())
        if not emails:
            raise ValueError("No users available in the user_auth.json file.")

        if len(emails) == 1:
            print(f"Automatically selected user: {emails[0]}")
            return emails[0]

        # Prompt user to select an email if multiple users exist
        print("Available users:")
        for i, email in enumerate(emails):
            print(f"{i + 1}. {email}")
        choice = int(input("Select user by number: ")) - 1

        if 0 <= choice < len(emails):
            selected_email = emails[choice]
            print(f"Selected user: {selected_email}")
            return selected_email
        else:
            raise ValueError("Invalid selection.")
    
    def get_direct_access_token(self, email=None, scopes=['https://www.googleapis.com/auth/drive']):
        '''Retrieve or refresh access token for the given user'''
        try:
            access_token_data = self.load_from_file(TOKEN_FILE)
            if not email:
                first_key = next(iter(access_token_data))
                print(f"Default First Email Selected: {first_key}")
                access_token = access_token_data[first_key].get('access_token')  ##needed to be patched
            else:
                access_token = access_token_data[email]['access_token'] 
            # Check access token validity
            if access_token:
                try:
                    user_info = self.get_user_info(access_token=access_token)
                    if user_info:
                        return access_token
                except ValueError:
                    print("Invalid access token. Refreshing...")
            
            return self.get_user_access_token()

        except:
            print("Re Generating user access token....")
            return self.get_user_access_token()

    def get_user_access_token(self, user_email=None, scopes=['https://www.googleapis.com/auth/drive']):
        """Retrieve or refresh access token for the given user."""
        if user_email is None:
            user_email = self.select_user_email()
            self.current_email = user_email

        user_auth_data = self.load_from_file(USER_AUTH_FILE)
        if user_email not in user_auth_data:
            raise ValueError(f"No credentials found for {user_email} in {USER_AUTH_FILE}.")

        refresh_token = user_auth_data[user_email].get('refresh_token')
        if not refresh_token:
            raise ValueError(f"Refresh token for {user_email} is missing.")

        creds = Credentials(
            None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret
        )

        # Refresh the token if expired
        if not creds.valid:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error during token refresh: {e}")
                self.generate_user_auth()
                print("User Authenticated again!")
                return self.get_user_access_token(user_email=user_email) 

        # Save the access token to tokens.json
        tokens_data = self.load_from_file(TOKEN_FILE)
        tokens_data[user_email] = {"access_token": creds.token}
        self.save_to_file(TOKEN_FILE, tokens_data)

        print(f"Access token for {user_email} saved to {TOKEN_FILE}")
        return creds.token

    def revoke_token(self, user_email=None):
        """Revoke the user's access and refresh tokens and delete them from the storage."""
        if user_email is None:
            user_email = self.select_user_email()

        user_auth_data = self.load_from_file(USER_AUTH_FILE)
        if user_email not in user_auth_data:
            raise ValueError(f"No credentials found for {user_email} in {USER_AUTH_FILE}.")
        
        refresh_token = user_auth_data[user_email].get('refresh_token')
        if not refresh_token:
            raise ValueError(f"No refresh token found for {user_email}.")

        revoke_url = "https://oauth2.googleapis.com/revoke"
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        response = requests.post(revoke_url, data={'token': refresh_token}, headers=headers)

        if response.status_code == 200:
            print(f"Token for {user_email} has been successfully revoked.")
            del user_auth_data[user_email]
            self.save_to_file(USER_AUTH_FILE, user_auth_data)

            # Also remove the token for this user from tokens.json
            tokens_data = self.load_from_file(TOKEN_FILE)
            if user_email in tokens_data:
                del tokens_data[user_email]
                self.save_to_file(TOKEN_FILE, tokens_data)
                print(f"Deleted token entry for {user_email} from {TOKEN_FILE}.")
                if self.current_email == user_email:
                    print('Restart CLI for reinstate the auth token. [CURRENT USER DELETED]')
                    exit()
        else:
            raise ValueError(f"Failed to revoke token for {user_email}. HTTP status: {response.status_code}")