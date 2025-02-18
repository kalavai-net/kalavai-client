import reflex as rx
from reflex.components.radix.themes.base import LiteralAccentColor

from ..backend.dashboard_state import DashboardState

from .. import styles


def stats_card(
    stat_name: str,
    value: int,
    max_value: int,
    icon: str,
    icon_color: LiteralAccentColor,
) -> rx.Component:
    percentage_change = 0
    change = "increase"
    arrow_icon = "trending-up"
    arrow_color = "grass"
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.badge(
                    rx.icon(tag=icon, size=34),
                    color_scheme=icon_color,
                    radius="full",
                    padding="0.7rem",
                ),
                rx.vstack(
                    rx.hstack(
                        rx.heading(
                            value,
                            size="5",
                            weight="bold",
                        ),
                        rx.heading(
                            "/",
                            size="5",
                            weight="medium",
                        ),
                        rx.heading(
                            max_value,
                            size="5",
                            weight="bold",
                        ),
                        spacing="1"
                    ),
                    rx.text(stat_name, size="4", weight="bold"),
                    spacing="1",
                    height="100%",
                    align_items="start",
                    width="100%"
                ),
                height="100%",
                spacing="4",
                align="center",
                width="100%",
            ),
            rx.hstack(
                rx.hstack(
                    rx.icon(
                        tag=arrow_icon,
                        size=24,
                        color=rx.color(arrow_color, 9),
                    ),
                    rx.text(
                        f"{percentage_change}%",
                        size="3",
                        color=rx.color(arrow_color, 9),
                        weight="medium",
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.text(
                    f"{change} from last month",
                    size="2",
                    color=rx.color("gray", 10),
                ),
                align="center",
                width="100%",
            ),
            spacing="3",
        ),
        size="3",
        width="100%",
        box_shadow=styles.box_shadow_style,
    )


def stats_cards() -> rx.Component:
    return rx.grid(
        stats_card(
            stat_name="Devices",
            value=DashboardState.online_devices,
            max_value=DashboardState.total_devices,
            icon="computer",
            icon_color="blue",
        ),
        stats_card(
            stat_name="Jobs",
            value=DashboardState.online_jobs,
            max_value=DashboardState.total_jobs,
            icon="cpu",
            icon_color="green",
            #extra_char="$",
        ),
        stats_card(
            stat_name="Issues",
            value=DashboardState.online_issues,
            max_value=DashboardState.total_issues,
            icon="badge-alert",
            icon_color="red",
        ),
        gap="1rem",
        grid_template_columns=[
            "1fr",
            "repeat(1, 1fr)",
            "repeat(2, 1fr)",
            "repeat(3, 1fr)",
            "repeat(3, 1fr)",
        ],
        width="100%",
    )
