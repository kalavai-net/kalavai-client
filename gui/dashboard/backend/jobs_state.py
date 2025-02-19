from typing import List

import reflex as rx

from kalavai_client.core import (
    fetch_job_names,
    fetch_job_details,
    fetch_job_logs,
    fetch_job_templates,
    fetch_job_defaults,
    deploy_job,
    delete_job
)


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

        templates = fetch_job_templates()
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
        
        params = fetch_job_defaults(name=self.selected_template)
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
                result = delete_job(
                    name=self.items[row].data["name"]
                )
                print(result)
    
    @rx.event(background=True)
    async def deploy_job(self, form_data: dict):
        # TODO: parse form values
        for key, value in form_data.items():
            if value.isdigit():
                form_data[key] = int(value)

        async with self:
            print("job deployed:", form_data)
        
        result = deploy_job(
            template_name=self.selected_template,
            values_dict=form_data
        )
        if "error" in result:
            print(result)
    
    @rx.event(background=True)
    async def load_logs(self, index):
        async with self:
            self.logs = None
        
        logs = fetch_job_logs(
            job_name=self.items[index].data["name"],
            force_namespace=self.items[index].data["owner"]
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
        
        all_jobs = fetch_job_names()
        
        if "error" in all_jobs:
            async with self:
                print(f"Error when fetching jobs: {all_jobs}")
                self.items = []
                self.total_items = 0
                self.is_loading = False
        else:
            async with self:
                # job names
                self.items = []
                for job in all_jobs:
                    self.items.append(
                        Job(
                            data=job.dict(),
                            status=""
                        )
                    )
                self.total_items = len(self.items)
                self.is_loading = False
        
            async with self:
                # go into details
                self.items = []
                details = fetch_job_details(jobs=all_jobs)
                if "error" not in details:
                    for job_details in details:
                        self.items.append(
                            Job(
                                data=job_details.dict()
                            )
                        )
                self.is_loading = False
