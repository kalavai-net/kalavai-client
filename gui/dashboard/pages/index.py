"""The overview page of the app."""

import reflex as rx

from ..templates import template
from ..backend.main_state import MainState
from ..backend.pools_state import PoolsState
from ..views.pools_table import PoolsView


pools_view = PoolsView()


def render_login() -> rx.Component:
    return rx.flex(
        rx.card(
            rx.cond(
                MainState.is_loading,
                rx.hstack(
                    rx.spinner(size="3"),
                    rx.text("Signing in..."),
                    spacing="3"
                ),
                rx.vstack(
                    rx.center(
                        rx.heading(
                            "Sign in to your account",
                            size="6",
                            as_="h2",
                            text_align="center",
                            width="100%",
                        ),
                        rx.text("Required for public and invitation-only pools", size="2", color_scheme="grass"),
                        direction="column",
                        spacing="4",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text(
                            "Email address",
                            size="3",
                            weight="medium",
                            text_align="left",
                            width="100%",
                        ),
                        rx.input(
                            rx.input.slot(rx.icon("user")),
                            on_blur=MainState.update_username,
                            placeholder="user@kalavai.net",
                            type="email",
                            size="3",
                            width="100%",
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.text(
                                "Password",
                                size="3",
                                weight="medium",
                            ),
                            rx.text(
                                MainState.login_error_message,
                                size="3",
                                color_scheme="red"
                            ),
                            justify="between",
                            width="100%",
                        ),
                        rx.input(
                            rx.input.slot(rx.icon("lock")),
                            placeholder="Enter your password",
                            on_blur=MainState.update_password,
                            type="password",
                            size="3",
                            width="100%",
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    rx.button("Sign in", size="3", width="100%", on_click=MainState.signin, loading=MainState.is_loading),
                    rx.center(
                        rx.text("Don't have an account?", size="3"),
                        rx.link("Sign up", href="https://platform.kalavai.net", is_external=True, size="3"),
                        opacity="0.8",
                        spacing="2",
                        direction="row",
                        width="100%",
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
                rx.link(
                    rx.button("Access dashboard"),
                    href="/dashboard",
                    color_scheme="purple",
                    is_external=False,
                ),
                rx.card(rx.text(f"Welcome back, {MainState.logged_user}"), rx.button("Sign out", on_click=MainState.signout, loading=PoolsState.is_loading)),
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
    return rx.cond(
        MainState.is_logged_in,
        render_pool_manager(),
        render_login()
    )
