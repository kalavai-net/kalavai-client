from collections import defaultdict
import os
import json
from typing import Optional, Any

_USER_KEY = "id"


class KalavaiAuth():
    """Client for authenticating with the Kalavai watcher service."""
    
    def __init__(
        self,
        auth_service_url: str,
        auth_service_key: str,
        user_cookie_file: str
    ):
        """Initialize the Kalavai auth client.
        
        Args:
            user_cookie_file: Path to store user session data
        """
        self.user_cookie = user_cookie_file
        self.auth_service_url = auth_service_url
        self.auth_service_key = auth_service_key
        self.user_session = defaultdict(None)
        self.load_user_session()

    def save_auth(self, user_key: str) -> Optional[Any]:
        """Login with user key.
        
        Args:
            user_key: User's key (actual authentication key)
            
        Returns:
            User data if successful, None otherwise
        """
        # Store the user key as the session
        self.user_session[_USER_KEY] = user_key
        with open(self.user_cookie, "w") as f:
            json.dump(self.user_session, f)
            print(f"User key securely saved to {self.user_cookie}")

    def clear_auth(self) -> bool:
        """Clear the current user and local session.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.user_session = defaultdict(None)
        try:
            if os.path.exists(self.user_cookie):
                os.remove(self.user_cookie)
        except Exception as e:
            print(f"Failed to clear user session: {str(e)}")

    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated.
        
        Returns:
            bool: True if logged in, False otherwise
        """
        return self.user_session[_USER_KEY] is not None

    def load_user_session(self) -> Optional[Any]:
        """Load user session from local storage.
        
        Returns:
            User data if session exists, None otherwise
        """
        try:
            if not os.path.exists(self.user_cookie):
                return None
                
            with open(self.user_cookie, "r") as f:
                for key, value in json.load(f).items():
                    self.user_session[key] = value
            return self.user_session
            
        except Exception as e:
            print(f"Failed to load user session: {str(e)}")
            self.clear_auth()
            return None
    
    def get_user_id(self) -> Optional[Any]:
        """Get the user key from the user session.
        
        Returns:
            User key if session exists, None otherwise
        """
        try:
            return self.user_session[_USER_KEY]
        except:
            return None


# Example usage
if __name__ == "__main__":
    # Initialize client
    auth = KalavaiAuth(
        auth_service_url="http://localhost:8000",
        auth_service_key="example_auth_service_key",
        user_cookie_file="user_cookie.json"
    )
    
    # Example of logging in with a user key
    user_id = "example_user_id"
    auth.save_auth(user_id)
    
    print(f"User id: {auth.get_user_id()}")
