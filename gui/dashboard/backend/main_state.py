import os
from typing import List, Optional
import asyncio

import reflex as rx

from ..backend.utils import request_to_kalavai_core
from ..backend.utils import extract_number


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

    # user space values
    user_spaces: list[str] = []
    selected_user_space: str = None
    user_space_has_quota: bool = False

    # quota values
    used_cpu_quota: int = 0
    max_cpu_quota: int = 0
    used_gpu_quota: int = 0
    max_gpu_quota: int = 0
    used_memory_quota: int = 0
    max_memory_quota: int = 0

    @rx.var(cache=True)
    def cpu_quota_ratio(self) -> int:
        if self.max_cpu_quota == 0:
            return 0
        return int(float(self.used_cpu_quota)/float(self.max_cpu_quota)*100)
    
    @rx.var(cache=True)
    def gpu_quota_ratio(self) -> int:
        if self.max_gpu_quota == 0:
            return 0
        return int(float(self.used_gpu_quota)/float(self.max_gpu_quota)*100)
    
    @rx.var(cache=True)
    def memory_quota_ratio(self) -> int:
        if self.max_memory_quota == 0:
            return 0
        return int(float(self.used_memory_quota)/float(self.max_memory_quota)*100)
    
    @rx.event(background=False)
    async def set_user_space(self, user_space):
        """Set user space"""
        
        self.selected_user_space = user_space
        self.user_space_has_quota = False
        
        # load resource quota
        try:
            quota = request_to_kalavai_core(
                method="get",
                endpoint="get_user_space_quota",
                params={"space_name": self.selected_user_space})
        except Exception as e:
            return rx.toast.error(f"Missing ACCESS_KEY?\n{e}", position="top-center")
    
        # set resource quota values
        
        try:
            for q in quota:
                if "limits.cpu" in q["status"]["used"]:
                    self.used_cpu_quota = int(q["status"]["used"]["limits.cpu"])
                else:
                    self.used_cpu_quota = 0
                if "limits.memory" in q["status"]["used"]:
                    self.used_memory_quota = extract_number(q["status"]["used"]["limits.memory"])
                else:
                    self.used_memory_quota = 0
                if "limits.nvidia.com/gpu" in q["status"]["used"]:
                    self.used_gpu_quota = int(q["status"]["used"]["limits.nvidia.com/gpu"])
                else:
                    self.used_gpu_quota = 0
                self.max_cpu_quota = int(q["status"]["hard"]["limits.cpu"])
                self.max_gpu_quota = int(q["status"]["hard"]["limits.nvidia.com/gpu"])
                self.max_memory_quota = extract_number(q["status"]["hard"]["limits.memory"])
                self.user_space_has_quota = True
        except Exception as e:
            return rx.toast.error(f"Error when loading quotas: {e}", position="top-center")

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
            
            # load user spaces
            try:
                spaces = request_to_kalavai_core(
                    method="GET",
                    endpoint="get_available_user_spaces"
                )
            except Exception as e:
                return rx.toast.error(f"Missing ACCESS_KEY?\n{str(e)}", position="top-center")
            
        async with self:
            # is the user authenticated?
            # user = request_to_kalavai_core(
            #     method="get",
            #     endpoint="load_user_session")
            # self.is_logged_in = user is not None
            self.user_spaces = spaces
            if len(self.user_spaces) > 0 and self.selected_user_space is None:
                await self.set_user_space(self.user_spaces[0])
            
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
