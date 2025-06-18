from typing import List
import asyncio

import reflex as rx
from plotly.graph_objects import Figure
import plotly.graph_objects as go

from ..backend.utils import request_to_kalavai_core

class DashboardState(rx.State):
    """The state class."""

    is_connected: bool = False
    is_loading: bool = False

    ## START STATE ##
    online_cpus: float = 0
    total_cpus: float = 0
    used_cpus: float = 0

    online_gpus: int = 0
    total_gpus: int = 0
    used_gpus: int = 0

    online_ram: float = 0
    total_ram: float = 0
    used_ram: float = 0

    online_jobs: int = 0
    total_jobs: int = 0

    online_devices: int = 0
    total_devices: int = 0
    
    online_issues: int = 0
    total_issues: int = 0
    ##

    @rx.event(background=True)
    async def load_data(self):
        async with self:
            self.is_loading = True
        
        try:
            resources = request_to_kalavai_core(
                method="get",
                endpoint="fetch_resources",
                json={}
            )

            all_jobs = request_to_kalavai_core(
                method="get",
                endpoint="fetch_job_names"
            )
        except Exception as e:
            return rx.toast.error(f"Missing ACCESS_KEY?\n{e}", position="top-center")
        
        async with self:
            # Resource utilisation
            if "error" in resources:
                pass
            else:
                self.total_cpus = resources["total"]["cpu"]
                self.online_cpus = resources["available"]["cpu"]
                self.used_cpus = 0 #self.total_cpus - self.online_cpus
                try:
                    self.total_gpus = resources["total"]["nvidia.com/gpu"]
                    self.online_gpus = resources["available"]["nvidia.com/gpu"]
                    self.used_gpus = 0 #self.total_gpus - self.online_gpus
                except:
                    pass
                self.total_ram = resources["total"]["memory"] / 1000000000
                self.online_ram = resources["available"]["memory"] / 1000000000
                self.used_ram = 0 #self.total_ram - self.online_ram
                self.online_devices = resources["available"]["n_nodes"]
                self.total_devices = resources["total"]["n_nodes"]
            
            # Jobs
            self.total_jobs = len(all_jobs)
            self.online_jobs = self.total_jobs
            self.is_loading = False
    
    def _generate_gauge(self, value, total, used):
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=value,
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [0, total]}, 
                    'threshold' : {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': used}
                },
                #title={'text': f"{online}/{total} online"}
            )
        )
        return fig
    @rx.var(cache=True)
    def cpus_plot(self) -> Figure:
        return self._generate_gauge(
            value=self.online_cpus,
            total=self.total_cpus,
            used=self.used_cpus
        )
    
    @rx.var(cache=True)
    def gpus_plot(self) -> Figure:
        return self._generate_gauge(
            value=self.online_gpus,
            total=self.total_gpus,
            used=self.used_gpus
        )
    
    @rx.var(cache=True)
    def ram_plot(self) -> Figure:
        return self._generate_gauge(
            value=self.online_ram,
            total=self.total_ram,
            used=self.used_ram
        )

