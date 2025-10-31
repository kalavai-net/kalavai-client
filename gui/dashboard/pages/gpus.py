"""The users page."""

import reflex as rx

from ..backend.gpus_state import GPUsState
from ..templates import template
from ..views.gpus_table import GPUsView


gpus_view = GPUsView()

@template(route="/gpus", title="GPUS", on_load=GPUsState.load_entries)
def gpus() -> rx.Component:
    """The table page.

    Returns:
        The UI for the table page.

    """
    return rx.vstack(
        rx.heading("GPUs", size="6"),
        rx.text("Available GPUs the pool is managing"),
        gpus_view.main_table(),
        spacing="5",
        width="100%",
    )
