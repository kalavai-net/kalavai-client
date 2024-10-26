import os
import pickle

import anvil.server
import anvil.users


AUTH_UPLINK_KEY = os.getenv("ANVIL_UPLINK_KEY", "client_AOPKTWK227ZV3R4ENTMOQRIY-ADMVMYW5OIRPH75P")

class KalavaiAuthClient:
    def __init__(self, user_cookie_file=None):
        anvil.server.connect(AUTH_UPLINK_KEY)
        self.user_cookie_file = user_cookie_file
        self.load_user_session()

    def login(self, username, password):
        try:
            user = anvil.users.login_with_email(username, password, remember=True)
        except:
            return None
        
        if self.user_cookie_file:
            with open(self.user_cookie_file, "wb") as f:
                    pickle.dump(user, f)  
        return user

    def logout(self):
        anvil.users.logout()
        try:
            os.remove(self.user_cookie_file)
        except:
            pass
    
    def is_logged_in(self):
        user = self.load_user_session()
        return user is not None

    def load_user_session(self):
        user = anvil.users.get_user()
        if user:
            return user
        try:
            with open(self.user_cookie_file, "rb") as f:
                user = pickle.load(f)
                return user
        except:
            return None
        
    def call_function(self, fn, *args):
        return anvil.server.call(
            fn,
            *args
        )

    

if __name__ == "__main__":
    auth = KalavaiAuthClient(
        user_cookie_file="here.pickle"
    )
    user = auth.load_user_session()
    if not user:
        user = auth.login(username="carlos@kalavai.net", password="wrong_pass")

    if user is None:
        print("Failed to login")
    else:
        print(user)