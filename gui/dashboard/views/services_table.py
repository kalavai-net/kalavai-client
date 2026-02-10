import reflex as rx

from .generic_table import TableView
from ..backend.services_state import ServicesState, Service


class ServicesView(TableView):

    def __init__(self,):
        super().__init__(
            table_item=Service,
            table_state=ServicesState,
            show_columns={
                "namespace": ("user", "Where the GPU is located"),
                "name": ("notebook", "Model ID for the GPU"),
                "internal": ("check", "Used GPU capacity (0-100%)"),
                "external": ("circle", "Total model")
                
            },
            item_id="Name",
            render_mapping={
                "namespace": lambda idx, x: rx.table.cell(x),
                "name": lambda idx, x: rx.table.cell(x),
                "internal": lambda idx, x: rx.table.cell(self._decorate_url(x, idx, False)),
                "external": lambda idx, x: rx.table.cell(self._decorate_url(x, idx, True)),
            }
        )

    def _decorate_url(self, item, index, is_external):
        return rx.flex(
            rx.foreach(
                item,
                lambda x: rx.hstack(
                    rx.cond(
                        is_external,
                        rx.link(x[0], href=x[1], white_space="pre-line", size="2", is_external=is_external),
                        rx.button(x[0], rx.icon("copy", size=10), size="1", on_click=[rx.set_clipboard(x[1]), rx.toast.success("Copied", position="top-center")])
                    ),
                    spacing="2"
                )
            ),
            spacing="1",
            direction="column"
        )
    
    def generate_table_actions(self) -> rx.Component:
        return rx.flex(
            rx.button(
                rx.icon("refresh-cw", size=20),
                "",
                size="2",
                variant="surface",
                display=["none", "none", "none", "flex"],
                on_click=self.table_state.load_entries(),
                loading=self.table_state.is_loading
            ),
            justify="end",
            wrap="wrap",
            padding_bottom="1em",
        )

