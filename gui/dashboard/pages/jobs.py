"""The jobs page."""

import reflex as rx

from ..backend.jobs_state import JobsState
from ..backend.main_state import MainState
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
        rx.hstack(
            rx.heading(f"Job deployments", size="6"),
            rx.link(
                rx.text(MainState.selected_user_space, size="3"),
                href="/dashboard",
                underline="none",
                is_external=False),
        ),
        rx.text("Manage your AI workloads. Deploy models across your pool through ready-made templates."),
        job_view.main_table(),
        spacing="5",
        width="100%",
    )
