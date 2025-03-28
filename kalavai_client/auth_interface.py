from abc import ABC, abstractmethod
from typing import Optional, Any

class AuthInterface(ABC):
    """Base interface for authentication clients."""
    
    @abstractmethod
    def login(self, username: str, password: str) -> Optional[Any]:
        """Login user and store session locally.
        
        Args:
            username: User's username/email
            password: User's password
            
        Returns:
            User object if successful, None otherwise
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    @abstractmethod
    def logout(self) -> bool:
        """Logout user and clear local session.
        
        Returns:
            bool: True if successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    @abstractmethod
    def is_logged_in(self) -> bool:
        """Check if user is currently logged in.
        
        Returns:
            bool: True if logged in, False otherwise
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    @abstractmethod
    def load_user_session(self) -> Optional[Any]:
        """Load user session from local storage.
        
        Returns:
            User object if session exists, None otherwise
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    @abstractmethod
    def get_user_id(self) -> Optional[str]:
        """Get user ID from local session.
        
        Returns:
            str: User ID if logged in, None otherwise
        """
        raise NotImplementedError("Subclasses must implement this method") 