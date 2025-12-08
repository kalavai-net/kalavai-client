"""Common templates used between pages in the app."""

from __future__ import annotations

import os
from typing import Callable

import reflex as rx

from .. import styles
from ..components.navbar import navbar
from ..components.sidebar import sidebar
from ..backend.main_state import MainState
from ..page_registry import register_page

ACCESS_KEY = os.getenv("ACCESS_KEY", None)

# Meta tags for the app.
default_meta = [
    {
        "name": "viewport",
        "content": "width=device-width, shrink-to-fit=no, initial-scale=1",
    },
]


def menu_item_link(text, href):
    return rx.menu.item(
        rx.link(
            text,
            href=href,
            width="100%",
            color="inherit",
        ),
        _hover={
            "color": styles.accent_color,
            "background_color": styles.accent_text_color,
        },
    )


class ThemeState(rx.State):
    """The state for the theme of the app."""

    accent_color: str = "grass"

    gray_color: str = "gray"

    radius: str = "large"

    scaling: str = "100%"


def template(
    route: str | None = None,
    title: str | None = None,
    description: str | None = None,
    meta: str | None = None,
    script_tags: list[rx.Component] | None = None,
    on_load: rx.EventHandler | list[rx.EventHandler] | None = None,
) -> Callable[[Callable[[], rx.Component]], rx.Component]:
    """The template for each page of the app.

    Args:
        route: The route to reach the page.
        title: The title of the page.
        description: The description of the page.
        meta: Additional meta to add to the page.
        on_load: The event handler(s) called when the page load.
        script_tags: Scripts to attach to the page.

    Returns:
        The template with the page content.

    """

    def decorator(page_content: Callable[[], rx.Component]) -> rx.Component:
        """The template for each page of the app.

        Args:
            page_content: The content of the page.

        Returns:
            The template with the page content.

        """
        # Get the meta tags for the page.
        all_meta = [*default_meta, *(meta or [])]

        def templated_page():
            return rx.cond(
                MainState.is_logged_in,
                rx.flex(
                    rx.cond(
                        MainState.is_logged_in & MainState.is_connected,
                        rx.flex(navbar(), sidebar()),
                        rx.flex()
                    ),
                    rx.flex(
                        rx.vstack(
                            page_content(),
                            width="100%",
                            **styles.template_content_style,
                        ),
                        width="100%",
                        **styles.template_page_style,
                        max_width=[
                            "100%",
                            "100%",
                            "100%",
                            "100%",
                            "100%",
                            styles.max_width,
                        ],
                    ),
                    flex_direction=[
                        "column",
                        "column",
                        "column",
                        "column",
                        "column",
                        "row",
                    ],
                    width="100%",
                    margin="auto",
                    position="relative",
                ),
                render_login()
            )

        # Register the page in our custom registry
        register_page(
            route=route or "/",
            title=title,
            description=description,
        )

        @rx.page(
            route=route,
            title=title,
            description=description,
            meta=all_meta,
            script_tags=script_tags,
            on_load=on_load,
        )
        def theme_wrap():
            return rx.theme(
                templated_page(),
                has_background=True,
                accent_color=ThemeState.accent_color,
                gray_color=ThemeState.gray_color,
                radius=ThemeState.radius,
                scaling=ThemeState.scaling,
            )

        return theme_wrap

    return decorator


def render_login() -> rx.Component:
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