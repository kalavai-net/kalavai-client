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
                "owner": ("user", "User that deployed the job"),
                "workers": ("pickaxe", "Workers status"),
                "endpoint": ("calendar", "Services exposed (if any) by the job"),
                "status": ("notebook-pen", "")
            },
            item_id="Name",
            render_mapping={
                "name": lambda idx, x: rx.table.cell(self._decorate_name(x, idx)),
                "owner": lambda idx, x: rx.table.cell(x),
                "workers": lambda idx, x: rx.table.cell(x),
                "endpoint": lambda idx, x: rx.table.cell(x),
                "status": lambda idx, x: rx.table.cell(job_badge(x))
            }
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
                rx.checkbox("", on_change=lambda checked: JobsState.set_selected_row(index, checked)),
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
                        rx.dialog.title("Deploy your LLM"),
                        rx.dialog.description("Select the model you want to deploy in the pool", margin_bottom="10px"),
                        rx.form(
                            rx.flex(
                                rx.text("Model template", as_="div", size="2", margin_bottom="4px", weight="bold"),
                                rx.select(
                                    JobsState.templates,
                                    placeholder="Select model engine",
                                    on_change=JobsState.load_template_parameters
                                ),
                                rx.text("Template details", as_="div", size="2", margin_bottom="4px", weight="bold"),
                                rx.separator(size="4"),
                                rx.foreach(
                                    JobsState.template_params,
                                    lambda item: self.show_parameter(item),
                                ),
                                rx.separator(size="4"),
                                direction="column",
                                spacing="2",
                                margin_botton="10px"
                            ),
                            rx.flex(
                                rx.text("Deployment details", as_="div", size="2", margin_bottom="4px", weight="bold"),
                                rx.checkbox("Autodetect", default_checked=True),
                                direction="column",
                                spacing="2",
                                margin_botton="10px",
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
                                        "Deploy",
                                        type="submit",
                                        on_click=rx.toast("Deployment submitted", position="top-center")
                                    )
                                ),
                                spacing="3",
                                margin_top="16px",
                                justify="end",
                            ),
                            direction="column",
                            spacing="4",
                            margin_botton="10px",
                            on_submit=JobsState.deploy_job
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

