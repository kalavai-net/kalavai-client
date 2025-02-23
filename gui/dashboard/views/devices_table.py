import reflex as rx

from ..views.generic_table import TableView
from ..backend.devices_state import DevicesState, Device
from ..backend.pools_state import PoolsState
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
                "name": lambda idx, x: rx.table.cell(self._decorate_name(x, idx)),
                "memory_pressure": lambda idx, x: rx.table.cell(device_pressure_badge(x)),
                "disk_pressure": lambda idx, x: rx.table.cell(device_pressure_badge(x)),
                "pid_pressure": lambda idx, x: rx.table.cell(device_pressure_badge(x)),
                "unschedulable": lambda idx, x: rx.table.cell(device_pressure_badge(x)),
                "ready": lambda idx, x: rx.table.cell(device_status_badge(x))
            }
        )
    
    def _decorate_name(self, item, index):
        return rx.hstack(
            rx.center(
                rx.checkbox("", on_change=lambda checked: DevicesState.set_selected_row(index, checked)),
                rx.text(item),
                spacing="2"
            ),
            style={"padding_x": "10px"}
        )
    
    def generate_table_actions(self) -> rx.Component:
        return rx.flex(
            rx.hstack(
                rx.dialog.root(
                    rx.dialog.trigger(
                        rx.button(
                            rx.icon("circle-plus", size=20),
                            "",
                            size="3",
                            variant="surface",
                            display=["none", "none", "none", "flex"],
                            on_click=PoolsState.update_token("")
                        )
                    ),
                    rx.dialog.content(
                        rx.dialog.title("Add new devices to the pool"),
                        rx.dialog.description("Simply share the joining token to add new devices to this pool", margin_bottom="10px"),
                        rx.flex(
                            rx.text("Access mode for the token"),
                            rx.radio(
                                PoolsState.token_modes,
                                on_change=PoolsState.get_pool_token,
                                direction="column"
                            ),
                            rx.cond(
                                PoolsState.token == "",
                                rx.flex(),
                                rx.flex(
                                    rx.card(rx.text(PoolsState.token)),
                                    rx.button(rx.icon("copy"), on_click=[rx.set_clipboard(PoolsState.token), rx.toast.success("Copied", position="top-center")]),
                                ),
                            ),
                            rx.separator(size="4"),
                            direction="column",
                            spacing="2",
                            margin_botton="10px"
                        ),
                        rx.dialog.close(
                            rx.button(
                                "OK",
                                #on_click=rx.toast("Creating pool...", position="top-center")
                            ),
                        ),
                        spacing="3",
                        margin_top="16px",
                        justify="end",
                    )
                ),
                rx.alert_dialog.root(
                    rx.alert_dialog.trigger(
                        rx.button(
                            rx.icon("trash-2", size=20),
                            "",
                            size="3",
                            variant="surface",
                            display=["none", "none", "none", "flex"]
                        )
                    ),
                    rx.alert_dialog.content(
                        rx.alert_dialog.title("Delete devices"),
                        rx.alert_dialog.description(
                            "Are you sure you want to delete the selected devices? This cannot be undone.",
                            size="2",
                        ),
                        rx.flex(
                            rx.alert_dialog.cancel(
                                rx.button(
                                    "Cancel",
                                    variant="soft",
                                    color_scheme="gray",
                                ),
                            ),
                            rx.alert_dialog.action(
                                rx.button(
                                    "Delete",
                                    color_scheme="red",
                                    variant="solid",
                                    on_click=self.table_state.remove_entries()
                                ),
                            ),
                            spacing="3",
                            margin_top="16px",
                            justify="end",
                        ),
                        style={"max_width": 450},
                    ),
                ),
                rx.button(
                    rx.icon("refresh-cw", size=20),
                    "",
                    size="3",
                    variant="surface",
                    display=["none", "none", "none", "flex"],
                    on_click=self.table_state.load_entries(),
                    loading=self.table_state.is_loading
                ),
            ),
            justify="end",
            wrap="wrap",
            padding_bottom="1em",
        )

