"""The overview page of the app."""

import datetime

import reflex as rx

from .. import styles
from ..components.card import card
from ..components.notification import notification
from ..templates import template
from ..views.resources_view import (
    cpu_resources,
    gpu_resources,
    memory_resources
)
from ..views.charts import (
    area_toggle,
)
from ..backend.dashboard_state import DashboardState
from ..views.stats_cards import stats_cards
from .profile import ProfileState


def _time_data() -> rx.Component:
    return rx.hstack(
        rx.tooltip(
            rx.icon("info", size=20),
            content=f"{(datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%b %d, %Y')} - {datetime.datetime.now().strftime('%b %d, %Y')}",
        ),
        rx.text("Workload", size="4", weight="medium"),
        align="center",
        spacing="2",
        display=["none", "none", "flex"],
    )


def tab_content_header() -> rx.Component:
    return rx.hstack(
        _time_data(),
        area_toggle(),
        align="center",
        width="100%",
        spacing="4",
    )


@template(route="/", title="Overview", on_load=DashboardState.load_data)
def index() -> rx.Component:
    """The overview page.

    Returns:
        The UI for the overview page.

    """
    return rx.vstack(
        rx.heading(f"Welcome, {ProfileState.profile.name}", size="5"),
        rx.flex(
            rx.input(
                rx.input.slot(rx.icon("search"), padding_left="0"),
                placeholder="Search here...",
                size="3",
                width="100%",
                max_width="450px",
                radius="large",
                style=styles.ghost_input_style,
            ),
            rx.flex(
                notification("bell", "cyan", 12),
                notification("message-square-text", "plum", 6),
                spacing="4",
                width="100%",
                wrap="nowrap",
                justify="end",
            ),
            justify="between",
            align="center",
            width="100%",
        ),
        rx.hstack(
            rx.text("Pool monitoring", size="5", font_weight="bold"),
            rx.cond(
                DashboardState.is_loading,
                rx.spinner(),
                None
            )
        ),
        stats_cards(),
        rx.hstack(
            rx.text("Resource utilisation", size="5", font_weight="bold"),
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
                        rx.text("CPUs online", size="4", weight="medium"),
                        align="center",
                        spacing="2",
                        margin_bottom="1.5em",
                    ),
                    rx.hstack(cpu_resources())
                ),
                card(
                    rx.hstack(
                        rx.icon("microchip", size=20),
                        rx.text("GPUs online", size="4", weight="medium"),
                        align="center",
                        spacing="2",
                        margin_bottom="1.5em",
                    ),
                    rx.hstack(gpu_resources())
                ),
                card(
                    rx.hstack(
                        rx.icon("memory-stick", size=20),
                        rx.text("Available RAM (GB)", size="4", weight="medium"),
                        align="center",
                        spacing="2",
                        margin_bottom="1.5em",
                    ),
                    rx.hstack(memory_resources())
                )
            ),
            width="100%",
        ),
        # rx.text("History profile", size="5", font_weight="bold"),
        # card(
        #     rx.hstack(
        #         tab_content_header(),
        #         rx.segmented_control.root(
        #             rx.segmented_control.item("CPU", value="users"),
        #             rx.segmented_control.item("GPU", value="revenue"),
        #             rx.segmented_control.item("RAM", value="orders"),
        #             margin_bottom="1.5em",
        #             default_value="users",
        #             on_change=StatsState.set_selected_tab,
        #         ),
        #         width="100%",
        #         justify="between",
        #     ),
        #     rx.match(
        #         StatsState.selected_tab,
        #         ("users", users_chart()),
        #         ("revenue", revenue_chart()),
        #         ("orders", orders_chart()),
        #     ),
        # ),
        spacing="8",
        width="100%",
    )
