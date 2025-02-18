from typing import List
from enum import Enum
import asyncio

import reflex as rx

from kalavai_client.core import fetch_devices

class Device(rx.Base):
    """The item class."""
    data: dict


class DevicesState(rx.State):
    """The state class."""

    is_loading: bool = False

    items: List[Device] = []

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
    def get_current_page(self) -> list[Device]:
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

    @rx.event(background=True)
    async def load_entries(self):
        async with self:
            self.is_loading = True
        
        devices = fetch_devices()
        async with self:
            if "error" in devices:
                print(f"Error when fetching devices: {devices}")
                self.items = []
            else:
                self.items = [Device(data=row.dict()) for row in devices]
                
            self.is_loading = False
            self.total_items = len(self.items)
            
