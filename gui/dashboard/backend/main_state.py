from typing import List
import asyncio

import reflex as rx

from kalavai_client.core import (
    authenticate_user,
    load_user_session,
    user_logout,
    is_connected,
    attach_to_pool,
    stop_pool
)


class MainState(rx.State):
    """The state class."""

    is_connected: bool = False
    is_logged_in: bool = False
    ##

    username: str = ""
    password: str = ""
    token: str = ""
    logged_user: str = ""
    is_loading: bool = False
    login_error_message: str = ""
    pool_error_message: str = ""

    @rx.event(background=True)
    async def load_state(self):
        async with self:
            self.is_loading = True
        
        async with self:
            # is computer connected to a pool?
            self.is_connected = is_connected()

        async with self:
            # is the user authenticated?
            user = load_user_session()
            self.is_logged_in = user is not None
            self.logged_user = user["username"] if user is not None else ""
            self.is_loading = False

    @rx.event(background=True)
    async def connect(self):
        async with self:
            await asyncio.sleep(3)
            self.is_connected = True
    
    @rx.event(background=True)
    async def attach(self):
        async with self:
            self.is_loading = True
            self.pool_error_message = ""

        result = attach_to_pool(token=self.token)

        async with self:
            if "error" in result:
                self.pool_error_message = result["error"]
            else:            
                self.is_connected = True
            self.is_loading = False
    
    @rx.event(background=True)
    async def stop(self):
        async with self:
            self.is_loading = True
        
        async with self:
            result = stop_pool()
            self.is_connected = False
            self.is_loading = False
        
    @rx.event
    def update_username(self, username: str):
        self.username = username
    
    @rx.event
    def update_password(self, password: str):
        self.password = password
    
    @rx.event
    def update_token(self, token: str):
        self.token = token
    
    @rx.event(background=True)
    async def signin(self):
        async with self:
            self.is_loading = True
            self.login_error_message = ""

        async with self:
            user = authenticate_user(username=self.username, password=self.password)
            if "error" in user:
                self.login_error_message = user["error"]
            else:
                self.is_logged_in = True
                self.logged_user = user["username"]
            self.is_loading = False
    
    @rx.event(background=True)
    async def signout(self):
        async with self:
            user_logout()
            self.is_logged_in = False
            self.login_error_message = ""
