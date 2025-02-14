"""Navbar component for the app."""

import reflex as rx

from dashboard import styles


def menu_item_icon(icon: str) -> rx.Component:
    return rx.icon(icon, size=20)


def menu_item(text: str, url: str) -> rx.Component:
    """Menu item.

    Args:
        text: The text of the item.
        url: The URL of the item.

    Returns:
        rx.Component: The menu item component.

    """
    # Whether the item is active.
    active = (rx.State.router.page.path == url.lower()) | (
        (rx.State.router.page.path == "/") & text == "Overview"
    )

    return rx.link(
        rx.hstack(
            rx.match(
                text,
                ("Home", menu_item_icon("home")),
                ("Dashboard", menu_item_icon("gauge")),
                ("Devices", menu_item_icon("laptop")),
                ("GPUs", menu_item_icon("microchip")),
                ("Jobs", menu_item_icon("cpu")),
                ("About", menu_item_icon("book-open")),
                ("Settings", menu_item_icon("settings")),
                menu_item_icon("layout-dashboard"),
            ),
            rx.text(text, size="4", weight="regular"),
            color=rx.cond(
                active,
                styles.accent_text_color,
                styles.text_color,
            ),
            style={
                "_hover": {
                    "background_color": rx.cond(
                        active,
                        styles.accent_bg_color,
                        styles.gray_bg_color,
                    ),
                    "color": rx.cond(
                        active,
                        styles.accent_text_color,
                        styles.text_color,
                    ),
                    "opacity": "1",
                },
                "opacity": rx.cond(
                    active,
                    "1",
                    "0.95",
                ),
            },
            align="center",
            border_radius=styles.border_radius,
            width="100%",
            spacing="2",
            padding="0.35em",
        ),
        underline="none",
        href=url,
        width="100%",
    )


def navbar_footer() -> rx.Component:
    """Navbar footer.

    Returns:
        The navbar footer component.

    """
    return rx.vstack(
        rx.link(
            rx.hstack(rx.icon("book-open-text"), rx.text("Docs", size="4")),
            href="https://kalavai-net.github.io/kalavai-client/",
            color_scheme="gray",
            underline="none",
            is_external=True
        ),
        rx.link(
            rx.hstack(rx.icon("github"), rx.text("GitHub", size="3")),
            href="https://github.com/kalavai-net/kalavai-client",
            color_scheme="gray",
            underline="none",
            is_external=True
        ),
        rx.link(
            rx.hstack(rx.icon("external-link"), rx.text("Website", size="4")),
            href="https://kalavai.net/",
            color_scheme="gray",
            underline="none",
            is_external=True
        ),
        rx.spacer(),
        justify="start",
        align="start",
        width="100%",
        padding="0.35em",
    )


def menu_button() -> rx.Component:
    # Get all the decorated pages and add them to the menu.
    from reflex.page import get_decorated_pages

    # The ordered page routes.
    ordered_page_routes = [
        "/",
        "/dashboard",
        "/devices",
        "/gpus",
        "/jobs",
        "/about",
        "/settings",
    ]

    # Get the decorated pages.
    pages = get_decorated_pages()

    # Include all pages even if they are not in the ordered_page_routes.
    ordered_pages = sorted(
        pages,
        key=lambda page: (
            ordered_page_routes.index(page["route"])
            if page["route"] in ordered_page_routes
            else len(ordered_page_routes)
        ),
    )

    return rx.drawer.root(
        rx.drawer.trigger(
            rx.icon("align-justify"),
        ),
        rx.drawer.overlay(z_index="5"),
        rx.drawer.portal(
            rx.drawer.content(
                rx.vstack(
                    rx.hstack(
                        rx.spacer(),
                        rx.drawer.close(rx.icon(tag="x")),
                        justify="end",
                        width="100%",
                    ),
                    rx.divider(),
                    *[
                        menu_item(
                            text=page.get(
                                "title", page["route"].strip("/").capitalize()
                            ),
                            url=page["route"],
                        )
                        for page in ordered_pages
                    ],
                    rx.spacer(),
                    navbar_footer(),
                    spacing="4",
                    width="100%",
                ),
                top="auto",
                left="auto",
                height="100%",
                width="20em",
                padding="1em",
                bg=rx.color("gray", 1),
            ),
            width="100%",
        ),
        direction="right",
    )


def navbar() -> rx.Component:
    """The navbar.

    Returns:
        The navbar component.

    """
    return rx.el.nav(
        rx.hstack(
            # The logo.
            rx.hstack(
                rx.link(
                    rx.color_mode_cond(
                        rx.image(src="/reflex_black.png", height="2em"),
                        rx.image(src="/reflex_white.png", height="2em"),
                    ),
                    href="https://platform.kalavai.net",
                    is_external=True
                ),
                rx.color_mode.button(style={"opacity": "0.8"}),
                spacing="3"
            ),
            rx.spacer(),
            menu_button(),
            align="center",
            width="100%",
            padding_y="1.25em",
            padding_x=["1em", "1em", "2em"],
        ),
        display=["block", "block", "block", "block", "block", "none"],
        position="sticky",
        background_color=rx.color("gray", 1),
        top="0px",
        z_index="5",
        border_bottom=styles.border,
    )
