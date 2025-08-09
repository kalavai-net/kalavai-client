from typing import List, Dict
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
    
    # Label management
    current_labels: Dict[str, Dict[str, str]] = {}  # node_name -> labels
    current_resources: Dict[str, Dict] = {} # available -> resources; total -> resources
    new_label_key: str = ""
    new_label_value: str = ""
    selected_node: str = ""

    total_items: int = 0
    offset: int = 0
    limit: int = 10  # Number of rows per page
    

    @rx.var
    def current_node_labels(self) -> Dict[str, str]:
        """Get the labels for the currently selected node."""
        if not self.selected_node or self.selected_node not in self.current_labels:
            return {}
        return self.current_labels[self.selected_node]
    
    @rx.var
    def current_node_resources(self) -> Dict[str, str]:
        """Get the labels for the currently selected node."""
        if not self.selected_node or self.selected_node not in self.current_resources:
            return {}
        # format resources
        resources = {}
        for key, value in self.current_resources[self.selected_node]["total"].items():
            available = self.current_resources[self.selected_node]["available"][key]
            resources[key] = f"{available} out of {value}"
        return resources

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
                all_elements = []
                for row, state in self.is_selected.items():
                    if state:
                        element = row + (self.page_number-1) * self.limit # 'row' is only local to current page, we need to calculate global row
                        all_elements.append(self.items[element].data["name"])
                result = request_to_kalavai_core(
                    method="post",
                    endpoint="delete_nodes",
                    json={"nodes": all_elements} #[self.items[row].data["name"] for row, state in self.is_selected.items() if state]}
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

    @rx.event(background=True)
    async def load_node_details(self, node_name: str):
        """Load details for a specific node."""
        async with self:
            self.selected_node = node_name
            self.is_loading = True
        
        try:
            labels_result = request_to_kalavai_core(
                method="get",
                endpoint="get_node_labels",
                json={"node_names": [node_name]}
            )
        except Exception as e:
            return rx.toast.error(f"Error loading labels: {e}", position="top-center")
        
        async with self:
            self.is_loading = False
            if "error" in labels_result:
                return rx.toast.error(str(labels_result["error"]), position="top-center")
            elif "labels" in labels_result and node_name in labels_result["labels"]:
                self.current_labels[node_name] = labels_result["labels"][node_name]
            else:
                self.current_labels[node_name] = {}
        
        try:
            resources_result = request_to_kalavai_core(
                method="get",
                endpoint="fetch_resources",
                json={"node_names": [node_name]}
            )
        except Exception as e:
            return rx.toast.error(f"Error loading resources: {e}", position="top-center")
        
        async with self:
            self.is_loading = False
            if "error" in resources_result:
                return rx.toast.error(str(resources_result["error"]), position="top-center")
            else:
                # format resources
                self.current_resources[node_name] = resources_result

    @rx.event(background=True)
    async def add_node_label(self):
        """Add a new label to the selected node."""
        if not self.new_label_key or not self.new_label_value:
            return rx.toast.error("Both key and value are required", position="top-center")
            
        async with self:
            self.is_loading = True
        
        try:
            result = request_to_kalavai_core(
                method="post",
                endpoint="add_node_labels",
                json={
                    "node_name": self.selected_node,
                    "labels": {self.new_label_key: self.new_label_value}
                }
            )
        except Exception as e:
            return rx.toast.error(f"Error adding label: {e}", position="top-center")
        
        async with self:
            self.is_loading = False
            if "error" in result:
                return rx.toast.error(str(result["error"]), position="top-center")
            else:
                # Clear the input fields
                self.new_label_key = ""
                self.new_label_value = ""
                # Return the class method instead of the instance method
                return rx.toast.success("Label added successfully", position="top-center")

    @rx.event(background=True)
    async def set_new_label_key(self, value: str):
        """Set the new label key."""
        async with self:
            self.new_label_key = value

    @rx.event(background=True)
    async def set_new_label_value(self, value: str):
        """Set the new label value."""
        async with self:
            self.new_label_value = value
