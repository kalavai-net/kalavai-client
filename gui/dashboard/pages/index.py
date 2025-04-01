"""The overview page of the app."""
import os

import reflex as rx

from ..templates import template
from ..backend.main_state import MainState
from ..backend.pools_state import PoolsState
from ..views.pools_table import PoolsView

ACCESS_KEY = os.getenv("ACCESS_KEY", None)
pools_view = PoolsView()


def render_login() -> rx.Component:
    if ACCESS_KEY is None:
        return rx.flex(
            rx.card(
                rx.text("Access key not set"),
                rx.text("Please set the ACCESS_KEY environment variable"),
            ),
        )
    
    return rx.flex(
        rx.card(
            rx.cond(
                MainState.is_loading,
                rx.hstack(
                    rx.spinner(size="3"),
                    rx.text("Verifying user key..."),
                    spacing="3"
                ),
                rx.vstack(
                    rx.center(
                        rx.heading(
                            "Enter your user key",
                            size="6",
                            as_="h2",
                            text_align="center",
                            width="100%",
                        ),
                        rx.text("Required for accessing the dashboard", size="2", color_scheme="grass"),
                        direction="column",
                        spacing="4",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text(
                            "User Key",
                            size="3",
                            weight="medium",
                            text_align="left",
                            width="100%",
                        ),
                        rx.input(
                            rx.input.slot(rx.icon("key")),
                            on_blur=MainState.update_user_key,
                            placeholder="Enter your user key",
                            type="password",
                            size="3",
                            width="100%",
                        ),
                        rx.cond(
                            MainState.login_error_message,
                            rx.text(
                                MainState.login_error_message,
                                size="3",
                                color_scheme="red"
                            ),
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    rx.button(
                        "Verify Key",
                        size="3",
                        width="100%",
                        on_click=MainState.authorize(ACCESS_KEY),
                        loading=MainState.is_loading
                    ),
                    spacing="4",
                    width="100%",
                ),
            ),
            max_width="28em",
            size="4",
            width="100%",
        ),
        align="center",
        justify="center"
    )

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
                rx.link(
                    rx.button("Access dashboard"),
                    href="/dashboard",
                    color_scheme="purple",
                    is_external=False,
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
    if ACCESS_KEY is None:
        return render_pool_manager()
    else:
        return rx.cond(
            MainState.is_logged_in,
            render_pool_manager(),
            render_login()
        )
