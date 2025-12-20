import reflex as rx

from ..backend.main_state import MainState


# def draw_user_space_selector():
#     return rx.vstack(
#         rx.hstack(
#             rx.text("Select user space", size="4", weight="bold"),
#             rx.select(
#                 MainState.user_spaces,
#                 value=MainState.selected_user_space,
#                 on_change=[MainState.set_user_space]
#             ),
#         ),
#         rx.markdown(f"**{MainState.selected_user_space}** space will be used to deploy jobs"),
#     )
def draw_resource_quota():
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.markdown(f"Space", ),
                rx.select(
                    MainState.user_spaces,
                    value=MainState.selected_user_space,
                    on_change=[MainState.set_user_space]
                ),
            ),
            rx.cond(
                MainState.user_space_has_quota,
                rx.vstack(
                    rx.flex(
                        rx.grid(
                            rx.text("CPU"),
                            rx.progress(value=MainState.cpu_quota_ratio),
                            rx.text(f"{MainState.used_cpu_quota}/{MainState.max_cpu_quota}"),

                            rx.text("GPU"),
                            rx.progress(value=MainState.gpu_quota_ratio),
                            rx.text(f"{MainState.used_gpu_quota}/{MainState.max_gpu_quota}"),

                            rx.text("RAM"),
                            rx.progress(value=MainState.memory_quota_ratio),
                            rx.text(f"{MainState.used_memory_quota}/{MainState.max_memory_quota} GB"),

                            columns="3",
                            spacing="2",
                            width="100%",
                            grid_template_columns="1fr 3fr 1fr",
                        ),
                        width="100%",
                        align="stretch"
                    ),
                    spacing="4",
                    width="100%",
                ),
                rx.flex(
                    rx.text("The user space has unlimited resources")
                )
            )
        ),
        width="40%",
        variant="surface",
        size="1",
        bg=rx.color("green", 1)
    )
