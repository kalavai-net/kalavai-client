"""The overview page of the app."""

import reflex as rx

from ..templates import template
from ..backend.main_state import MainState
from ..backend.pools_state import PoolsState
from ..views.pools_table import PoolsView


pools_view = PoolsView()


def render_login() -> rx.Component:
    return rx.flex(
        rx.cond(
            MainState.is_logged_in,
            rx.card(rx.text(f"Welcome back, {MainState.logged_user}"), rx.button("Sign out", on_click=MainState.signout, loading=PoolsState.is_loading)),
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
                pools_view.main_table(),
                rx.text(PoolsState.pool_error_message, color_scheme="tomato"),
                spacing="4"
            ),
            rx.box(render_login()),
            width="100%",
            justify="between"
        ),
        width="100%"
    )

def render_home() -> rx.Component:
    return rx.grid(
        rx.hstack(
            rx.text("Worker status", size="5", weight="bold"),
            rx.button(
                rx.icon("refresh-cw", size=20),
                "",
                size="3",
                variant="surface",
                display=["none", "none", "none", "flex"],
                on_click=PoolsState.refresh_status,
                loading=PoolsState.is_loading
            ),
        ),
        rx.hstack(
            rx.cond(
                PoolsState.connected_to_server,
                rx.flex(rx.icon("circle", color="green"), rx.text("Server reachable", size="2"), spacing="3"),
                rx.flex(rx.icon("circle", color="red"), rx.text("Server not reachable", size="2"), spacing="3"),
            )
        ),
        rx.hstack(
            rx.cond(
                PoolsState.agent_running,
                rx.flex(rx.icon("circle", color="green"), rx.text("Worker running", size="2"), spacing="3"),
                rx.flex(rx.icon("circle", color="red"), rx.text("Worker not running", size="2"), spacing="3"),
            )
        ),
        rx.hstack(
            rx.cond(
                PoolsState.is_server,
                rx.flex(rx.icon("server", color="gray"), rx.text("Local node is a server", size="2"), spacing="3"),
                rx.text(""),
            )
        ),
        rx.text("Actions", size="5", weight="bold"),
        rx.hstack(
            rx.alert_dialog.root(
                rx.alert_dialog.trigger(
                    rx.button(
                        rx.icon("circle-stop", size=20),
                        "Stop",
                        size="3",
                        variant="surface",
                        color_scheme="tomato",
                        display=["none", "none", "none", "flex"],
                        loading=PoolsState.is_loading
                    )
                ),
                rx.alert_dialog.content(
                    rx.alert_dialog.title("Leave pool"),
                    rx.alert_dialog.description(
                        "Stopping the worker will leave the pool. Are you sure you want to leave the pool?",
                        size="2",
                    ),
                    rx.flex(
                        rx.alert_dialog.cancel(
                            rx.button(
                                "Cancel",
                                variant="soft",
                                color_scheme="gray",
                            ),
                        ),
                        rx.alert_dialog.action(
                            rx.button(
                                "Leave",
                                color_scheme="red",
                                variant="solid",
                                on_click=PoolsState.stop
                            ),
                        ),
                        spacing="3",
                        margin_top="16px",
                        justify="end",
                    ),
                    style={"max_width": 450},
                ),
            ),
            rx.cond(
                PoolsState.agent_running,
                rx.button(
                    rx.icon("circle-pause"),
                    "Pause",
                    color_scheme="yellow",
                    variant="surface",
                    size="3",
                    on_click=[PoolsState.pause, rx.toast("Pausing worker, you may lose access to the pool until you resume", position="top-center")],
                    loading=PoolsState.is_loading
                ),
                rx.button(
                    rx.icon("circle-play"),
                    "Resume",
                    color_scheme="green",
                    variant="surface",
                    size="3",
                    on_click=[PoolsState.resume, rx.toast("Restarting worker, it may take some time", position="top-center")],
                    loading=PoolsState.is_loading
                )
            ),  
            spacing="3"
        ),
        spacing="5",
    )

@template(route="/", title="Home", on_load=[MainState.load_state, PoolsState.refresh_status])
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