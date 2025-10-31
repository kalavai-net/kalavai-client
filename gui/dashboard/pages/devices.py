"""The users page."""

import reflex as rx

from ..backend.devices_state import DevicesState
from ..templates import template
from ..views.devices_table import DevicesView


devices_view = DevicesView()

@template(route="/devices", title="Devices", on_load=DevicesState.load_entries)
def devices() -> rx.Component:
    """The table page.

    Returns:
        The UI for the table page.

    """
    return rx.vstack(
        rx.heading("Devices", size="6"),
        rx.text("List all registered devices in the pool"),
        devices_view.main_table(),
        spacing="5",
        width="100%",
    )
