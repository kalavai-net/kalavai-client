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

    sort_value: str = ""
    sort_reverse: bool = False

    total_items: int = 0
    offset: int = 0
    limit: int = 12  # Number of rows per page

    @rx.var(cache=True)
    def filtered_sorted_items(self) -> List[GPU]:
        items = self.items

        # Sort items based on selected column
        if self.sort_value:
            # Determine if the column should be sorted as numeric
            numeric_columns = ["available", "total"]
            
            if self.sort_value in numeric_columns:
                items = sorted(
                    items,
                    key=lambda item: float(item.data.get(self.sort_value, 0)),
                    reverse=self.sort_reverse,
                )
            else:
                items = sorted(
                    items,
                    key=lambda item: str(item.data.get(self.sort_value, "")).lower(),
                    reverse=self.sort_reverse,
                )

        return items

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
        return self.filtered_sorted_items[start_index:end_index]

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

    def set_sort_column(self, column: str):
        """Set the column to sort by. Toggle reverse if same column is clicked."""
        if self.sort_value == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_value = column
            self.sort_reverse = False
        # Reset to first page when sorting changes
        self.offset = 0

    @rx.event(background=True)
    async def load_entries(self):
        async with self:
            self.is_loading = True
        
        try:
            devices = request_to_kalavai_core(
                method="get",
                endpoint="fetch_gpus"
            )
        except Exception as e:
            return rx.toast.error(f"Missing ACCESS_KEY?\n{e}", position="top-center")
        async with self:
            self.is_loading = False
            if "error" in devices:
                self.items = []
                self.total_items = 0
                return rx.toast.error(f"Error when fetching gpus: {devices}", position="top-center")
            else:
                self.items = []
                for gpu in devices:
                    gpu_data = {
                        "node": gpu["node"],
                        "model": gpu["model"],
                        "used": 100 - int(float(gpu["available"]) / float(gpu["total"]) * 100),
                        "total": gpu["total"],
                        "ready": gpu["ready"]
                    }
                    self.items.append(GPU(data=gpu_data))
            
            # Update total_items based on sorted items (same as items length, but using filtered_sorted_items for consistency)
            self.total_items = len(self.filtered_sorted_items)
            
