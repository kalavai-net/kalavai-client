import reflex as rx
from reflex.components.radix.themes.base import LiteralAccentColor

from ..backend.dashboard_state import DashboardState

import plotly.graph_objects as go


def flag(initials: str) -> rx.Component:
    return rx.image(
        src=f"https://flag.vercel.app/s/{initials}.svg",
        loading="lazy",
        decoding="async",
        width="24px",
        height="auto",
        border_radius="2px",
    )


def item(
    country: str, initials: str, progress: int, color: LiteralAccentColor
) -> rx.Component:
    return (
        rx.hstack(
            rx.hstack(
                flag(initials),
                rx.text(
                    country,
                    size="3",
                    weight="medium",
                    display=["none", "none", "none", "none", "flex"],
                ),
                width=["10%", "10%", "10%", "10%", "25%"],
                align="center",
                spacing="3",
            ),
            rx.flex(
                rx.text(
                    f"{progress}%",
                    position="absolute",
                    top="50%",
                    left=["90%", "90%", "90%", "90%", "95%"],
                    transform="translate(-50%, -50%)",
                    size="1",
                ),
                rx.progress(
                    value=progress,
                    height="19px",
                    color_scheme=color,
                    width="100%",
                ),
                position="relative",
                width="100%",
            ),
            width="100%",
            border_radius="10px",
            align="center",
            justify="between",
        ),
    )


def cpu_resources() -> rx.Component:
    return rx.plotly(
        data=DashboardState.cpus_plot,
        layout={
            "margin": dict(l=50, r=50, t=30, b=0),
            "height": 200,
            "width": 300,
            "plot_bgcolor": "rgba(0, 0, 0, 0)",
            "paper_bgcolor": "rgba(0, 0, 0, 0)"},
        use_resize_handler=True,
        width="70%",
        height="70%"
    )

def gpu_resources() -> rx.Component:
    return rx.plotly(
        data=DashboardState.gpus_plot,
        layout={
            "margin": dict(l=50, r=50, t=30, b=0),
            "height": 200,
            "width": 300,
            "plot_bgcolor": "rgba(0, 0, 0, 0)",
            "paper_bgcolor": "rgba(0, 0, 0, 0)"},
        use_resize_handler=True,
        width="70%",
        height="70%"
    )

def memory_resources() -> rx.Component:
    return rx.plotly(
        data=DashboardState.ram_plot,
        layout={
            "margin": dict(l=50, r=50, t=30, b=0),
            "height": 200,
            "width": 300,
            "plot_bgcolor": "rgba(0, 0, 0, 0)",
            "paper_bgcolor": "rgba(0, 0, 0, 0)"},
        use_resize_handler=True,
        width="70%",
        height="70%"
    )
