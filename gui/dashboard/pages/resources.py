"""The users page."""

import reflex as rx

from ..backend.resources_state import ResourcesState
from ..templates import template
from ..views.resources_table import ResourcesView


resources_view = ResourcesView()

@template(route="/resources", title="Resources", on_load=ResourcesState.load_entries)
def resources() -> rx.Component:
    """The table page.

    Returns:
        The UI for the table page.

    """
    return rx.vstack(
        rx.heading("Resources", size="6"),
        rx.text("Available Resources the pool is managing"),
        resources_view.main_table(),
        spacing="5",
        width="100%",
    )
