import reflex as rx

from ..views.generic_table import TableView
from ..backend.resources_state import ResourcesState, Resource
from ..components.status_badge import (
    device_status_badge,
    render_progress
)

class ResourcesView(TableView):

    def __init__(self,):
        super().__init__(
            table_item=Resource,
            table_state=ResourcesState,
            show_columns={
                "node": ("computer", "Where the GPU is located"),
                "ready": ("check-check", "GPU available (connected and not used)"),
                "models": ("gpu", "Model ID for the GPU"),
                "used": ("check", "Used GPU capacity (0-100%)"),
                "disabled": ("notebook-pen", "Node available to receive jobs"),
                "issues": ("info", "Node issues")
            },
            item_id="Name",
            render_mapping={
                "node": lambda idx, x: rx.table.cell(self._decorate_name(x, idx)),
                "models": lambda idx, x: rx.table.cell(rx.text(x, size="1", white_space="pre-line"), max_width="10px"),
                "used": lambda idx, x: rx.table.cell(render_progress(x)),
                "ready": lambda idx, x: rx.table.cell(device_status_badge(x)),
                "disabled": lambda idx, x: rx.table.cell(self._decorate_schedulable(x, idx)),
                "issues": lambda idx, x: rx.table.cell(x, size="2")
            }
        )
    
    def _decorate_status(self, data):
        return rx.flex(
            rx.foreach(
                data,
                lambda x: rx.hstack(
                    rx.text(x, size="2", color_scheme="gray")
                )
            ),
        )


    def _decorate_name(self, item, index):
        return rx.hstack(
            rx.center(
                rx.checkbox("", checked=self.table_state.is_selected[index], on_change=lambda checked: self.table_state.set_selected_row(index, checked)),
                rx.dialog.root(
                    rx.dialog.trigger(
                        rx.link(item, size="2", on_click=self.table_state.load_node_details(item))
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
                                            self.table_state.current_node_resources,
                                            rx.vstack(
                                                rx.foreach(
                                                    self.table_state.current_node_resources.items(),
                                                    lambda x: rx.hstack(
                                                        rx.text(f"{x[0]}: {x[1]}", size="2", color_scheme="gray")
                                                    )
                                                ),
                                                spacing="2"
                                            ),
                                            rx.text("Loading resources", size="2", color="gray")
                                        ),
                                        spacing="4"
                                    ),
                                    value="resources_tab"
                                ),
                                rx.tabs.content(
                                    rx.vstack(
                                        # Current labels section
                                        rx.cond(
                                            self.table_state.current_node_labels,
                                            rx.vstack(
                                                rx.foreach(
                                                    self.table_state.current_node_labels.items(),
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
                                                value=self.table_state.new_label_key,
                                                on_change=self.table_state.set_new_label_key,
                                                width="45%"
                                            ),
                                            rx.input(
                                                placeholder="Label value",
                                                value=self.table_state.new_label_value,
                                                on_change=self.table_state.set_new_label_value,
                                                width="45%"
                                            ),
                                            rx.button(
                                                "Add",
                                                on_click=self.table_state.add_node_label,
                                                width="10%",
                                                loading=self.table_state.is_loading
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
                ),
                spacing="2"
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
                rx.alert_dialog.root(
                    rx.alert_dialog.trigger(
                        rx.button(
                            rx.icon("trash-2", size=20),
                            "Remove",
                            size="2",
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
                    size="2",
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

