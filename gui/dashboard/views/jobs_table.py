import reflex as rx

from ..views.generic_table import TableView
from ..backend.jobs_state import JobsState, Job
from ..backend.dashboard_state import DashboardState
from ..components.status_badge import job_badge


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
                "workers": lambda idx, x: rx.table.cell(x),
                "host_nodes": lambda idx, x: rx.table.cell(x),
                "endpoint": lambda idx, x: rx.table.cell(self._decorate_url(x, idx)),
                "status": lambda idx, x: rx.table.cell(job_badge(x))
            }
        )

    def _decorate_url(self, item, index):
        return rx.flex(
            rx.link(item, on_click=JobsState.open_endpoint(index))
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
                rx.checkbox("", checked=JobsState.is_selected[index], on_change=lambda checked: JobsState.set_selected_row(index, checked)),
                rx.dialog.root(
                    rx.dialog.trigger(
                        rx.link(item, on_click=JobsState.load_logs(index))
                    ),
                    rx.dialog.content(
                        rx.hstack(
                            rx.text(f"Job: {item}", size="4", weight="bold"),
                            rx.button(rx.icon("refresh-cw"), on_click=JobsState.load_logs(index)),
                            rx.dialog.close(
                                rx.flex(rx.button("Close", size="2"), justify="end")
                            ),
                            justify="between",
                            width="100%"
                        ),
                        rx.match(
                            JobsState.job_logs,
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
                                                rx.input(type="number", value=JobsState.log_tail, on_change=JobsState.set_log_tail),           
                                            ),
                                            rx.container(
                                                rx.vstack(
                                                    rx.scroll_area(
                                                        rx.code_block(JobsState.job_logs),
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
                                                    rx.code_block(JobsState.job_metadata),
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
                                                    rx.code_block(JobsState.job_status),
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
        return rx.flex(
            rx.hstack(
                rx.dialog.root(
                    rx.dialog.trigger(
                        rx.button(
                            rx.icon("circle-plus", size=20, on_click=[JobsState.load_templates, JobsState.load_node_target_labels]),
                            "New",
                            size="2",
                            variant="surface",
                            display=["none", "none", "none", "flex"],
                            on_click=[JobsState.load_templates, JobsState.load_node_target_labels]
                        )
                    ),
                    rx.dialog.content(
                        rx.dialog.title("Deploy your job"),
                        rx.flex(
                            rx.match(
                                JobsState.current_deploy_step,
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
                                        on_click=JobsState.set_deploy_step(0)
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
                            on_click=JobsState.load_service_logs
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
                                    rx.input(type="number", value=JobsState.log_tail, on_change=JobsState.set_log_tail),           
                                    rx.button(rx.icon("refresh-cw"), on_click=JobsState.load_service_logs),
                                ),
                                rx.vstack(
                                    rx.scroll_area(
                                        rx.code_block(JobsState.service_logs),
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
            ),            
        )
    
    ## DEPLOYMENT STEP SCREENS #
    def select_template(self):
        return rx.flex(
            rx.hstack(
                rx.button(
                    "Next",
                    on_click=JobsState.set_deploy_step(1),
                    disabled=self.table_state.selected_template == "",
                    variant="surface",
                ),
                justify="end"
            ),
            rx.text("1. Select the template you want to deploy", as_="div", size="4", margin_bottom="10px", weight="bold"),
            rx.text("Model template", as_="div", size="2", margin_bottom="4px", weight="bold"),
            rx.select(
                JobsState.templates,
                placeholder="Select model engine",
                on_change=JobsState.load_template_parameters
            ),
            rx.cond(
                JobsState.template_metadata,
                rx.flex(
                    rx.card(
                        rx.link(
                            rx.flex(
                                rx.image(src=JobsState.template_metadata.icon_url, width="100px", height="100px"),
                                rx.box(
                                    rx.vstack(
                                        rx.heading(JobsState.template_metadata.name),
                                        rx.text(
                                            JobsState.template_metadata.description
                                        ),
                                        rx.text(f"Extra info: {JobsState.template_metadata.info}"),
                                    ),
                                    spacing="3"
                                ),
                                spacing="2",
                            ),
                            href=JobsState.template_metadata.docs_url,
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
                    on_click=JobsState.set_deploy_step(0),
                    variant="surface"
                ),
                rx.button(
                    "Next",
                    on_click=[JobsState.set_deploy_step(2), DashboardState.load_data],
                    variant="surface"
                ),
                justify="end"
            ),
            rx.text("2. Select specific nodes (leave blank for auto deploy)", as_="div", size="4", margin_bottom="10px", weight="bold"),
            rx.cond(
                JobsState.selected_labels,
                rx.flex(
                    rx.text('Current labels to select pool nodes', size="1", margin_bottom="4px"),
                    rx.vstack(
                        rx.foreach(
                            JobsState.selected_labels.items(),
                            lambda x: rx.hstack(
                                rx.text(f"{x[0]}: {x[1]}", size="2", color="gray"),
                                spacing="2"
                            )
                        ),
                        spacing="2"
                    ),
                    rx.hstack(
                        rx.text("Selection operator across labels"),
                        rx.radio(["AND", "OR"], direction="row", default_value="AND", on_change=JobsState.set_target_label_mode),
                    ),
                    direction="column"
                ),
                rx.text("No labels selected", size="2", color="gray")
            ),
            rx.hstack(
                rx.select(
                    JobsState.node_target_labels,
                    placeholder="Select target labels",
                    on_change=JobsState.parse_new_target_label
                ),
                rx.button(
                    "Clear",
                    on_click=JobsState.clear_target_labels,
                    color_scheme="gray",
                    width="10%",
                    loading=JobsState.is_loading
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
                    on_click=JobsState.set_deploy_step(1),
                    variant="surface"
                ),
                justify="end"
            ),
            rx.text("3. Populate template values", as_="div", size="4", margin_bottom="10px", weight="bold"),
            # rx.accordion.root(
            #     rx.accordion.item(
            #         header="What do these values mean",
            #         content=rx.markdown(JobsState.template_metadata.values_rules)
            #     ),
            #     collapsible=True,
            #     color_scheme="gray",
            #     variant="outline"
            # ),
            rx.form(
                rx.flex(
                    rx.flex(
                        rx.foreach(
                            JobsState.template_params,
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
                                JobsState.template_params,
                                lambda item: self.show_parameter(item, required=False),
                            )
                        ),
                        collapsible=True,
                        color_scheme="gray",
                        variant="outline"
                    ),
                    rx.text("Available resources", as_="div", size="2", margin_bottom="4px", weight="bold"),
                    rx.tabs.root(
                        rx.tabs.list(
                            rx.tabs.trigger("Workers", value="workers"),
                            rx.tabs.trigger("CPU", value="cpu"),
                            rx.tabs.trigger("RAM", value="ram"),
                            rx.tabs.trigger("GPU", value="gpu"),
                        ),
                        rx.tabs.content(
                            rx.text(f"Workers: {DashboardState.online_devices}/{DashboardState.total_devices}"),
                            value="workers",
                        ),
                        rx.tabs.content(
                            rx.text(f"CPUs: {DashboardState.online_cpus}/{DashboardState.total_cpus}"),
                            value="cpu",
                        ),
                        rx.tabs.content(
                            rx.text(f"RAM: {DashboardState.online_ram:.2f}/{DashboardState.total_ram:.2f} GB"),
                            value="ram",
                        ),
                        rx.tabs.content(
                            rx.text(f"GPUs: {DashboardState.online_gpus}/{DashboardState.total_gpus}"),
                            value="gpu",
                        ),
                        default_value="workers",
                    ),
                    # rx.accordion.root(
                    #     rx.accordion.item(
                    #         header="Available resources",
                    #         content=[
                    #             rx.text(f"Devices: {DashboardState.online_devices}/{DashboardState.total_devices}"),
                    #             rx.text(f"CPUs: {DashboardState.online_cpus:.1f}/{DashboardState.total_cpus:.1f}"),
                    #             rx.text(f"RAM: {DashboardState.online_ram:.2f}/{DashboardState.total_ram:.2f} GB"),
                    #             rx.text(f"GPUs: {DashboardState.online_gpus}/{DashboardState.total_gpus}"),
                    #         ],
                    #         on_click=DashboardState.load_data,
                    #         collapsible=True,
                    #         color_scheme="gray"
                    #     )
                    # ),
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
                on_submit=JobsState.deploy_job
            ),
            direction="column",
            spacing="2",
            margin_botton="10px",
        )
    
    

