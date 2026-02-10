from typing import List
from enum import Enum
import asyncio
from collections import defaultdict

import reflex as rx

from ..backend.utils import request_to_kalavai_core

# filter resources shown per device to only those here
RESOURCES_SHOWN: list[str] = ["cpu", "memory", "nvidia.com/gpu", "amd.com/gpu"]


class Resource(rx.Base):
    """The item class."""
    data: dict


class ResourcesState(rx.State):
    
    """The state class."""

    is_loading: bool = False

    items: List[Resource] = []

    is_selected: dict[int, bool]
    invitees: str = ""
    
    # Label management
    current_labels: dict[str, dict[str, str]] = {}  # node_name -> labels
    current_resources: dict[str, dict] = {} # available -> resources; total -> resources
    new_label_key: str = ""
    new_label_value: str = ""
    selected_node: str = ""

    sort_value: str = ""
    sort_reverse: bool = False
    total_items: int = 0
    offset: int = 0
    limit: int = 12  # Number of rows per page

    @rx.var
    def current_node_labels(self) -> dict[str, str]:
        """Get the labels for the currently selected node."""
        if not self.selected_node or self.selected_node not in self.current_labels:
            return {}
        return self.current_labels[self.selected_node]
    
    @rx.var
    def current_node_resources(self) -> dict[str, str]:
        """Get the labels for the currently selected node."""
        if not self.selected_node or self.selected_node not in self.current_resources:
            return {}
        # format resources
        resources = {}
        if "total" not in self.current_resources[self.selected_node] or "available" not in self.current_resources[self.selected_node]:
            return {}
        for key, value in self.current_resources[self.selected_node]["total"].items():
            available = self.current_resources[self.selected_node]["available"][key]
            resources[key] = f"{available} out of {value}"
        return resources

    @rx.var(cache=True)
    def filtered_sorted_items(self) -> List[Resource]:
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
    def get_current_page(self) -> list[Resource]:
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
    
    def reset_selection(self):
        self.is_selected = {i: False for i in self.is_selected}

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
    async def set_selected_row(self, index, state):
        async with self:
            self.is_selected[index] = state

    @rx.event(background=True)
    async def load_entries(self):
        # Load device information
        temp_data = defaultdict(dict)
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
                for device in devices:
                    temp_data[device["name"]] = {
                        "issues": ",".join([f"{label}: {device[label]}" for label in ["memory_pressure", "disk_pressure", "pid_pressure"]  if device[label]]),
                        "disabled": device["unschedulable"],
                        "ready": device["ready"]
                    }
                
            self.total_items = len(self.items)
        # Lad GPU information
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
                    if gpu["ready"]:
                        used = 100 - int(float(gpu["available"]) / float(gpu["total"]) * 100) if gpu["total"] > 0 else 0
                    else:
                        used = 0
                    gpu_data = {
                        "node": gpu["node"],
                        "models": "\n\n".join(gpu["models"]),
                        "used": used,
                        "total": gpu["total"]
                    }
                    item = {**temp_data[gpu["node"]], **gpu_data}
                    del temp_data[gpu["node"]]
                    self.items.append(Resource(data=item))
                # add non-gpu devices left
                for name, device in temp_data.items():
                    gpu_data = {"node": name, "model": "-", "used": 0, "total": 0}
                    item = {**device, **gpu_data}
                    self.items.append(Resource(data=item))
            # Update total_items based on sorted items (same as items length, but using filtered_sorted_items for consistency)
            self.total_items = len(self.filtered_sorted_items)
    
    @rx.event(background=True)
    async def remove_entries(self):
        async with self:
            try:
                all_elements = []
                for row, state in self.is_selected.items():
                    if state:
                        element = row + (self.page_number-1) * self.limit # 'row' is only local to current page, we need to calculate global row
                        all_elements.append(self.items[element].data["node"])
                result = request_to_kalavai_core(
                    method="post",
                    endpoint="delete_nodes",
                    json={"nodes": all_elements} #[self.items[row].data["name"] for row, state in self.is_selected.items() if state]}
                )
            except Exception as e:
                return rx.toast.error(f"Missing ACCESS_KEY?\n{e}", position="top-center")
            finally:
                self.reset_selection()
            if "error" in result:
                return rx.toast.error(str(result["error"]), position="top-center")
            else:
                return rx.toast.success("Devices deleted", position="top-center")

    @rx.event(background=True)
    async def toggle_unschedulable(self, state, index):
        async with self:
            try:
                result = request_to_kalavai_core(
                    method="post",
                    endpoint="uncordon_nodes" if state else "cordon_nodes",
                    json={"nodes": [self.items[index].data["node"]]}
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
    async def load_node_details(self, node_name: str):
        """Load details for a specific node."""
        async with self:
            self.selected_node = node_name
            self.current_resources = {}
            self.is_loading = True
        
        try:
            labels_result = request_to_kalavai_core(
                method="get",
                endpoint="get_node_labels",
                params={"nodes": node_name}
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
                json={"nodes": [node_name]}
            )
        except Exception as e:
            return rx.toast.error(f"Error loading resources: {e}", position="top-center")
        
        async with self:
            self.is_loading = False
            if "error" in resources_result:
                return rx.toast.error(str(resources_result["error"]), position="top-center")
            else:
                # format resources
                self.current_resources[node_name] = {
                    "total": {key: value for key, value in resources_result["total"].items() if key in RESOURCES_SHOWN},
                    "available": {key: value for key, value in resources_result["available"].items() if key in RESOURCES_SHOWN}
                }

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