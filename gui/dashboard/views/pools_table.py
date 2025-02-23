import reflex as rx

from .generic_table import TableView
from ..backend.pools_state import PoolsState, Pool


class PoolsView(TableView):

    def __init__(self,):
        super().__init__(
            table_item=Pool,
            table_state=PoolsState,
            show_columns={
                "name": ("a-large-small", "Process issues (when nodes have too many processes running)"),
                "owner": ("user", "Node available for scheduling jobs"),
                "description": ("notebook", "RAM issues (when nodes run low on memory)"),
                "join_key": ("key", "Disk memory issues (when nodes run low on free space)"),
                "created_at": ("calendar", "Hostname of the device"),
            },
            item_id="Name",
            render_mapping={
                "created_at": lambda idx, x: rx.table.cell(x),
                "description": lambda idx, x: rx.table.cell(rx.markdown(x), max_width="400px"),
                "join_key": lambda idx, x: rx.box(self.join_dialog(x), justify="center"),
                "name": lambda idx, x: rx.table.cell(x),
                "owner": lambda idx, x: rx.table.cell(x)
            }
        )

    def custom_join(self):
        return rx.vstack(
            rx.text("Access with token", size="4", weight="bold"),
            rx.text("Enter here your joining token to access a private pool."),
            rx.hstack(
                rx.input(placeholder="Paste your token here", on_change=PoolsState.update_token),
                self.join_dialog(PoolsState.token)
            ),
            spacing="3"
        )

    def join_dialog(self, token):
        return rx.dialog.root(
            rx.dialog.trigger(
                rx.button("Join", loading=PoolsState.is_loading, on_click=PoolsState.update_token(token))
            ),
            rx.dialog.content(
                rx.dialog.title("Join the pool"),
                rx.vstack(
                    rx.text("Choose joining option. With 'Join' your machine will be able to run workloads. 'Attach' gives pool access to your machine without running workloads"),
                    rx.radio(
                        PoolsState.join_actions,
                        on_change=PoolsState.set_join_action,
                        direction="column",
                        default_value=PoolsState.selected_join_action
                    ),
                    rx.hstack(
                        rx.dialog.close(
                            rx.button(
                                "Cancel",
                                variant="soft"
                            )
                        ),
                        rx.dialog.close(
                            rx.button(
                                "Join",
                                on_click=PoolsState.join
                            )
                        ),
                    ),
                    spacing="4",
                    
                )
            )
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
                            loading=PoolsState.is_loading,
                            variant="surface",
                            display=["none", "none", "none", "flex"],
                            on_click=PoolsState.load_ip_addresses
                        )
                    ),
                    rx.dialog.content(
                        rx.dialog.title("Create your LLM pool"),
                        rx.dialog.description("Settings for the LLM pool", margin_bottom="10px"),
                        rx.form(
                            rx.flex(
                                rx.input(placeholder="Cluster name", name="cluster_name"),
                                rx.text("Local worker settings", size="3", weight="bold"),
                                rx.select(
                                    PoolsState.ip_addresses,
                                    placeholder="IP address to advertise (must be visible by workers)",
                                    name="ip_address"
                                ),
                                #rx.input(min=0, max=4, placeholder="Number of GPUs to share", name="num_gpus", type="number"),
                                rx.separator(size="4"),
                                direction="column",
                                spacing="2",
                                margin_botton="10px"
                            ),
                            rx.flex(
                                rx.dialog.close(
                                    rx.button(
                                        "Cancel",
                                        color_scheme="gray",
                                        variant="soft",
                                    ),
                                ),
                                rx.dialog.close(
                                    rx.button(
                                        "Create",
                                        type="submit",
                                        on_click=rx.toast("Creating pool...", position="top-center")
                                    ),
                                ),
                                spacing="3",
                                margin_top="16px",
                                justify="end",
                            ),
                            direction="column",
                            spacing="4",
                            margin_botton="10px",
                            on_submit=PoolsState.create
                        )
                    )
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

