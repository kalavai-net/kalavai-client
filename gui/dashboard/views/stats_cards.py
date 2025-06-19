import reflex as rx
from reflex.components.radix.themes.base import LiteralAccentColor

from ..backend.dashboard_state import DashboardState
from ..backend.pools_state import PoolsState
from .. import styles


def stats_card(
    stat_name: str,
    value: int,
    max_value: int,
    icon: str,
    icon_color: LiteralAccentColor,
    page_link: str = "#",
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
                        rx.cond(
                            max_value >= 0,
                            rx.flex(
                                rx.heading(
                                    "/",
                                    size="5",
                                    weight="medium",
                                ),
                                rx.heading(
                                    max_value,
                                    size="5",
                                    weight="bold",
                                )
                            )
                        ),
                        spacing="1"
                    ),
                    rx.link(stat_name, href=page_link, size="4", weight="bold"),
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

def local_status() -> rx.Component:
    return rx.card(
        rx.stack(
            rx.hstack(
                rx.text("Local status", size="4", weight="bold"),
                rx.button(
                    rx.icon("refresh-cw", size=15),
                    "",
                    size="2",
                    variant="surface",
                    display=["none", "none", "none", "flex"],
                    on_click=PoolsState.refresh_status,
                    loading=PoolsState.is_loading
                ),
                # rx.cond(
                #     PoolsState.agent_running,
                #     rx.button(
                #         rx.icon("circle-pause", size=15),
                #         "",
                #         color_scheme="yellow",
                #         variant="surface",
                #         size="2",
                #         on_click=[PoolsState.pause, rx.toast("Pausing worker, you may lose access to the pool until you resume", position="top-center")],
                #         loading=PoolsState.is_loading
                #     ),
                #     rx.button(
                #         rx.icon("circle-play", size=15),
                #         "",
                #         color_scheme="green",
                #         variant="surface",
                #         size="2",
                #         on_click=[PoolsState.resume, rx.toast("Restarting worker, it may take some time", position="top-center")],
                #         loading=PoolsState.is_loading
                #     )
                # ),
                rx.alert_dialog.root(
                    rx.alert_dialog.trigger(
                        rx.button(
                            rx.icon("circle-stop", size=15),
                            "",
                            size="2",
                            variant="surface",
                            color_scheme="tomato",
                            display=["none", "none", "none", "flex"],
                            #loading=PoolsState.is_loading,
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
                justify="between",
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
            direction="column"
        ),
        box_shadow=styles.box_shadow_style,
    )

def stats_cards() -> rx.Component:
    return rx.grid(
        stats_card(
            stat_name="Devices",
            page_link="/devices",
            value=DashboardState.online_devices,
            max_value=DashboardState.total_devices,
            icon="computer",
            icon_color="blue",
        ),
        stats_card(
            stat_name="Jobs",
            page_link="/jobs",
            value=DashboardState.online_jobs,
            max_value=DashboardState.total_jobs,
            icon="cpu",
            icon_color="green",
            #extra_char="$",
        ),
        local_status(),
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
