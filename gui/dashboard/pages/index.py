# """The overview page of the app."""
import os

import reflex as rx

from ..templates import template
from ..backend.main_state import MainState
from ..backend.pools_state import PoolsState
from ..views.pools_table import PoolsView

pools_view = PoolsView()


def intro_card(title, icon, text, link_ref, link_is_external):
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon(icon, size=50),
                #rx.text(title, size="3", weight="bold"),
                rx.link(title, href=link_ref, is_external=link_is_external, size="5", weight="bold")
            ),
            rx.text(text),
            spacing="3"
        )
    )


def render_pool_manager() -> rx.Component:
    return rx.flex(
        rx.cond(
            MainState.is_connected,
            rx.vstack(
                rx.text(f"Welcome back", size="8", weight="bold"),
                rx.text("Here are a few links to get you going."),
                rx.grid(
                    intro_card(
                        title="Explore your resources",
                        icon="computer",
                        text="Visit the dashboard for a high level overview of your Kalavai pool",
                        link_is_external=False,
                        link_ref="/dashboard"
                    ),
                    intro_card(
                        title="Add resources to your pool",
                        icon="cpu",
                        text="Want to add your own devices to the pool? Check out how",
                        link_is_external=True,
                        link_ref="https://kalavai-net.github.io/kalavai-client/getting_started/#2-add-worker-nodes"
                    ),
                    intro_card(
                        title="Deploy jobs and models",
                        icon="anchor",
                        text="Put your resources to work by deploying models and workloads withour ready-made templates",
                        link_is_external=False,
                        link_ref="/jobs"
                    ),
                    intro_card(
                        title="Kalavai documentation",
                        icon="notebook",
                        text="Explore what Kalavai has to offer",
                        link_is_external=True,
                        link_ref="https://kalavai-net.github.io/kalavai-client/"
                    ),
                    spacing="4",
                    columns="3",
                ),
                spacing="6"
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
