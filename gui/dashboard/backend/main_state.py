import os
from typing import List, Optional
import asyncio

import reflex as rx

from ..backend.utils import request_to_kalavai_core


ACCESS_KEY = os.getenv("ACCESS_KEY", None)


class MainState(rx.State):
    """The state class."""

    is_connected: bool = False
    is_logged_in: bool = False
    ##

    username: str = ""
    password: str = ""
    is_loading: bool = False
    login_error_message: str = ""
    user_key: str = ""

    @rx.event
    def update_username(self, username: str):
        self.username = username
    
    @rx.event
    def update_password(self, password: str):
        self.password = password
    
    @rx.event
    def update_connected(self, state: bool):
        self.is_connected = state

    @rx.event(background=True)
    async def load_state(self):
        async with self:
            self.is_loading = True
        
        async with self:
            # is computer connected to a pool?
            try:
                self.is_connected = request_to_kalavai_core(
                    method="get",
                    endpoint="is_connected")
            except Exception as e:
                return rx.toast.error(f"Missing ACCESS_KEY?\n{e}", position="top-center")

        async with self:
            # is the user authenticated?
            # user = request_to_kalavai_core(
            #     method="get",
            #     endpoint="load_user_session")
            # self.is_logged_in = user is not None
            if ACCESS_KEY is None:
                self.is_logged_in = True
            self.is_loading = False

    @rx.event(background=True)
    async def connect(self):
        async with self:
            await asyncio.sleep(3)
            self.is_connected = True
    
    @rx.event(background=True)
    async def authorize(self, access_key: str):
        """Authorize user with key.
        
        Args:
            access_key: The configured access key from environment
            user_key: The key entered by the user
        """
        async with self:
            self.is_loading = True
            self.login_error_message = ""
        
        # Check if user key matches ACCESS_KEY
        async with self:
            self.is_logged_in = self.user_key == access_key
            if self.is_logged_in:
                self.login_error_message = ""
            else:
                self.login_error_message = "Invalid user key"
                
            self.is_loading = False

        # async with self:
        #     user = request_to_kalavai_core(
        #         method="get",
        #         endpoint="authenticate_user",
        #         params={"user_id": self.username})
        #     if "error" in user:
        #         self.login_error_message = user["error"]
        #     else:
        #         self.is_logged_in = True
        #     self.is_loading = False
    
    @rx.event(background=True)
    async def signout(self):
        async with self:
            # request_to_kalavai_core(
            #     method="get",
            #     endpoint="user_logout")
            self.is_logged_in = False
            self.login_error_message = ""
            return rx.redirect("/")

    def update_user_key(self, value: str):
        """Update the user key."""
        self.user_key = value
