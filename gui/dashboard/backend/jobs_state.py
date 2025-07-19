from typing import List
from collections import defaultdict

import reflex as rx

from ..backend.utils import request_to_kalavai_core


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

class JobsState(rx.State):
    """The state class."""

    current_deploy_step: int = 0
    is_loading: bool = False
    logs: str = None
    items: List[Job] = []
    is_selected: dict[int, bool]
    templates: list[str] = []
    selected_template: str = ""
    template_params: list[dict[str, str]] = []
    template_metadata: TemplateData = None
    selected_labels: dict[str, str] = {}
    new_label_key: str
    new_label_value: str

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
    def get_current_page(self) -> list[Job]:
        start_index = self.offset
        end_index = start_index + self.limit
        return self.items[start_index:end_index]
    
    def set_deploy_step(self, step: int):
        self.current_deploy_step = step

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
    
    def reset_values(self):
        self.templates = []
        self.template_params = []
        self.template_metadata = None
        self.selected_template = ""
        self.set_deploy_step(0)
        self.selected_labels = {}
    
    def filter_templates(self, templates):
        return [t for t in templates if t not in ["custom"]]

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
                )

    @rx.event(background=True)
    async def set_selected_row(self, index, state):
        async with self:
            self.is_selected[index] = state
    
    @rx.event(background=True)
    async def remove_entries(self):
        async with self:
            for row, state in self.is_selected.items():
                if not state:
                    continue
                try:
                    result = request_to_kalavai_core(
                        method="post",
                        endpoint="delete_job",
                        json={"name": self.items[row].data["name"], "force_namespace": self.items[row].data["owner"]}
                    )
                except Exception as e:
                    toast = rx.toast.error(f"Missing ACCESS_KEY?\n{e}", position="top-center")
                if "error" in result:
                    toast = rx.toast.error(result["error"], position="top-center")
            toast = rx.toast.success("Jobs deleted", position="top-center")
            self.is_selected = {i: False for i in self.is_selected}
            return toast

    @rx.event(background=True)
    async def deploy_job(self, form_data: dict):
        # TODO: parse form values
        for key, value in form_data.items():
            if value.isdigit():
                form_data[key] = int(value)
            
        data = {
            "template_name": self.selected_template,
            "values": form_data
        }
        if self.selected_labels:
            data["target_labels"] = self.selected_labels
        
        force_namespace = form_data.pop("force_namespace", None)
        if force_namespace is not None and len(force_namespace.strip()) > 0:
            data["force_namespace"] = force_namespace

        async with self:
            print("job deployed:", form_data)
        
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
            self.logs = None
        
        try:
            logs = request_to_kalavai_core(
                method="get",
                endpoint="fetch_job_logs",
                params={
                "job_name": self.items[index].data["name"],
                "force_namespace": self.items[index].data["owner"]
                }
            )
        except Exception as e:
            return rx.toast.error(f"Missing ACCESS_KEY?\n{e}", position="top-center")
        async with self:
            if "error" in logs:
                self.logs = logs["error"]
            else:
                formatted_logs = []
                for name, info in logs.items():
                    formatted_logs.append("------")
                    formatted_logs.append(f"--> Pod: {name} in {info['pod']['spec']['node_name']}")
                    formatted_logs.append("------")
                    formatted_logs.extend(info['logs'].split("\n"))
                    formatted_logs.append("")
                    #logs = {name: log.split("\n") for name, log in logs.items()}
                if len(formatted_logs) == 0:
                    self.logs = "No logs found. Is this your job?"
                else:
                    self.logs = "\n".join(formatted_logs)

    @rx.event(background=True)
    async def load_entries(self):
        async with self:
            self.is_loading = True
        
        try:
            all_jobs = request_to_kalavai_core(
                method="get",
                endpoint="fetch_job_names")
        except Exception as e:
            return rx.toast.error(f"Missing ACCESS_KEY?\n{e}", position="top-center")
        
        if "error" in all_jobs:
            async with self:
                self.items = []
                self.total_items = 0
                self.is_loading = False
                return rx.toast.error(f"Error when fetching jobs: {all_jobs}", position="top-center")
        else:
            async with self:
                # job names
                self.items = []
                for job in all_jobs:
                    self.items.append(
                        Job(
                            data=job,
                            status=""
                        )
                    )
                self.total_items = len(self.items)
                self.is_loading = False
        
            async with self:
                # go into details
                self.items = []
                try:
                    details = request_to_kalavai_core(
                        method="post",
                        endpoint="fetch_job_details",
                        json={"jobs": all_jobs})
                except Exception as e:
                    return rx.toast.error(f"Missing ACCESS_KEY?\n{e}", position="top-center")
                if "error" not in details:
                    for job_details in details:
                        self.items.append(
                            Job(
                                data=job_details
                            )
                        )
                self.is_loading = False

    @rx.event(background=True)
    async def set_new_label_key(self, value: str):
        """Set the new label key."""
        async with self:
            self.new_label_key = value
    
    @rx.event(background=True)
    async def set_new_label_value(self, value: str):
        """Set the new label key."""
        async with self:
            self.new_label_value = value

    @rx.event(background=True)
    async def add_label(self):
        """Add a new label to the deployment."""
        async with self:
            self.selected_labels[self.new_label_key] = self.new_label_value
        
        async with self:
            self.new_label_key = ""
            self.new_label_value = ""
