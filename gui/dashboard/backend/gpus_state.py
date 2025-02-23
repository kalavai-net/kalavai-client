from typing import List
from enum import Enum
import asyncio

import reflex as rx

from ..backend.utils import request_to_kalavai_core

class GPU(rx.Base):
    """The item class."""
    data: dict


class GPUsState(rx.State):
    """The state class."""

    is_loading: bool = False

    items: List[GPU] = []

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
    def get_current_page(self) -> list[GPU]:
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
        
        devices = request_to_kalavai_core(
            method="get",
            endpoint="fetch_gpus"
        )
        async with self:
            self.is_loading = False
            if "error" in devices:
                self.items = []
                return rx.toast.error(f"Error when fetching gpus: {devices}", position="top-center")
            else:
                self.items = [GPU(data=row) for row in devices]
                
            self.total_items = len(self.items)
            
