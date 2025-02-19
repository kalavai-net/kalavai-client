"""Sidebar component for the app."""

import reflex as rx

from .. import styles


def sidebar_header() -> rx.Component:
    """Sidebar header.

    Returns:
        The sidebar header component.

    """
    return rx.hstack(
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
            rx.spacer(),
            rx.color_mode.button(style={"opacity": "0.8"}),
            spacing="3"
        ),
        rx.spacer(),
        align="center",
        width="100%",
        padding="0.35em",
        margin_bottom="1em",
    )


def sidebar_footer() -> rx.Component:
    """Sidebar footer.

    Returns:
        The sidebar footer component.

    """
    return rx.vstack(
        rx.link(
            rx.hstack(rx.icon("book-open-text"), rx.text("Docs", size="3")),
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
            rx.hstack(rx.icon("external-link"), rx.text("Website", size="3")),
            href="https://kalavai.net/",
            color_scheme="gray",
            underline="none",
            is_external=True
        ),
        #rx.spacer(),
        justify="start",
        align="start",
        width="100%",
        padding="0.35em",
    )


def sidebar_item_icon(icon: str) -> rx.Component:
    return rx.icon(icon, size=18)


def sidebar_item(text: str, url: str) -> rx.Component:
    """Sidebar item.

    Args:
        text: The text of the item.
        url: The URL of the item.

    Returns:
        rx.Component: The sidebar item component.

    """
    # Whether the item is active.
    active = (rx.State.router.page.path == url.lower()) | (
        (rx.State.router.page.path == "/") & text == "Overview"
    )

    return rx.link(
        rx.hstack(
            rx.match(
                text,
                ("Dashboard", sidebar_item_icon("gauge")),
                ("Devices", sidebar_item_icon("laptop")),
                ("GPUs", sidebar_item_icon("microchip")),
                ("Jobs", sidebar_item_icon("cpu")),
                ("About", sidebar_item_icon("book-open")),
                ("Settings", sidebar_item_icon("settings")),
                sidebar_item_icon("layout-dashboard"),
            ),
            rx.text(text, size="3", weight="regular"),
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


def sidebar() -> rx.Component:
    """The sidebar.

    Returns:
        The sidebar component.

    """
    # Get all the decorated pages and add them to the sidebar.
    from reflex.page import get_decorated_pages

    # The ordered page routes.
    ordered_page_routes = [
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

    return rx.flex(
        rx.vstack(
            sidebar_header(),
            rx.vstack(
                *[
                    sidebar_item(
                        text=page.get("title", page["route"].strip("/").capitalize()),
                        url=page["route"],
                    )
                    for page in ordered_pages
                ],
                spacing="1",
                width="100%",
            ),
            rx.spacer(),
            sidebar_footer(),
            justify="end",
            align="end",
            width=styles.sidebar_content_width,
            height="100dvh",
            padding="1em",
        ),
        display=["none", "none", "none", "none", "none", "flex"],
        max_width=styles.sidebar_width,
        width="auto",
        height="100%",
        position="sticky",
        justify="end",
        top="0px",
        left="0px",
        flex="1",
        bg=rx.color("gray", 2),
    )
