from typing import List

import reflex as rx

from ..backend.utils import request_to_kalavai_core


class Job(rx.Base):
    """The item class."""
    data: dict

class JobsState(rx.State):
    """The state class."""

    FORBIDDEN_PARAMS: list[str] = [
        "id_field",
        "endpoint_ports"
    ]

    is_loading: bool = False
    logs: str = None
    items: List[Job] = []
    selected_rows: set = set()
    templates: list[str] = []
    selected_template: str
    template_params: list[dict[str, str]] = []

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
    async def load_templates(self):
        async with self:
            self.templates = []
            self.template_params = []

        templates = request_to_kalavai_core(
            method="get",
            endpoint="fetch_job_templates"
        )
        if "error" in templates:
            print("Error when fetching templates:", templates)
        else:
            async with self:
                self.templates = [t for t in templates if t not in ["custom"]]
            
    @rx.event(background=True)
    async def load_template_parameters(self, template):
        async with self:
            self.selected_template = template
            self.template_params = []
        
        params = request_to_kalavai_core(
            method="get",
            endpoint="fetch_job_defaults",
            params={"name": self.selected_template}
        )
        async with self:
            self.template_params = [p for p in params if p["name"] not in self.FORBIDDEN_PARAMS]

    @rx.event(background=True)
    async def set_selected_row(self, index, state):
        async with self:
            if state:
                self.selected_rows.add(index)
            else:
                self.selected_rows.remove(index)
    
    @rx.event(background=True)
    async def remove_entries(self):
        async with self:
            for row in self.selected_rows:
                result = request_to_kalavai_core(
                    method="post",
                    endpoint="delete_job",
                    json={"name": self.items[row].data["name"], "force_namespace": self.items[row].data["owner"]}
                )
                if "error" in result:
                    return rx.toast.error(result["error"], position="top-center")
                else:
                    return rx.toast.success("Jobs deleted", position="top-center")

    @rx.event(background=True)
    async def deploy_job(self, form_data: dict):
        # TODO: parse form values
        for key, value in form_data.items():
            if value.isdigit():
                form_data[key] = int(value)

        force_namespace = None 
        if "force_namespace" in form_data and len(form_data["force_namespace"].strip()) > 0:
            force_namespace = form_data["force_namespace"]

        async with self:
            print("job deployed:", form_data)
        
        result = request_to_kalavai_core(
            method="post",
            endpoint="deploy_job",
            json={
                "template_name": self.selected_template,
                "values": form_data,
                "force_namespace": force_namespace
            }
        )
        if "error" in result:
            return rx.toast.error(str(result["error"]), position="top-center")
        else:
            return rx.toast.success("Job deployed", position="top-center")

    
    @rx.event(background=True)
    async def load_logs(self, index):
        async with self:
            self.logs = None
        
        logs = request_to_kalavai_core(
            method="get",
            endpoint="fetch_job_logs",
            params={
                "job_name": self.items[index].data["name"],
                "force_namespace": self.items[index].data["owner"]
            }
        )
        async with self:
            if "error" in logs:
                self.logs = logs["error"]
            else:
                formatted_logs = []
                for name, log in logs.items():
                    formatted_logs.append("------")
                    formatted_logs.append(f"--> Pod: {name}")
                    formatted_logs.append("------")
                    formatted_logs.extend(log.split("\n"))
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
        
        all_jobs = request_to_kalavai_core(
            method="get",
            endpoint="fetch_job_names")
        
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
                details = request_to_kalavai_core(
                    method="post",
                    endpoint="fetch_job_details",
                    json={"jobs": all_jobs})
                if "error" not in details:
                    for job_details in details:
                        self.items.append(
                            Job(
                                data=job_details
                            )
                        )
                self.is_loading = False
