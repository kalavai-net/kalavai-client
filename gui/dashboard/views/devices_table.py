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
                        rx.link(item, on_click=DevicesState.load_node_labels(item))
                    ),
                    rx.dialog.content(
                        rx.dialog.title(f"Device Labels: {item}"),
                        rx.dialog.description("Manage labels for this device", margin_bottom="10px"),
                        rx.vstack(
                            # Current labels section
                            rx.text("Current Labels", as_="div", size="2", margin_bottom="4px", weight="bold"),
                            rx.cond(
                                DevicesState.current_node_labels,
                                rx.vstack(
                                    rx.foreach(
                                        DevicesState.current_node_labels.items(),
                                        lambda x: rx.hstack(
                                            rx.text(f"{x[0]}: {x[1]}", size="2"),
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
                spacing="2"
            ),
            style={"padding_x": "10px"}
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
                        rx.dialog.description("Invite other users directly or share the joining token to add new devices to this pool", margin_bottom="10px"),
                        rx.tabs.root(
                            rx.tabs.list(
                                rx.tabs.trigger("Invite", value="invite"),
                                rx.tabs.trigger("Generate token", value="token")
                            ),
                            rx.tabs.content(
                                rx.hstack(
                                    rx.text_area(placeholder="Invite others by email (comma-separated list)", width="85%", on_change=DevicesState.set_invitees),
                                    rx.button("Send", width="15%", on_click=DevicesState.send_invites, loading=DevicesState.is_loading),
                                ),
                                value="invite"
                            ),
                            rx.tabs.content(
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
                                value="token"
                            )
                        ),
                        rx.hstack(
                            rx.text("For private pools, only machines in the same network can connect to the pool. Go Pro to create over-the-internet pools, where any machine with internet access can join", weight="bold", width="85%"),
                            rx.button("Go Pro", color_scheme="purple", width="15%"),
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

