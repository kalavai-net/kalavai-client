from typing import List
import asyncio

import reflex as rx

from .main_state import MainState
from .utils import request_to_kalavai_core


class ServiceData(rx.Base):
    namespace: str
    name: str
    internal: dict[str, str]
    external: dict[str, str]
    
class Service(rx.Base):
    """The item class."""
    data: ServiceData

class ServicesState(rx.State):
    """The state class."""

    is_loading: bool = False

    items: List[Service] = []
    total_items: int = 0
    offset: int = 0
    limit: int = 10  # Number of rows per page

    @rx.var(cache=True)
    def page_number(self) -> int:
        return (self.offset // self.limit) + 1

    @rx.var(cache=True)
    def total_pages(self) -> int:
        return (self.total_items // self.limit) + (
            1 if self.total_items % self.limit else 1
        )

    @rx.var(cache=True, initial_value=[])
    def get_current_page(self) -> list[Service]:
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
            self.total_items = 0
            self.items = []
        
        async with self:
            # load available pools
            try:
                data = request_to_kalavai_core(
                    method="get",
                    endpoint="fetch_pool_services")
                self.items = []
                for namespace, services in data.items():
                    for service in services:
                        self.items.append(
                            Service(
                                data=dict(
                                    namespace=namespace,
                                    name=service["name"],
                                    internal={key: endpoints["internal"] for key, endpoints in service["endpoints"].items()},
                                    external={key: f"http://{endpoints['external']}" for key, endpoints in service["endpoints"].items() if "external" in endpoints}
                                )
                            )
                        )
                    self.total_items = len(self.items)
                yield rx.toast.success("Services loaded successfully", position="top-center")
            except Exception as e:
                yield rx.toast.error(f"Error:\n{e}", position="top-center")
            self.is_loading = False
            
        