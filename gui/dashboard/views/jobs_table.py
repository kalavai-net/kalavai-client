import reflex as rx

from ..views.generic_table import TableView
from ..backend.jobs_state import JobsState, Job
from ..components.status_badge import job_badge


class JobsView(TableView):

    def __init__(self,):
        super().__init__(
            table_item=Job,
            table_state=JobsState,
            show_columns={
                "name": ("dollar-sign", "Name of the job, click to access logs"),
                #"owner": ("user", "User that deployed the job"),
                "workers": ("pickaxe", "Workers status"),
                "host_nodes": ("computer", "Where the job is currently running"),
                "endpoint": ("calendar", "Services exposed (if any) by the job"),
                "status": ("notebook-pen", "<b>Workload status</b><br><br>Running: ready<br>Working: initialising<br>Pending: not enough resources to deploy<br>Error: something went wrong")
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
    
    def show_parameter(self, item: rx.Var):
        return rx.hstack(
            rx.hover_card.root(
                rx.hover_card.trigger(
                    rx.text(item["name"])
                ),
                rx.hover_card.content(
                    rx.markdown(f'_{item["description"]}_')
                    
                )
            ),            
            #rx.hstack(
            rx.separator(size="1"),
            rx.input(default_value=item["default"], width="60%", name=item["name"]),
            #),
            justify="between"
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
                        rx.match(
                            JobsState.logs,
                            (None, rx.spinner()),
                            rx.vstack(
                                rx.hstack(
                                    rx.flex(
                                        rx.text(f"Logs: {item}", size="4", weight="bold"),
                                        rx.button(rx.icon("refresh-cw"), on_click=JobsState.load_logs(index)),
                                        spacing="3"
                                    ),
                                    rx.dialog.close(
                                        rx.flex(rx.button("Close", size="2"), justify="end")
                                    ),
                                    justify="between",
                                    width="100%"
                                ),
                                rx.separator(),
                                rx.container(
                                    rx.vstack(
                                        rx.scroll_area(
                                            rx.code_block(JobsState.logs),
                                            scrollbars="vertical",
                                            style={"height": 500}
                                        )
                                    ),
                                    stack_children_full_width=True
                                ),
                                spacing="4"
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
                            rx.icon("circle-plus", size=20, on_click=JobsState.load_templates),
                            "",
                            size="3",
                            variant="surface",
                            display=["none", "none", "none", "flex"],
                            on_click=JobsState.load_templates
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
                            "",
                            size="3",
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
                rx.button(
                    rx.icon("refresh-cw", size=20),
                    "",
                    size="3",
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
            rx.text("1. Select the template you want to deploy", size="3", margin_bottom="10px"),
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
                                rx.image(src=JobsState.template_metadata.icon_url, width="100px", height="auto"),
                                rx.box(
                                    rx.heading(JobsState.template_metadata.name),
                                    rx.text(
                                        JobsState.template_metadata.description
                                    ),
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
                    on_click=JobsState.set_deploy_step(2),
                    variant="surface"
                ),
                justify="end"
            ),
            rx.text("2. Target specific nodes (leave blank for auto deploy)", as_="div", size="3", margin_bottom="4px", weight="bold"),
            rx.cond(
                JobsState.selected_labels,
                rx.flex(
                    rx.text('Current labels', size="1", margin_bottom="4px"),
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
                    direction="column"
                ),
                rx.text("No labels selected", size="2", color="gray")
            ),
            rx.hstack(
                rx.input(
                    placeholder="Key",
                    value=JobsState.new_label_key,
                    on_change=JobsState.set_new_label_key,
                    width="45%"
                ),
                rx.input(
                    placeholder="Value",
                    value=JobsState.new_label_value,
                    on_change=JobsState.set_new_label_value,
                    width="45%"
                ),
                rx.button(
                    "Add",
                    on_click=JobsState.add_label,
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
            rx.text("3. Populate template values", size="3", margin_bottom="10px"),
            rx.form(
                rx.flex(
                    rx.text("Template values (hover for more info)", as_="div", size="2", margin_bottom="4px", weight="bold"),
                    rx.separator(size="4"),
                    rx.foreach(
                        JobsState.template_params,
                        lambda item: self.show_parameter(item),
                    ),
                    rx.separator(size="4"),
                    rx.dialog.close(
                        rx.hstack(
                            rx.button(
                                "Deploy",
                                type="submit",
                                on_click=rx.toast("Deployment submitted", position="top-center")
                            ),
                            justify="end"
                        )
                    ),
                    direction="column",
                    spacing="2",
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
    
    

