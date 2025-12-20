"""The overview page of the app."""

import reflex as rx

from .. import styles
from ..components.card import card
from ..components.notification import notification
from ..components.resource_quota import draw_resource_quota
from ..templates import template
from ..views.resources_view import (
    cpu_resources,
    gpu_resources,
    memory_resources
)
from ..backend.dashboard_state import DashboardState
from ..backend.pools_state import PoolsState
from ..views.stats_cards import stats_cards


@template(route="/dashboard", title="Dashboard", on_load=[DashboardState.load_data, PoolsState.refresh_status])
def dashboard() -> rx.Component:
    """The overview page.

    Returns:
        The UI for the overview page.

    """
    return rx.vstack(
        #rx.heading(f"Welcome!", size="7"),
        rx.hstack(
            rx.heading(f"Welcome!", size="7"),
            draw_resource_quota(),
            justify="between", width="100%"
        ),
        # rx.flex(
        #     rx.input(
        #         rx.input.slot(rx.icon("search"), padding_left="0"),
        #         placeholder="Search here...",
        #         size="3",
        #         width="100%",
        #         max_width="450px",
        #         radius="large",
        #         style=styles.ghost_input_style,
        #     ),
        #     rx.flex(
        #         notification("bell", "cyan", 12),
        #         notification("message-square-text", "plum", 6),
        #         spacing="4",
        #         width="100%",
        #         wrap="nowrap",
        #         justify="end",
        #     ),
        #     justify="between",
        #     align="center",
        #     width="100%",
        # ),
        rx.hstack(
            rx.text("Pool usage", size="5", font_weight="bold"),
            rx.cond(
                DashboardState.is_loading,
                rx.spinner(),
                None
            )
        ),
        stats_cards(),
        rx.hstack(
            rx.text("Resources", size="5", font_weight="bold"),
            rx.cond(
                DashboardState.is_loading,
                rx.spinner(),
                None
            )
        ),
        rx.grid(
            rx.hstack(
                card(
                    rx.hstack(
                        rx.icon("cpu", size=20),
                        rx.text("CPUs", size="4", weight="medium"),
                        align="center",
                        spacing="2",
                        margin_bottom="1.5em",
                    ),
                    cpu_resources()
                ),
                card(
                    rx.hstack(
                        rx.icon("gpu", size=20),
                        rx.text("GPUs", size="4", weight="medium"),
                        align="center",
                        spacing="2",
                        margin_bottom="1.5em",
                    ),
                    gpu_resources()
                ),
                card(
                    rx.hstack(
                        rx.icon("memory-stick", size=20),
                        rx.text("RAM (GB)", size="4", weight="medium"),
                        align="center",
                        spacing="2",
                        margin_bottom="1.5em",
                    ),
                    memory_resources()
                )
            ),
            width="100%",
        ),
        spacing="8",
        width="100%",
    )
