import reflex as rx

from ..views.generic_table import TableView
from ..backend.gpus_state import GPUsState, GPU
from ..components.status_badge import (
    device_status_badge
)

class GPUsView(TableView):

    def __init__(self,):
        super().__init__(
            table_item=GPU,
            table_state=GPUsState,
            show_columns={
                "node": ("computer", "Where the GPU is located"),
                "model": ("microchip", "Model ID for the GPU"),
                "available": ("check", "Number of available models"),
                "total": ("circle", "Total model"),
                "ready": ("check-check", "GPU available (connected and not used)")
                
            },
            item_id="Name",
            render_mapping={
                "node": lambda idx, x: rx.table.cell(x),
                "model": lambda idx, x: rx.table.cell(x),
                "available": lambda idx, x: rx.table.cell(x),
                "total": lambda idx, x: rx.table.cell(x),
                "ready": lambda idx, x: rx.table.cell(device_status_badge(x))
            }
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

