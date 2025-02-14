"""The overview page of the app."""

import reflex as rx

from ..templates import template
from ..backend.main_state import MainState


def render_login() -> rx.Component:
    return rx.flex(
        rx.cond(
            MainState.is_logged_in,
            rx.card(rx.text(f"Welcome back, {MainState.logged_user}"), rx.button("Sign out", on_click=MainState.signout)),
            rx.card(
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
                max_width="28em",
                size="4",
                width="100%",
            ),
        ),
        align="center",
        justify="center"
    )

def render_pool_manager() -> rx.Component:
    return rx.flex(
        rx.hstack(
            rx.vstack(
                rx.heading("Kalavai pool manager"),
                rx.text("You are not connected to any LLM pool."),
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger("Create", value="start"),
                        rx.tabs.trigger("Join", value="join"),
                        rx.tabs.trigger("Attach", value="attach"),
                        size="2"
                    ),
                    rx.tabs.content(
                        rx.vstack(
                            rx.text("Create a seed node for a new LLM pool"),
                            rx.button("Start", on_click=MainState.connect, loading=MainState.is_loading),
                            spacing="4",
                            margin_top="15px"
                        ),
                        value="start"
                    ),
                    rx.tabs.content(
                        rx.vstack(
                            rx.text("Join an existing LLM pool as a worker. Your machine will be able to execute workloads"),
                            rx.hstack(
                                rx.input(placeholder="Paste joining token", on_blur=MainState.update_token),
                                rx.button("Join", on_click=MainState.connect, loading=MainState.is_loading),
                                spacing="3"
                            ),
                            spacing="4",
                            margin_top="15px"
                        ),
                        value="join"
                    ),
                    rx.tabs.content(
                        rx.vstack(
                            rx.text("Join an existing LLM pool as a controller only. No workloads will be executed in the local machine"),
                            rx.hstack(
                                rx.input(placeholder="Paste joining token", on_blur=MainState.update_token),
                                rx.button("Attach", on_click=MainState.attach, loading=MainState.is_loading),
                                spacing="3"
                            ),
                            spacing="4",
                            margin_top="15px"
                        ),
                        value="attach"
                    )
                ),
                rx.text(MainState.pool_error_message, color_scheme="tomato"),
                spacing="4"
            ),
            rx.box(render_login()),
            width="100%",
            justify="between"
        ),
        width="100%"
    )

def render_home() -> rx.Component:
    return rx.flex(
        rx.text("Connected!", size="5"),
        rx.button("Leave pool", on_click=MainState.stop, loading=MainState.is_loading),
        spacing="4"
        
    )

@template(route="/", title="Home", on_load=MainState.load_state)
def index() -> rx.Component:
    """The overview page.

    Returns:
        The UI for the overview page.

    """
    return rx.cond(
        MainState.is_connected,
        render_home(),
        render_pool_manager()
    )