from typing import List
import asyncio

import reflex as rx

from ..backend.main_state import MainState
from kalavai_client.core import (
    list_available_pools,
    attach_to_pool,
    stop_pool,
    join_pool,
    is_connected,
    is_agent_running,
    is_server,
    pause_agent,
    resume_agent,
    create_pool,
    get_ip_addresses
)


class Pool(rx.Base):
    data: dict


class PoolsState(rx.State):
    """The state class."""

    items: List[Pool]
    is_loading: bool = False
    join_actions: List[str] = ["Join", "Attach"]
    selected_join_action: str = "Join"
    pool_error_message: str = ""
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
            pools = list_available_pools()
            self.items = [
                Pool(data=data) for data in pools
            ]
            self.is_loading = False
        
    @rx.event(background=True)
    async def load_ip_addresses(self):
        async with self:
            self.is_loading = True

        ip_addresses = get_ip_addresses()

        async with self:
            self.ip_addresses = ip_addresses
            self.is_loading = False
        
    @rx.event(background=True)
    async def create(self, form_data: dict):
        async with self:
            self.is_loading = True
            self.pool_error_message = "Creating your LLM pool, this may take a while..."
            formatted_data = {}
            for key, value in form_data.items():
                if len(value) == 0:
                    self.pool_error_message = "Error: all fields must be filled in"
                    return
                if value.isdigit():
                    formatted_data[key] = int(value)
                else:
                    formatted_data[key] = value
        result = create_pool(**formatted_data)

        async with self:
            state = await self.get_state(MainState)
            state.update_connected(state=True)
            self.pool_error_message = ""
            self.is_loading = False
        
    @rx.event(background=True)
    async def join(self, token):
        async with self:
            self.is_loading = True
            self.pool_error_message = "Connecting, this may take a few minutes..."
        
        if self.selected_join_action == "Join":
            result = join_pool(token=token)
        else:
            result = attach_to_pool(token=token)

        async with self:
            if "error" in result:
                self.pool_error_message = result["error"] 
            else: 
                self.pool_error_message = ""
                state = await self.get_state(MainState)
                state.update_connected(state=True)
            self.is_loading = False
    
    @rx.event(background=True)
    async def stop(self):
        async with self:
            self.is_loading = True
        
        async with self:
            result = stop_pool()
            state = await self.get_state(MainState)
            state.update_connected(state=False)
            self.is_loading = False
    
    @rx.event(background=True)
    async def refresh_status(self):
        async with self:
            self.is_loading = True

        async with self:
            self.agent_running = is_agent_running()
        
        async with self:
            self.connected_to_server = is_connected()
        
        async with self:
            self.is_server = is_server()
            self.is_loading = False


    @rx.event(background=True)
    async def pause(self):
        async with self:
            self.is_loading = True

        result = pause_agent()
        yield PoolsState.refresh_status
        
        async with self:
            self.is_loading = False
    
    @rx.event(background=True)
    async def resume(self):
        async with self:
            self.is_loading = True

        result = resume_agent()
        yield PoolsState.refresh_status
        
        async with self:
            self.is_loading = False

    
