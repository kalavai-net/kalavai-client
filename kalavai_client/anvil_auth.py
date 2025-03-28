import os
import pickle
from typing import Optional, Any
import anvil.server
import anvil.users
from kalavai_client.auth_interface import AuthInterface

AUTH_UPLINK_KEY = os.getenv("ANVIL_UPLINK_KEY", "client_AOPKTWK227ZV3R4ENTMOQRIY-ADMVMYW5OIRPH75P")

class KalavaiAuthClient(AuthInterface):
    def __init__(self, user_cookie_file=None):
        """Initialize the Kalavai auth client.
        
        Args:
            user_cookie_file: Path to store user session data
        """
        anvil.server.connect(AUTH_UPLINK_KEY, quiet=True)
        self.user_cookie_file = user_cookie_file
        self._user: Optional[Any] = None
        self.load_user_session()

    def login(self, username: str, password: str) -> Optional[Any]:
        """Login with username and password.
        
        Args:
            username: User's username/email
            password: User's password
            
        Returns:
            User object if successful, None otherwise
        """
        try:
            self._user = anvil.users.login_with_email(username, password, remember=True)
            if self._user and self.user_cookie_file:
                with open(self.user_cookie_file, "wb") as f:
                    pickle.dump(self._user, f)
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
            anvil.users.logout()
            self._user = None
            if self.user_cookie_file and os.path.exists(self.user_cookie_file):
                os.remove(self.user_cookie_file)
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
            # First try to get current session
            self._user = anvil.users.get_user()
            if self._user:
                return self._user
                
            # If no current session, try to load from file
            if self.user_cookie_file and os.path.exists(self.user_cookie_file):
                with open(self.user_cookie_file, "rb") as f:
                    self._user = pickle.load(f)
                return self._user
                
            return None
        except Exception as e:
            print(f"Failed to load user session: {str(e)}")
            return None

    def get_user_id(self) -> Optional[str]:
        """Get user ID from local session.
        
        Returns:
            str: User ID if logged in, None otherwise
        """
        if not self._user:
            return None
        return self._user.get("username", None)
    
    def get_user_key(self) -> Optional[str]:
        """Get user ID from local session.
        
        Returns:
            str: User ID if logged in, None otherwise
        """
        if not self._user:
            return None
        return self._user.get("api_key", None)

    def call_function(self, fn, *args):
        """Call a server function.
        
        Args:
            fn: Function name to call
            *args: Arguments to pass to the function
            
        Returns:
            Result of the function call
        """
        return anvil.server.call(fn, *args)

if __name__ == "__main__":
    auth = KalavaiAuthClient(
        user_cookie_file="here.pickle"
    )
    
    # Try to load existing session
    user = auth.load_user_session()
    if not user:
        # If no session, try to login
        user = auth.login(username="carlos@kalavai.net", password="password")

    if user is None:
        print("Failed to login")
    else:
        print(f"Logged in as: {auth.get_user_id()}")
        print(f"User Key: {auth.get_user_key()}")