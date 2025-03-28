import os
import json
from datetime import datetime
from typing import Optional, Dict, Any
from supabase import create_client, Client
from kalavai_client.auth_interface import AuthInterface

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://vxnmtvagfrqvvnmumswk.supabase.co")
#SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ4bm10dmFnZnJxdnZubXVtc3drIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI0OTYwNDEsImV4cCI6MjA1ODA3MjA0MX0.7dRlh1o_sihgOXZs3idz88MZst_HXUw62dSpimfJlXM")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ4bm10dmFnZnJxdnZubXVtc3drIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MjQ5NjA0MSwiZXhwIjoyMDU4MDcyMDQxfQ.xbIQrG02vfez9vxox8hs9MMlpIKq3BC24L-uLnOZp38")

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class SupabaseAuthClient(AuthInterface):
    def __init__(self, user_cookie_file: str = "supabase_user.json"):
        """Initialize the Supabase auth client.
        
        Args:
            user_cookie: Path to store user session data
        """
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.user_cookie = user_cookie_file
        self._user: Optional[Any] = None
        self._load_user_session()  # Try to load existing session on init

    def login(self, username: str, password: str) -> Optional[Any]:
        """Login with email and password.
        
        Args:
            username: User's email address
            password: User's password
            
        Returns:
            User object if successful, None otherwise
        """
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": username,
                "password": password
            })
            self._user = response.user
            self._save_user_session()
            return self._user
        except Exception as e:
            print(f"Login failed: {str(e)}")
            return None

    def logout(self) -> bool:
        """Logout the current user and clear local session.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.supabase.auth.sign_out()
            self._user = None
            self._clear_user_session()
            return True
        except Exception as e:
            print(f"Logout failed: {str(e)}")
            return False

    def is_logged_in(self) -> bool:
        """Check if user is currently logged in.
        
        Returns:
            bool: True if logged in, False otherwise
        """
        return self._user is not None

    def load_user_session(self) -> Optional[Any]:
        """Load user session from local storage.
        
        Returns:
            User object if session exists, None otherwise
        """
        try:
            if not os.path.exists(self.user_cookie):
                return None
                
            with open(self.user_cookie, "r") as f:
                user_data = json.load(f)
                
            # Set the user session in Supabase client
            self.supabase.auth.set_session({
                "access_token": user_data["access_token"],
                "refresh_token": user_data["refresh_token"]
            })
            
            # Get fresh user data
            self._user = self.supabase.auth.get_user()
            return self._user
            
        except Exception as e:
            print(f"Failed to load user session: {str(e)}")
            self._clear_user_session()
            return None

    def get_user_id(self) -> Optional[str]:
        """Get user ID from local session.
        
        Returns:
            str: User ID if logged in, None otherwise
        """
        if not self._user:
            return None
        return getattr(self._user, "user_metadata", {}).get("user_id", None)
    
    def get_user_key(self) -> Optional[str]:
        """Get user ID from local session.
        
        Returns:
            str: User ID if logged in, None otherwise
        """
        if not self._user:
            return None
        return getattr(self._user, "id", None)

    def sign_up(self, username: str, password: str, user_id: str) -> Optional[Any]:
        """Create a new user account.
        
        Args:
            username: User's email address
            password: User's password
            user_id: User's user_id
            
        Returns:
            User object if successful, None otherwise
        """
        try:
            response = self.supabase.auth.sign_up({
                "email": username,
                "password": password,
                "options": {
                    "data": {
                        "user_id": user_id,
                        "confirmation_sent_at": datetime.now().isoformat()
                    }
                }
            })
            self._user = response.user
            self._save_user_session()
            return self._user
        except Exception as e:
            print(f"Sign up failed: {str(e)}")
            return None

    def get_user_data(self) -> Optional[Dict[str, Any]]:
        """Get user data as dictionary.
        
        Returns:
            Dict containing user data if logged in, None otherwise
        """
        if not self._user:
            return None
            
        return {
            "id": getattr(self._user, "id", None),
            "email": getattr(self._user, "email", None),
            "user_metadata": getattr(self._user, "user_metadata", {}),
            "created_at": getattr(self._user, "created_at", None),
            "last_sign_in_at": getattr(self._user, "last_sign_in_at", None)
        }

    def _save_user_session(self) -> None:
        """Save user session to local file."""
        if not self._user:
            return
            
        user_data = {
            "id": getattr(self._user, "id", None),
            "email": getattr(self._user, "email", None),
            "access_token": getattr(self._user, "access_token", None),
            "refresh_token": getattr(self._user, "refresh_token", None),
            "user_metadata": getattr(self._user, "user_metadata", {}),
            "created_at": getattr(self._user, "created_at", None),
            "last_sign_in_at": getattr(self._user, "last_sign_in_at", None)
        }
        
        with open(self.user_cookie, "w") as f:
            json.dump(user_data, f, cls=DateTimeEncoder)

    def _clear_user_session(self) -> None:
        """Clear local user session file."""
        try:
            if os.path.exists(self.user_cookie):
                os.remove(self.user_cookie)
        except Exception as e:
            print(f"Failed to clear user session: {str(e)}")

    def _load_user_session(self) -> None:
        """Load user session from local file."""
        try:
            if not os.path.exists(self.user_cookie):
                return
                
            with open(self.user_cookie, "r") as f:
                user_data = json.load(f)
                
            # Set the user session in Supabase client
            self.supabase.auth.set_session({
                "access_token": user_data["access_token"],
                "refresh_token": user_data["refresh_token"]
            })
            
            # Get fresh user data
            self._user = self.supabase.auth.get_user()
            
        except Exception as e:
            print(f"Failed to load user session: {str(e)}")
            self._clear_user_session()

# Example usage
if __name__ == "__main__":
    # Initialize client
    auth = SupabaseAuthClient(
        user_cookie_file="supabase_user.json"
    )
    # With a service key, on server, get the user given an id
    # this is useful to get the user_id of the client and validate namespace
    print(
        auth.supabase.auth.admin.get_user_by_id("91bdd3c9-8372-4944-99ec-5b3cec8f6456")
    )
    exit()

    # Example of creating a new usern
    # new_user = auth.sign_up(
    #     username="test@kalavai.net",
    #     password="secure_password123",
    #     user_id="testuser"
    # )
    # print(f"New user: {new_user}")
    # exit()
    # Example of creating a new user
    new_user = auth.login(
        username="test@kalavai.net",
        password="secure_password123",
    )
    
    if new_user:
        print("User created successfully!")
        print(f"User ID: {auth.get_user_id()}")
        print(f"User Key: {auth.get_user_key()}")
    else:
        print("Failed to create user!") 