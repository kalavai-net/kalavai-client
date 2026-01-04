import reflex as rx

from ..views.generic_table import TableView
from ..backend.jobs_state import JobsState, Job
from ..backend.dashboard_state import DashboardState
from ..components.status_badge import job_badge
from ..components.resource_quota import draw_resource_quota


class JobsView(TableView):

    def __init__(self,):
        super().__init__(
            table_item=Job,
            table_state=JobsState,
            show_columns={
                "name": ("notebook-pen", "Name of the job, click to access logs"),
                #"owner": ("user", "User that deployed the job"),
                "workers": ("pickaxe", "Workers status"),
                "host_nodes": ("computer", "Where the job is currently running"),
                "endpoint": ("calendar", "Services exposed (if any) by the job"),
                "status": ("check-check", "<b>Workload status</b><br><br>Running: ready<br>Working: initialising<br>Pending: not enough resources to deploy<br>Error: something went wrong")
            },
            item_id="Name",
            render_mapping={
                "name": lambda idx, x: rx.table.cell(self._decorate_name(x, idx)),
                #"owner": lambda idx, x: rx.table.cell(x),
                "workers": lambda idx, x: rx.table.cell(rx.text(x, white_space="pre-line", size="2")),
                "host_nodes": lambda idx, x: rx.table.cell(rx.text(x, white_space="pre-line", size="2")),
                "endpoint": lambda idx, x: rx.table.cell(self._decorate_url(x, idx)),
                "status": lambda idx, x: rx.table.cell(job_badge(x))
            }
        )

    def _decorate_url(self, item, index):
        return rx.flex(
            rx.link(item, on_click=self.table_state.open_endpoint(index), size="2")
        )
    
    def show_parameter(self, item: rx.Var, required=True):
        def _display(item):
            return rx.tooltip(
                    rx.hstack(
                        rx.text(item["name"]),
                        rx.input(default_value=item["default"], width="60%", name=item["name"]),
                        justify="between"
                    ),
                    content=f'{item["description"]}'
            )
            
        if required:
            return rx.cond(
                item["required"],
                _display(item)
            )
        else:
            return rx.cond(
                ~item["required"],
                _display(item)
            )

    def _decorate_name(self, item, index):
        return rx.hstack(
            rx.center(
                rx.checkbox("", checked=self.table_state.is_selected[index], on_change=lambda checked: self.table_state.set_selected_row(index, checked)),
                rx.dialog.root(
                    rx.dialog.trigger(
                        rx.link(item, on_click=self.table_state.load_logs(index), size="2")
                    ),
                    rx.dialog.content(
                        rx.hstack(
                            rx.text(f"Job: {item}", size="4", weight="bold"),
                            rx.button(rx.icon("refresh-cw"), on_click=self.table_state.load_logs(index)),
                            rx.dialog.close(
                                rx.flex(rx.button("Close", size="2"), justify="end")
                            ),
                            justify="between",
                            width="100%"
                        ),
                        rx.match(
                            self.table_state.job_logs,
                            (None, rx.spinner()),
                            rx.vstack(
                                rx.tabs.root(
                                    rx.tabs.list(
                                        rx.tabs.trigger("Logs", value="logs_tab"),
                                        rx.tabs.trigger("Metadata", value="metadata_tab"),
                                        rx.tabs.trigger("Status", value="status_tab")
                                    ),
                                    rx.tabs.content(
                                        rx.flex(
                                            rx.separator(),
                                            rx.hstack(
                                                rx.text("Lines to fetch"),
                                                rx.input(type="number", value=self.table_state.log_tail, on_change=self.table_state.set_log_tail),           
                                            ),
                                            rx.container(
                                                rx.vstack(
                                                    rx.scroll_area(
                                                        rx.code_block(self.table_state.job_logs),
                                                        style={"height": 500},
                                                        width="100%"
                                                    ),
                                                    overflow_x="auto",
                                                    overflow_y="auto"
                                                ),
                                                stack_children_full_width=True
                                            ),
                                            direction="column",
                                            spacing="4"
                                        ),
                                        spacing="4",
                                        value="logs_tab"
                                    ),
                                    rx.tabs.content(
                                        rx.separator(),
                                        rx.container(
                                            rx.vstack(
                                                rx.scroll_area(
                                                    rx.code_block(self.table_state.job_metadata),
                                                    scrollbars="vertical",
                                                    style={"height": 500}
                                                )
                                            ),
                                            stack_children_full_width=True
                                        ),
                                        spacing="4",
                                        value="metadata_tab"
                                    ),
                                    rx.tabs.content(
                                        rx.separator(),
                                        rx.container(
                                            rx.vstack(
                                                rx.scroll_area(
                                                    rx.code_block(self.table_state.job_status),
                                                    scrollbars="vertical",
                                                    style={"height": 500}
                                                )
                                            ),
                                            stack_children_full_width=True
                                        ),
                                        spacing="4",
                                        value="status_tab"
                                    ),
                                    default_value="logs_tab"
                                )
                            )
                        ),
                        rx.separator(),
                        max_width="90%",
                        width="90%",
                    )
                ),
                spacing="2"
            ),
            style={"padding_x": "10px"}
        )
    
    def generate_table_actions(self) -> rx.Component:
        return rx.hstack(
            rx.dialog.root(
                rx.dialog.trigger(
                    rx.button(
                        rx.icon("circle-plus", size=20, on_click=[self.table_state.load_templates, self.table_state.load_node_target_labels]),
                        "New",
                        size="2",
                        variant="surface",
                        display=["none", "none", "none", "flex"],
                        on_click=[self.table_state.load_templates, self.table_state.load_node_target_labels]
                    )
                ),
                rx.dialog.content(
                    rx.dialog.title("Deploy your job"),
                    rx.flex(
                        rx.match(
                            self.table_state.current_deploy_step,
                            (0, self.select_template()),
                            (1, self.select_targets()),
                            (2, self.select_parameters())
                        ),
                        rx.dialog.close(
                            rx.flex(
                                rx.button(
                                    "Cancel",
                                    variant="soft",
                                    color_scheme="gray",
                                    on_click=self.table_state.set_deploy_step(0)
                                ),
                                justify="start"
                            )
                        ),
                        spacing="4",
                        direction="column"
                    )
                )
            ),
            rx.alert_dialog.root(
                rx.alert_dialog.trigger(
                    rx.button(
                        rx.icon("trash-2", size=20),
                        "Delete",
                        size="2",
                        variant="surface",
                        display=["none", "none", "none", "flex"]
                    )
                ),
                rx.alert_dialog.content(
                    rx.alert_dialog.title("Delete jobs"),
                    rx.alert_dialog.description(
                        "Are you sure you want to delete the selected jobs? This cannot be undone.",
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
            rx.alert_dialog.root(
                rx.alert_dialog.trigger(
                    rx.button(
                        rx.icon("info", size=20),
                        "",
                        size="2",
                        variant="surface",
                        display=["none", "none", "none", "flex"],
                        on_click=self.table_state.load_service_logs
                    )
                ),
                rx.alert_dialog.content(
                    rx.alert_dialog.title("Kalavai API service logs"),
                    rx.alert_dialog.description(
                        "Kalavai API service status.",
                        size="2",
                    ),
                    rx.flex(
                        rx.container(
                            rx.hstack(
                                rx.text("Lines to fetch"),
                                rx.input(type="number", value=self.table_state.log_tail, on_change=self.table_state.set_log_tail),           
                                rx.button(rx.icon("refresh-cw"), on_click=self.table_state.load_service_logs),
                            ),
                            rx.vstack(
                                rx.scroll_area(
                                    rx.code_block(self.table_state.service_logs),
                                    scrollbars="vertical",
                                    style={"height": 500}
                                )
                            ),
                            stack_children_full_width=True
                        ),
                        rx.alert_dialog.cancel(
                            rx.button(
                                "OK",
                                variant="soft",
                                color_scheme="gray",
                            ),
                        ),
                        spacing="3",
                        margin_top="16px",
                        justify="end",
                        direction="column"
                    ),
                    style={"max_width": 1000},
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
            spacing="3",
            justify="end",
            wrap="wrap",
            width="100%",
            padding_bottom="1em",
        )
    
    ## DEPLOYMENT STEP SCREENS #
    def select_template(self):
        return rx.flex(
            rx.hstack(
                rx.button(
                    "Next",
                    on_click=self.table_state.set_deploy_step(1),
                    disabled=self.table_state.selected_template == "",
                    variant="surface",
                ),
                justify="end"
            ),
            rx.text("1. Select the template you want to deploy", as_="div", size="4", margin_bottom="10px", weight="bold"),
            rx.text("Model template", as_="div", size="2", margin_bottom="4px", weight="bold"),
            rx.select(
                self.table_state.templates,
                placeholder="Select model engine",
                on_change=self.table_state.load_template_parameters
            ),
            rx.cond(
                self.table_state.template_metadata,
                rx.flex(
                    rx.card(
                        rx.link(
                            rx.flex(
                                rx.image(src=self.table_state.template_metadata.icon_url, width="100px", height="100px"),
                                rx.box(
                                    rx.vstack(
                                        rx.heading(self.table_state.template_metadata.name),
                                        rx.text(
                                            self.table_state.template_metadata.description
                                        ),
                                        rx.text(f"Extra info: {self.table_state.template_metadata.info}"),
                                    ),
                                    spacing="3"
                                ),
                                spacing="2",
                            ),
                            href=self.table_state.template_metadata.docs_url,
                            is_external=True
                        ),
                        as_child=True,
                        width="60%"
                    ),
                    justify="center"
                ),
                rx.flex()
            ),
            direction="column",
            spacing="2",
            margin_botton="10px",
        )
    
    def select_targets(self):
        return rx.flex(
            rx.hstack(
                rx.button(
                    "Previous",
                    on_click=self.table_state.set_deploy_step(0),
                    variant="surface"
                ),
                rx.button(
                    "Next",
                    on_click=[self.table_state.set_deploy_step(2), DashboardState.load_data],
                    variant="surface"
                ),
                justify="end"
            ),
            rx.text("2. Select specific nodes (leave blank for auto deploy)", as_="div", size="4", margin_bottom="10px", weight="bold"),
            rx.cond(
                self.table_state.selected_labels,
                rx.flex(
                    rx.text('Current labels to select pool nodes', size="1", margin_bottom="4px"),
                    rx.vstack(
                        rx.foreach(
                            self.table_state.selected_labels.items(),
                            lambda x: rx.hstack(
                                rx.text(f"{x[0]}: {x[1]}", size="2", color="gray"),
                                spacing="2"
                            )
                        ),
                        spacing="2"
                    ),
                    rx.hstack(
                        rx.text("Selection operator across labels"),
                        rx.radio(["AND", "OR"], direction="row", default_value="AND", on_change=self.table_state.set_target_label_mode),
                    ),
                    direction="column"
                ),
                rx.text("No labels selected", size="2", color="gray")
            ),
            rx.hstack(
                rx.select(
                    self.table_state.node_target_labels,
                    placeholder="Select target labels",
                    on_change=self.table_state.parse_new_target_label
                ),
                rx.button(
                    "Clear",
                    on_click=self.table_state.clear_target_labels,
                    color_scheme="gray",
                    width="10%",
                    loading=self.table_state.is_loading
                ),
            ),
            #rx.input(placeholder="Force namespace (admin only)", name="force_namespace"),
            direction="column",
            spacing="2",
            margin_botton="10px",
        )
    
    def select_parameters(self):
        return rx.flex(
            rx.hstack(
                rx.button(
                    "Previous",
                    on_click=self.table_state.set_deploy_step(1),
                    variant="surface"
                ),
                justify="end"
            ),
            rx.text("3. Populate template values", as_="div", size="4", margin_bottom="10px", weight="bold"),
            # rx.accordion.root(
            #     rx.accordion.item(
            #         header="What do these values mean",
            #         content=rx.markdown(self.table_state.template_metadata.values_rules)
            #     ),
            #     collapsible=True,
            #     color_scheme="gray",
            #     variant="outline"
            # ),
            rx.form(
                rx.flex(
                    rx.flex(
                        rx.foreach(
                            self.table_state.template_params,
                            lambda item: self.show_parameter(item, required=True),
                        ),
                        spacing="1",
                        justify="between",
                        direction="column"
                    ),
                    rx.separator(size="4"),
                    rx.accordion.root(
                        rx.accordion.item(
                            header="Advanced parameters",
                            content=rx.foreach(
                                self.table_state.template_params,
                                lambda item: self.show_parameter(item, required=False),
                            )
                        ),
                        collapsible=True,
                        color_scheme="gray",
                        variant="outline"
                    ),
                    draw_resource_quota(),
                    rx.dialog.close(
                        rx.hstack(
                            rx.tooltip(
                                rx.button(
                                    "Deploy",
                                    type="submit",
                                    on_click=rx.toast("Deployment submitted", position="top-center")
                                ),
                                content="If your pool does not have enough resources available the job will be queued with **pending** status until sufficient resources are freed."
                            ),
                            justify="end"
                        )
                    ),
                    direction="column",
                    spacing="4",
                    margin_botton="10px"
                ),
                direction="column",
                spacing="4",
                margin_botton="10px",
                on_submit=self.table_state.deploy_job
            ),
            direction="column",
            spacing="2",
            margin_botton="10px",
        )
    
    

