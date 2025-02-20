from typing import List
import asyncio

import reflex as rx

from ..backend.main_state import MainState
from ..backend.utils import request_to_kalavai_core


class Pool(rx.Base):
    data: dict


class PoolsState(rx.State):
    """The state class."""

    items: List[Pool]
    is_loading: bool = False
    join_actions: List[str] = ["Join", "Attach"]
    selected_join_action: str = "Join"
    ip_addresses: List[str] = []
    connected_to_server: bool = False
    agent_running: bool = False
    is_server: bool = False

    total_items: int = 0
    offset: int = 0
    limit: int = 12  # Number of rows per page

    @rx.var(cache=True)
    def page_number(self) -> int:
        return (self.offset // self.limit) + 1

    @rx.var(cache=True)
    def total_pages(self) -> int:
        return (self.total_items // self.limit) + (
            1 if self.total_items % self.limit else 1
        )

    @rx.var(cache=True, initial_value=[])
    def get_current_page(self) -> list[Pool]:
        start_index = self.offset
        end_index = start_index + self.limit
        return self.items[start_index:end_index]

    def prev_page(self):
        if self.page_number > 1:
            self.offset -= self.limit

    def next_page(self):
        if self.page_number < self.total_pages:
            self.offset += self.limit

    def first_page(self):
        self.offset = 0

    def last_page(self):
        self.offset = (self.total_pages - 1) * self.limit
    
    @rx.event
    def set_join_action(self, action):
        self.selected_join_action = action

    @rx.event(background=True)
    async def load_entries(self):
        async with self:
            self.is_loading = True
        
        async with self:
            # load available pools
            pools = request_to_kalavai_core(
                method="get",
                endpoint="list_available_pools")
            self.items = [
                Pool(data=data) for data in pools
            ]
            self.is_loading = False
            yield rx.toast.success("Pools loaded successfully", position="top-center")
        
    @rx.event(background=True)
    async def load_ip_addresses(self):
        async with self:
            self.is_loading = True

        ip_addresses = request_to_kalavai_core(
            method="get",
            endpoint="get_ip_addresses")

        async with self:
            self.ip_addresses = ip_addresses
            self.is_loading = False
        
    @rx.event(background=True)
    async def create(self, form_data: dict):
        async with self:
            self.is_loading = True
        
        async with self:
            formatted_data = {}
            for key, value in form_data.items():
                if len(value) == 0:
                    self.is_loading = False
                    return rx.toast.error("Error: all fields must be filled in", position="top-center")
                if value.isdigit():
                    formatted_data[key] = int(value)
                else:
                    formatted_data[key] = value
        result = request_to_kalavai_core(
            method="post",
            endpoint="create_pool",
            json=formatted_data)
        if "error" in result:
            return rx.toast.error(result["error"], position="top-center")

        async with self:
            state = await self.get_state(MainState)
            state.update_connected(state=True)
            self.is_loading = False
            return rx.toast.success("Pool created", position="top-center")
        
    @rx.event(background=True)
    async def join(self, token):
        async with self:
            self.is_loading = True
        
        if self.selected_join_action == "Join":
            result = request_to_kalavai_core(
                method="post",
                endpoint="join_pool",
                json={"token":token})
        else:
            result = request_to_kalavai_core(
                method="post",
                endpoint="attach_to_pool",
                json={"token":token})

        async with self:
            if "error" in result:
                self.is_loading = False
                return rx.toast.error(result["error"], position="top-center")
            else:
                state = await self.get_state(MainState)
                state.update_connected(state=True)
            self.is_loading = False
        return rx.redirect("/dashboard")
    
    @rx.event(background=True)
    async def stop(self):
        async with self:
            self.is_loading = True
        
        async with self:
            result = request_to_kalavai_core(
                method="post",
                endpoint="stop_pool")
            if "error" in result:
                self.is_loading = False
                return rx.toast.error(result["error"], position="top-center")
            state = await self.get_state(MainState)
            state.update_connected(state=False)
            self.is_loading = False
        return rx.redirect("/")
    
    @rx.event(background=True)
    async def refresh_status(self):
        async with self:
            self.is_loading = True

        async with self:
            self.agent_running = request_to_kalavai_core(
                method="get",
                endpoint="is_agent_running")
        
        async with self:
            self.connected_to_server = request_to_kalavai_core(
                method="get",
                endpoint="is_connected")
        
        async with self:
            self.is_server = request_to_kalavai_core(
                method="get",
                endpoint="is_server")
            self.is_loading = False

    @rx.event(background=True)
    async def pause(self):
        async with self:
            self.is_loading = True

        result = request_to_kalavai_core(
            method="post",
            endpoint="pause_agent")
        async with self:
            if "error" in result:
                self.is_loading = False
                return rx.toast.error(result["error"], position="top-center")
        
        async with self:
            self.is_loading = False
            return rx.toast.success("Agent paused", position="top-center")
    
    @rx.event(background=True)
    async def resume(self):
        async with self:
            self.is_loading = True

        result = request_to_kalavai_core(
            method="post",
            endpoint="resume_agent")
        async with self:
            if "error" in result:
                self.is_loading = False
                return rx.toast.error(result["error"], position="top-center")
        
        async with self:
            self.is_loading = False
            return rx.toast.success("Agent restarted", position="top-center")

    
