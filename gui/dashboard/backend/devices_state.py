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
    is_selected: dict[int, bool]
    invitees: str = ""

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
        
        try:
            devices = request_to_kalavai_core(
                method="get",
                endpoint="fetch_devices"
            )
        except Exception as e:
            return rx.toast.error(f"Missing ACCESS_KEY?\n{e}", position="top-center")
        async with self:
            self.is_loading = False
            if "error" in devices:
                self.items = []
                return rx.toast.error(f"Error when fetching devices: {devices}", position="top-center")
            else:
                self.items = [Device(data=row) for row in devices]
                
            self.total_items = len(self.items)
    
    @rx.event(background=True)
    async def remove_entries(self):
        async with self:
            try:
                result = request_to_kalavai_core(
                    method="post",
                    endpoint="delete_nodes",
                    json={"nodes": [self.items[row].data["name"] for row, state in self.is_selected.items() if state]}
                )
            except Exception as e:
                return rx.toast.error(f"Missing ACCESS_KEY?\n{e}", position="top-center")
            finally:
                self.is_selected = {i: False for i in self.is_selected}
            if "error" in result:
                return rx.toast.error(str(result["error"]), position="top-center")
            else:
                return rx.toast.success("Devices deleted", position="top-center")
    
    @rx.event(background=True)
    async def set_selected_row(self, index, state):
        async with self:
            self.is_selected[index] = state
    
    @rx.event(background=True)
    async def toggle_unschedulable(self, state, index):
        async with self:
            try:
                result = request_to_kalavai_core(
                    method="post",
                    endpoint="uncordon_nodes" if state else "cordon_nodes",
                    json={"nodes": [self.items[index].data["name"]]}
                )
            except Exception as e:
                return rx.toast.error(f"Missing ACCESS_KEY?\n{e}", position="top-center")
            if "error" in result:
                return rx.toast.error(str(result["error"]), position="top-center")
            else:
                return rx.toast.success(
                    "Device uncordoned" if state else "Device cordoned",
                    position="top-center")
        
    @rx.event(background=True)
    async def set_invitees(self, invitees):
        async with self:
            self.invitees = invitees

    @rx.event(background=True)
    async def send_invites(self):
        async with self:
            self.is_loading = True

        try:
            result = request_to_kalavai_core(
                method="post",
                endpoint="send_pool_invites",
                json={"invitees": self.invitees.split(",")}
            )
        except Exception as e:
            return rx.toast.error(f"Missing ACCESS_KEY?\n{e}", position="top-center")
        async with self:
            self.set_invitees("")
            self.is_loading = False
            if "error" in result:
                return rx.toast.error(result["error"], position="top-center")
            if "not_sent" in result and len(result["not_sent"]) > 0:
                return rx.toast.warning(f"Could not send invite to: {result['not_sent']}", position="top-center")
            if "sent" in result:
                return rx.toast.success(f"Invites sent to {result['sent']}", position="top-center")
            return rx.toast.info("Nothing was sent", position="top-center")
