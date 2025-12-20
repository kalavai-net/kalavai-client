from typing import List
from collections import defaultdict
import json

import reflex as rx

from ..backend.utils import request_to_kalavai_core
from ..backend.main_state import MainState


class Job(rx.Base):
    """The item class."""
    data: dict

class TemplateData(rx.Base):
    """The template data class."""
    name: str
    description: str
    icon_url: str
    docs_url: str
    info: str
    values_rules: str
    template_rules: str


class JobsState(rx.State):
    """The state class."""

    current_deploy_step: int = 0
    is_loading: bool = False
    job_metadata: str = None
    job_logs: str = None
    job_status: str = None
    log_tail: int = 100
    service_logs: str = None
    items: List[Job] = []
    is_selected: dict[int, bool]
    templates: list[str] = []
    selected_template: str = ""
    template_params: list[dict[str, str]] = []
    template_metadata: TemplateData = None
    selected_labels: dict[str, list] = {}
    node_target_labels: list[str] = []
    target_label_mode: str = "AND"

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
    def get_current_page(self) -> list[Job]:
        start_index = self.offset
        end_index = start_index + self.limit
        return self.items[start_index:end_index]
    
    def set_deploy_step(self, step: int):
        self.current_deploy_step = step

    def prev_page(self):
        self.reset_selection()
        if self.page_number > 1:
            self.offset -= self.limit

    def next_page(self):
        self.reset_selection()
        if self.page_number < self.total_pages:
            self.offset += self.limit

    def first_page(self):
        self.offset = 0

    def last_page(self):
        self.offset = (self.total_pages - 1) * self.limit
    
    def reset_selection(self):
        self.is_selected = {i: False for i in self.is_selected}
    
    def reset_values(self):
        self.templates = []
        self.template_params = []
        self.template_metadata = None
        self.selected_template = ""
        self.set_deploy_step(0)
        self.selected_labels = {}
        self.is_selected = {}
    
    def filter_templates(self, templates):
        return [t for t in templates if t not in ["custom"]]
    
    @rx.event(background=True)
    async def load_job_data(self):
        await self.load_templates()
        await self.load_node_target_labels()
    
    @rx.event(background=True)
    async def load_node_target_labels(self):
        async with self:
            self.node_target_labels = []
        
        try:
            # load nodes
            nodes = request_to_kalavai_core(
                method="get",
                endpoint="fetch_devices"
            )
            node_names = [node["name"] for node in nodes]
            node_target_labels = request_to_kalavai_core(
                method="get",
                endpoint="get_node_labels",
                params={"nodes": node_names}
            )
            label_set = {f"{key}: {value}" for value_pair in node_target_labels["labels"].values() for key, value in value_pair.items()}
        except Exception as e:
            return rx.toast.error(f"{e}", position="top-center")
        async with self:
            self.node_target_labels = sorted(list(label_set))

    @rx.event(background=True)
    async def load_service_logs(self):
        async with self:
            self.service_logs = None
        
        try:
            logs = request_to_kalavai_core(
                method="get",
                endpoint="fetch_service_logs",
                params={"tail": self.log_tail}
            )
        except Exception as e:
            return rx.toast.error(f"{e}", position="top-center")
        async with self:
            if "error" in logs:
                self.job_logs = logs["error"]
            else:
                formatted_logs = []
                for name, info in logs.items():
                    formatted_logs.append("------")
                    formatted_logs.append(f"--> Service: {name} in {info['pod']['spec']['node_name']}")
                    formatted_logs.append("------")
                    formatted_logs.extend(info['logs'].split("\n"))
                    formatted_logs.append("")
                    #logs = {name: log.split("\n") for name, log in logs.items()}
                if len(formatted_logs) == 0:
                    self.service_logs = "No logs found. Is this your job?"
                else:
                    self.service_logs = "\n".join(formatted_logs)


    @rx.event(background=True)
    async def load_templates(self):
        async with self:
            self.reset_values()

        try:
            templates = request_to_kalavai_core(
                method="get",
                endpoint="fetch_job_templates"
            )
        except Exception as e:
            return rx.toast.error(f"Missing ACCESS_KEY?\n{e}", position="top-center")
        if "error" in templates:
            print("Error when fetching templates:", templates)
        else:
            async with self:
                self.templates = self.filter_templates(templates)
            
    @rx.event(background=True)
    async def load_template_parameters(self, template):
        async with self:
            self.selected_template = template
            self.template_params = []
            self.template_metadata = None
        
        try:
            data = request_to_kalavai_core(
                method="get",
                endpoint="fetch_job_defaults",
                params={"name": self.selected_template}
            )
            params = data
            data = request_to_kalavai_core(
                method="get",
                endpoint="fetch_job_metadata",
                params={"name": self.selected_template}
            )
            metadata = data
        except Exception as e:
            return rx.toast.error(f"Missing ACCESS_KEY?\n{e}", position="top-center")
        async with self:
            self.template_params = [p for p in params if p["editable"]]
            if metadata:
                self.template_metadata = TemplateData(
                    name=metadata["name"] if "name" in metadata else "N/A",
                    description=metadata["description"] if "description" in metadata else "N/A",
                    icon_url=metadata["icon"] if "icon" in metadata else "N/A",
                    docs_url=metadata["docs"] if "docs" in metadata else "N/A",
                    info=metadata["info"] if "info" in metadata else "N/A",
                    template_rules=metadata["template_rules"] if "info" in metadata else "N/A",
                    values_rules=metadata["values_rules"] if "info" in metadata else "N/A"
                )

    @rx.event(background=True)
    async def set_selected_row(self, index, state):
        async with self:
            self.is_selected[index] = state
    
    @rx.event(background=True)
    async def remove_entries(self):
        async with self:
            for row, state in self.is_selected.items():
                element = row + (self.page_number-1) * self.limit # 'row' is only local to current page, we need to calculate global row
                if not state:
                    continue
                try:
                    result = request_to_kalavai_core(
                        method="post",
                        endpoint="delete_job",
                        json={"name": self.items[element].data["name"], "force_namespace": self.items[element].data["owner"]}
                    )
                except Exception as e:
                    toast = rx.toast.error(f"Missing ACCESS_KEY?\n{e}", position="top-center")
                if "error" in result:
                    toast = rx.toast.error(result["error"], position="top-center")
            toast = rx.toast.success("Jobs deleted", position="top-center")
            self.reset_selection()
            return toast

    @rx.event(background=True)
    async def deploy_job(self, form_data: dict):
        # TODO: parse form values
        for key, value in form_data.items():
            if value.isdigit():
                form_data[key] = int(value)
        
        async with self:
            state = await self.get_state(MainState)
        data = {
            "template_name": self.selected_template,
            "values": form_data,
            "force_namespace": state.selected_user_space
        }
        if self.selected_labels:
            data["target_labels"] = self.selected_labels
            data["target_labels_ops"] = self.target_label_mode

        async with self:
            print("job deployed:", data)
        
        try:
            result = request_to_kalavai_core(
                method="post",
                endpoint="deploy_job",
                json=data
            )
        except Exception as e:
            return rx.toast.error(f"Missing ACCESS_KEY?\n{e}", position="top-center")
        if "error" in result:
            return rx.toast.error(str(result["error"]), position="top-center")
        else:
            return rx.toast.success("Job deployed", position="top-center")

    @rx.event
    async def open_endpoint(self, index):
        return rx.redirect(self.items[index].data["endpoint"], is_external=True)
    
    @rx.event(background=True)
    async def load_logs(self, index):
        async with self:
            self.job_logs = None
        element = index + (self.page_number-1) * self.limit
        try:
            data = request_to_kalavai_core(
                method="get",
                endpoint="fetch_job_logs",
                params={
                    "job_name": self.items[element].data["name"],
                    "force_namespace": self.items[element].data["owner"],
                    "tail": self.log_tail
                }
            )
        except Exception as e:
            return rx.toast.error(f"Missing ACCESS_KEY?\n{e}", position="top-center")
        async with self:
            if "error" in data:
                self.job_logs = data["error"]
            else:
                self.job_logs = ""
                self.job_metadata = ""
                self.job_status = ""
                for match_label, logs in data.items():
                    for name, info in logs.items():
                        if "describe" not in info:
                            self.job_logs = "Logs not ready yet"
                            self.job_metadata = "Info not ready yet"
                            self.job_status = "Info not ready yet"
                            continue
                        pod_spec = info["describe"]
                        if "logs" not in info or info["logs"] is None:
                            self.job_logs = "Logs not ready yet"
                        else:
                            self.job_logs += "------"
                            self.job_logs += f"--> Pod: {name} in {pod_spec['spec']['node_name']}"
                            self.job_logs += "------"
                            self.job_logs += info["logs"]
                            self.job_logs += "\n\n"
                        if "status" in info["describe"]:
                            self.job_status += f"--> STATUS for: {name} in {pod_spec['spec']['node_name']}"
                            self.job_status += json.dumps(info["describe"]["status"], indent=2)
                            self.job_status += "\n\n"
                        if "metadata" in info["describe"]:
                            self.job_metadata += f"--> METADATA for: {name} in {pod_spec['spec']['node_name']}"
                            self.job_metadata += json.dumps(info["describe"]["metadata"], indent=2)
                            self.job_metadata += "\n\n"

    @rx.event(background=True)
    async def set_target_label_mode(self, mode):
        async with self:
            self.target_label_mode = mode
    
    @rx.event(background=True)
    async def set_log_tail(self, value):
        async with self:
            try:
                self.log_tail = int(value)
            except:
                self.log_tail = 100
    
    @rx.event(background=True)
    async def load_entries(self):
        async with self:
            self.is_loading = True
            self.total_items = 0
            self.items = []
            state = await self.get_state(MainState)

        try:
            
            details = request_to_kalavai_core(
                method="get",
                endpoint="fetch_job_details",
                params={"force_namespace": state.selected_user_space})
        except Exception as e:
            return rx.toast.error(f"Missing ACCESS_KEY?\n{str(e)}", position="top-center")
            
        if "error" in details:
            return rx.toast.error(f"Error:\n{details}", position="top-center")
    
        async with self:
            
            for job_details in details:
                self.items.append(
                    Job(
                        data=job_details
                    )
                )  
            self.total_items = len(self.items)
            self.is_loading = False
    
    @rx.event(background=True)
    async def clear_target_labels(self):
        """Clear all node selector labels"""
        async with self:
            self.selected_labels = {}
    
    @rx.event(background=True)
    async def parse_new_target_label(self, encoded_label: str):
        """Set the new node selector label"""
        try:
            key = encoded_label.split(":")[0].strip()
            value = encoded_label.split(":")[1].strip()
        except:
            return rx.toast.error("Invalid label format, ':' expected", position="top-center")
        async with self:
            if key in self.selected_labels:
                self.selected_labels[key].append(value)
            else:
                self.selected_labels[key] = [value]