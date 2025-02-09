import reflex as rx

from ..views.generic_table import TableView
from ..backend.devices_state import DevicesState, Device
from ..components.status_badge import (
    device_pressure_badge,
    device_status_badge
)

class DevicesView(TableView):

    def __init__(self,):
        super().__init__(
            table_item=Device,
            table_state=DevicesState,
            show_columns={
                "name": ("computer", "Hostname of the device"),
                "memory_pressure": ("user", "RAM issues (when nodes run low on memory)"),
                "disk_pressure": ("cpu", "Disk memory issues (when nodes run low on free space)"),
                "pid_pressure": ("microchip", "Process issues (when nodes have too many processes running)"),
                "unschedulable": ("notebook-pen", "Node available for scheduling jobs"),
                "ready": ("memory-stick", "Node online (connected)"),
            },
            item_id="Name",
            render_mapping={
                "name": lambda idx, x: rx.table.cell(x),
                "memory_pressure": lambda idx, x: rx.table.cell(device_pressure_badge(x)),
                "disk_pressure": lambda idx, x: rx.table.cell(device_pressure_badge(x)),
                "pid_pressure": lambda idx, x: rx.table.cell(device_pressure_badge(x)),
                "unschedulable": lambda idx, x: rx.table.cell(device_pressure_badge(x)),
                "ready": lambda idx, x: rx.table.cell(device_status_badge(x))
            }
        )
    
    def generate_table_actions(self) -> rx.Component:
        return rx.flex(
            rx.button(
                rx.icon("refresh-cw", size=20),
                "",
                size="3",
                variant="surface",
                display=["none", "none", "none", "flex"],
                on_click=self.table_state.load_entries(),
                loading=self.table_state.is_loading
            ),
            justify="end",
            wrap="wrap",
            padding_bottom="1em",
        )

