"""The jobs page."""

import reflex as rx

from ..backend.jobs_state import JobsState
from ..templates import template
from ..views.jobs_table import JobsView


job_view = JobsView()

@template(route="/jobs", title="Jobs", on_load=JobsState.load_entries)
def jobs() -> rx.Component:
    """The table page.

    Returns:
        The UI for the table page.

    """
    return rx.vstack(
        rx.heading("Job deployments", size="5"),
        job_view.main_table(),
        spacing="8",
        width="100%",
    )
