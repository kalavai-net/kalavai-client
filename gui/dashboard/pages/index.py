# """The overview page of the app."""
import os

import reflex as rx

from ..templates import template
from ..backend.main_state import MainState
from ..backend.pools_state import PoolsState
from ..views.pools_table import PoolsView

pools_view = PoolsView()


def render_pool_manager() -> rx.Component:
    return rx.flex(
        rx.cond(
            MainState.is_connected,
            rx.vstack(
                rx.hstack(
                    rx.card(rx.text(f"Welcome back")),
                    justify="between",
                    width="100%",
                ),
                # rx.link(
                #     rx.button("Access dashboard"),
                #     href="/dashboard",
                #     color_scheme="purple",
                #     is_external=False,
                # ),
                rx.card(
                    rx.vstack(
                        rx.text("Getting started", weight="bold"),
                        rx.link("Explore your available resources", href="/dashboard", is_external=False),
                        rx.link("Add resources to your pool", href="https://kalavai-net.github.io/kalavai-client/getting_started/#2-add-worker-nodes", is_external=True),
                        rx.link("Deploy jobs and models", href="/jobs", is_external=False),
                        rx.link("Kalavai documentation", href="https://kalavai-net.github.io/kalavai-client/", is_external=True),
                        spacing="3"
                    )
                ),
                spacing="3"
            ),
            rx.vstack(
                rx.heading("Kalavai pool manager"),
                rx.text("You are not connected to any LLM pool."),
                rx.text("Pools you have access to", size="4", weight="bold"),
                pools_view.main_table(),
                pools_view.custom_join(),
                spacing="4"
            ),            
        ),
        width="100%",
        justify="center"
    )

@template(route="/", title="Home", on_load=[MainState.load_state, PoolsState.refresh_status])
def index() -> rx.Component:
    """The overview page.

    Returns:
        The UI for the overview page.

    """
    return render_pool_manager()
