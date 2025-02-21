from typing import List
import asyncio

import reflex as rx

from ..backend.utils import request_to_kalavai_core

class Device(rx.Base):
    """The item class."""
    data: dict


class DevicesState(rx.State):
    """The state class."""

    is_loading: bool = False

    items: List[Device] = []
    selected_rows: set = set()

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
        
        devices = request_to_kalavai_core(
            method="get",
            endpoint="fetch_devices"
        )
        async with self:
            self.is_loading = False
            if "error" in devices:
                self.items = []
                return rx.toast.error(f"Error when fetching devices: {devices}", position="top-center")
            else:
                self.items = [Device(data=row) for row in devices]
                
            self.total_items = len(self.items)
    
    @rx.event(background=True)
    async def set_selected_row(self, index, state):
        async with self:
            if state:
                self.selected_rows.add(index)
            else:
                self.selected_rows.remove(index)
        print(self.selected_rows)
    
    @rx.event(background=True)
    async def remove_entries(self):
        async with self:
            result = request_to_kalavai_core(
                method="post",
                endpoint="delete_nodes",
                json={"nodes": [self.items[row].data["name"] for row in self.selected_rows]}
            )
            if "error" in result:
                return rx.toast.error(str(result["error"]), position="top-center")
            else:
                return rx.toast.success("Devices deleted", position="top-center")