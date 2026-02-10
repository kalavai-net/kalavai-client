from typing import List, Union
from collections import defaultdict
import json
import asyncio

import reflex as rx

from ..backend.utils import (
    request_to_kalavai_core
)
from ..backend.main_state import MainState


class JobData(rx.Base):
    job_id: str
    spec: dict
    conditions: dict
    owner: str
    name: str
    workers: str
    endpoint: dict[str, str]
    status: str
    host_nodes: str

class Job(rx.Base):
    """The item class."""
    data: JobData

class TemplateData(rx.Base):
    """The template data class."""
    name: str
    description: str
    icon_url: str
    docs_url: str
    version: str


class JobsState(rx.State):
    """The state class."""

    current_deploy_step: int = 0
    is_loading: bool = False
    job_metadata: Union[str, None] = None
    job_logs: Union[dict[str, str], None] = None
    job_status: Union[str, None] = None
    log_tail: int = 100
    service_logs: Union[str, None] = None
    items: List[Job] = []
    is_selected: dict[int, bool]
    templates: list[dict] = []
    template_names: list[str]
    selected_template: str = ""
    template_name: Union[str, None] = None
    template_params: dict[str, dict] = {}
    template_metadata: Union[TemplateData, None] = None
    selected_labels: dict[str, list] = {}
    node_target_labels: list[str] = []
    target_label_mode: str = "AND"

    total_items: int = 0
    offset: int = 0
    limit: int = 10  # Number of rows per page

    def _parse_template_parameter(self, name, schema, value, required):
        """Parse a job template parameter and schema to a reflex parameter"""
        param = {
            "default": value,
            "type": schema["type"],
            "name": name,
            "required": required,
            "description": schema["description"] if "description" in schema else ""
        }
        # If it's an enum, set the possible options
        if "enum" in schema:
            param["options"] = schema["enum"]
            param["type"] = "enum"
        
        return param
    
    def _parse_parameter_values(self, form_data):
        """Parse form types to match known template parameter schema"""
        for key, value in form_data.items():
            if len(value.strip()) == 0:
                form_data[key] = None
                continue
            if key in self.template_params:
                if self.template_params[key]["type"] == "integer":
                    form_data[key] = int(value)
                if self.template_params[key]["type"] == "boolean":
                    form_data[key] = bool(value)
        return form_data
    
    def _expand_parameter_values(self, data):
        """Expand given parameters with default parameters"""
        for key, values in self.template_params.items():
            if key not in data:
                data[key] = values["default"]
        return data

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
        self.template_names = []
        self.template_params = {}
        self.template_metadata = None
        self.selected_template = ""
        self.template_name = None
        self.set_deploy_step(0)
        self.selected_labels = {}
        self.is_selected = {}
        self.is_loading = False
    
    def filter_templates(self, templates):
        return templates
    
    async def deploy(self, data: dict, is_redeployment: bool = False):
        form_data = self._expand_parameter_values(
            self._parse_parameter_values(data)
        )

        if self.template_name is None or len(self.template_name.strip()) == 0:
            return {"error": f"Job name not defined. Try again"}

        async with self:
            state = await self.get_state(MainState)
        data = {
            "name": self.template_name.lower(),
            "template_name": self.selected_template,
            "values": form_data,
            "force_namespace": state.selected_user_space,
            "is_update": is_redeployment
        }
        if self.selected_labels:
            data["target_labels"] = {key: value for key, value in self.selected_labels.items()}
            data["target_labels_ops"] = self.target_label_mode
        
        try:
            result = request_to_kalavai_core(
                method="post",
                endpoint="deploy_job",
                json=data
            )
            return result
        except Exception as e:
            return {"error": f"Missing ACCESS_KEY?\n{e}"}
    
    @rx.event(background=True)
    async def set_job_name(self, name):
        async with self:
            self.template_name = name
    
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
                self.service_logs = logs["error"]
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
            self.is_loading = True
        await asyncio.sleep(0.1)

        try:
            templates = request_to_kalavai_core(
                method="get",
                endpoint="fetch_job_templates"
            )
        except Exception as e:
            async with self:
                self.is_loading = False
            return rx.toast.error(f"Missing ACCESS_KEY?\n{e}", position="top-center")
        if "error" in templates:
            async with self:
                self.is_loading = False
            return rx.toast.error(f"Error when fetching templates: {templates}", position="top-center")
        else:
            async with self:
                self.templates = self.filter_templates(templates)
                self.template_names = [template["name"] for template in self.templates]
                self.is_loading = False

    def fetch_template_details(self):
        try:
            data = request_to_kalavai_core(
                method="get",
                endpoint="fetch_template_all",
                params={"name": self.selected_template}
            )
        except Exception as e:
            return rx.toast.error(f"Missing ACCESS_KEY?\n{e}", position="top-center")
        
        # set default parameters
        self.template_params = {}
        for name, value in data["values"].items():
            schema = data["schema"]["properties"][name]
            if "type" not in schema or schema["type"] == "object":
                continue
            param = self._parse_template_parameter(
                name=name, 
                schema=schema,
                value=value,
                required=name in data["schema"]["required"])
            
            self.template_params[name] = param
        # set template metadata
        self.template_metadata = TemplateData(
            name=data["metadata"]["name"] if "name" in data["metadata"] else "N/A",
            description=data["metadata"]["description"] if "description" in data["metadata"] else "N/A",
            icon_url=data["metadata"]["icon"] if "icon" in data["metadata"] else "N/A",
            docs_url= "".join(data["metadata"]["sources"]) if "sources" in data["metadata"] else "N/A",
            version=data["metadata"]["version"] if "version" in data["metadata"] else "N/A",
        )

    @rx.event(background=True)
    async def load_template_parameters(self, template):
        async with self:
            self.selected_template = template
            self.template_params = {}
            self.template_metadata = None
            self.is_loading = True
        
        await asyncio.sleep(0.1)
        async with self:
            self.fetch_template_details()

        async with self:
            self.is_loading = False

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
                    job_data = self.items[element].data.dict()
                    result = request_to_kalavai_core(
                        method="post",
                        endpoint="delete_job",
                        json={"name": job_data["name"], "force_namespace": job_data["owner"]}
                    )
                except Exception as e:
                    toast = rx.toast.error(f"Missing ACCESS_KEY?\n{e}", position="top-center")
                if "error" in result:
                    toast = rx.toast.error(result["error"], position="top-center")
            toast = rx.toast.success("Jobs deleted", position="top-center")
            self.reset_selection()
            return toast
        
    @rx.event(background=True)
    async def redeploy_job(self, form_data: dict):
        """Redeploy a job with new values"""
        # self.template_name and form data to redeploy
        result = await self.deploy(data=form_data, is_redeployment=True)

        if "error" in result:
            return rx.toast.error(result["error"], position="top-center")
        if "failed" in result and len(result["failed"]) > 0:
            return rx.toast.error(f"Failed to deploy: {result['failed']}", position="top-center")
        return rx.toast.success("Redeployment updated", position="top-center")

    @rx.event(background=True)
    async def deploy_job(self, form_data: dict):
        result = await self.deploy(data=form_data, is_redeployment=False)

        if "error" in result:
            return rx.toast.error(result["error"], position="top-center")
        if "failed" in result and len(result["failed"]) > 0:
            return rx.toast.error(f"Failed to deploy: {result['failed']}", position="top-center")
        return rx.toast.success("Deployment successful", position="top-center")

    @rx.event
    async def open_endpoint(self, address):
        return rx.redirect(address, is_external=True)
    
    @rx.event(background=True)
    async def load_current_job_details(self, index):
        element = index + (self.page_number-1) * self.limit
        async with self:
            self.is_loading = True
        await asyncio.sleep(0.1)

        async with self:
            data = self.items[element].data.dict()
            job_id = data["job_id"]
            self.selected_template = f"{data['spec']['template']['repo']}/{data['spec']['template']['chart']}"
            if "nodeSelectors" in data["spec"]:
                self.selected_labels = data["spec"]["nodeSelectors"]
        
            self.fetch_template_details()
        
            # parse template defaults and use job params instead
            job_data = self._expand_parameter_values(
                data["spec"]["template"]["values"]
            )
            for key, value in self.template_params.items():
                if key in job_data:
                    self.template_params[key]["default"] = job_data[key]

        # set job name
        async with self:
            self.template_name = data["name"]
            self.is_loading = False

    
    @rx.event(background=True)
    async def load_logs(self, index):
        async with self:
            self.job_logs = None
        element = index + (self.page_number-1) * self.limit
        job_data = self.items[element].data.dict()
        async with self:
            if "spec" in job_data:
                self.job_metadata = json.dumps(job_data["spec"], indent=3)
            else:
                self.job_metadata = "Job spec pending..."
            if "conditions" in job_data:
                self.job_status = json.dumps(job_data["conditions"], indent=3)
            else:
                self.job_status = "Status conditions pending..."
            self.job_logs = {}
        
        try:
            data = request_to_kalavai_core(
                method="get",
                endpoint="fetch_job_logs",
                params={
                    "job_name": job_data["job_id"],
                    "force_namespace": job_data["owner"],
                    "tail": self.log_tail
                }
            )
        except Exception as e:
            return rx.toast.error(f"Missing ACCESS_KEY?\n{e}", position="top-center")
        async with self:
            if "error" in data:
                self.job_logs = {"error": data["error"]}
            else:
                self.job_logs = {}
                for match_label, logs in data.items():
                    for name, info in logs.items():
                        if "describe" not in info:
                            self.job_logs[name] = "Logs not ready yet"
                            continue
                        pod_spec = info["describe"]
                        if "logs" not in info or info["logs"] is None:
                            self.job_logs[name] = "Logs not ready yet"
                        else:
                            n_logs = "------"
                            n_logs += "LOGS"
                            n_logs += "------\n"
                            n_logs += info["logs"]
                            n_logs += "\n\n"
                            self.job_logs[name] = n_logs

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
                # parse endpoint
                job_details["endpoint"] = {name: f"http://{endpoint['address']}:{endpoint['port']}" for name, endpoint in job_details["endpoint"].items()}
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