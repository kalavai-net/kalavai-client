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
                "unschedulable": lambda idx, x: rx.table.cell(self._decorate_schedulable(x, idx)),
                "ready": lambda idx, x: rx.table.cell(device_status_badge(x))
            }
        )
    
    def _decorate_name(self, item, index):
        return rx.hstack(
            rx.center(
                rx.checkbox("", checked=DevicesState.is_selected[index], on_change=lambda checked: DevicesState.set_selected_row(index, checked)),
                rx.dialog.root(
                    rx.dialog.trigger(
                        rx.link(item, on_click=DevicesState.load_node_details(item))
                    ),
                    rx.dialog.content(
                        rx.dialog.title(f"Device Details for {item}"),
                        #rx.dialog.description("Manage device", margin_bottom="10px"),
                        rx.vstack(
                            rx.tabs.root(
                                rx.tabs.list(
                                    rx.tabs.trigger("Available resources", value="resources_tab"),
                                    rx.tabs.trigger("Device labels", value="labels_tab")
                                ),
                                rx.tabs.content(
                                    rx.vstack(
                                        rx.cond(
                                            DevicesState.current_node_resources,
                                            rx.vstack(
                                                rx.foreach(
                                                    DevicesState.current_node_resources.items(),
                                                    lambda x: rx.hstack(
                                                        rx.text(f"{x[0]}: {x[1]}", size="2", color_scheme="gray")
                                                    )
                                                ),
                                                spacing="2"
                                            ),
                                            rx.text("No resources found", size="2", color="gray")
                                        ),
                                        spacing="4"
                                    ),
                                    value="resources_tab"
                                ),
                                rx.tabs.content(
                                    rx.vstack(
                                        # Current labels section
                                        rx.cond(
                                            DevicesState.current_node_labels,
                                            rx.vstack(
                                                rx.foreach(
                                                    DevicesState.current_node_labels.items(),
                                                    lambda x: rx.hstack(
                                                        rx.text(f"{x[0]}: {x[1]}", size="2", color_scheme="gray"),
                                                        spacing="2"
                                                    )
                                                ),
                                                spacing="2"
                                            ),
                                            rx.text("No labels found", size="2", color="gray")
                                        ),
                                        rx.separator(size="4"),
                                        # Add new label section
                                        rx.text("Add New Label", as_="div", size="2", margin_bottom="4px", weight="bold"),
                                        rx.hstack(
                                            rx.input(
                                                placeholder="Label key",
                                                value=DevicesState.new_label_key,
                                                on_change=DevicesState.set_new_label_key,
                                                width="45%"
                                            ),
                                            rx.input(
                                                placeholder="Label value",
                                                value=DevicesState.new_label_value,
                                                on_change=DevicesState.set_new_label_value,
                                                width="45%"
                                            ),
                                            rx.button(
                                                "Add",
                                                on_click=DevicesState.add_node_label,
                                                width="10%",
                                                loading=DevicesState.is_loading
                                            ),
                                            width="100%",
                                            spacing="2"
                                        ),
                                        spacing="4"
                                    ),
                                    value="labels_tab"
                                ),
                                spacing="4"
                            
                            ),
                            rx.dialog.close(
                                rx.button(
                                    "Close",
                                ),
                            ),
                            spacing="4"
                        )
                    )
                )
            )
        )
    
    def _decorate_schedulable(self, item, index):
        return rx.cond(
            item,
            rx.alert_dialog.root(
                rx.alert_dialog.trigger(
                    rx.button(rx.icon("toggle-left", size=16), "", size="2", variant="surface", color_scheme="tomato"),
                ),
                rx.alert_dialog.content(
                    rx.alert_dialog.title("[Admin only] Unblock node schedulable"),
                    rx.alert_dialog.description(
                        "Schedulable devices will receive workloads. Do you want to toggle the state of this node?",
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
                                "OK",
                                color_scheme="grass",
                                variant="solid",
                                on_click=self.table_state.toggle_unschedulable(item, index)
                            ),
                        ),
                        spacing="3",
                        margin_top="16px",
                        justify="end",
                    ),
                    style={"max_width": 450},
                ),
            ),
            rx.alert_dialog.root(
                rx.alert_dialog.trigger(
                    rx.button(rx.icon("toggle-right", size=16), "", size="2", variant="surface", color_scheme="grass"),
                ),
                rx.alert_dialog.content(
                    rx.alert_dialog.title("[Admin only] Block device"),
                    rx.alert_dialog.description(
                        "Unschedulable devices won't receive any more workloads. Do you want to toggle the state of this node?",
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
                                "OK",
                                color_scheme="grass",
                                variant="solid",
                                on_click=self.table_state.toggle_unschedulable(item, index)
                            ),
                        ),
                        spacing="3",
                        margin_top="16px",
                        justify="end",
                    ),
                    style={"max_width": 450},
                ),
            ),
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
                        rx.dialog.description("Invite other users to share resources and add computing power to this pool", margin_bottom="10px"),
                        rx.flex(
                            rx.link("How to join a pool", href="https://kalavai-net.github.io/kalavai-client/getting_started/#2-add-worker-nodes", is_external=True),
                            rx.text("Access mode for the token"),
                            rx.radio(
                                PoolsState.token_modes,
                                on_change=PoolsState.get_pool_token,
                                direction="column"
                            ),
                            rx.cond(
                                PoolsState.token == "",
                                rx.flex(rx.card(rx.text("Select token access"))),
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
                        rx.hstack(
                            rx.text("Machines must be able to see each other (shared private network or with a public IP). This is not required when using Managed pools.", weight="bold", width="85%")
                        ),
                        rx.dialog.close(
                            rx.button(
                                "Close",
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

