from typing import List
import asyncio

import reflex as rx


class PoolState(rx.State):
    """The state class."""

    is_loading: bool = False

    ## START STATE ##
    online_cpus: int = 8
    total_cpus: int = 8
    used_cpus: int = 0

    online_gpus: int = 1
    total_gpus: int = 1
    used_gpus: int = 0

    online_ram: int = 32
    total_ram: int = 32
    used_ram: int = 0

    jobs: int = 0
    devices: int = 1
    issues: int = 0
    ##

    def get_online_cpus(self):
        return self.online_cpus
    
    def get_total_cpus(self):
        return self.total_cpus
    
    def get_used_cpus(self):
        return self.used_cpus
    
    def get_online_gpus(self):
        return self.online_gpus
    
    def get_total_gpus(self):
        return self.total_gpus
    
    def get_used_gpus(self):
        return self.used_gpus
    
    def get_online_ram(self):
        return self.online_ram
    
    def get_total_ram(self):
        return self.total_ram
    
    def get_used_ram(self):
        return self.used_ram
    
    def get_jobs(self):
        return self.jobs
    
    def get_devices(self):
        return self.devices
    
    def get_issues(self):
        return self.issues

    @rx.event(background=True)
    async def load_data(self):
        async with self:
            self.is_loading = True
        await asyncio.sleep(5)
        
        async with self:
            self.is_loading = False

