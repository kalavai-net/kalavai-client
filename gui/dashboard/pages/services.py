"""The users page."""

import reflex as rx

from ..backend.services_state import ServicesState
from ..templates import template
from ..views.services_table import ServicesView


services_view = ServicesView()

@template(route="/services", title="Services", on_load=ServicesState.load_entries)
def services() -> rx.Component:
    """The table page.

    Returns:
        The UI for the table page.

    """
    return rx.vstack(
        rx.heading("Core Services", size="6"),
        rx.text("Core services available in the pool"),
        services_view.main_table(),
        spacing="5",
        width="100%",
    )
