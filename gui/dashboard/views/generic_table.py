import validators

import reflex as rx


class TableView:
    def __init__(self, table_item, table_state, show_columns, item_id, render_mapping=None):
        self.table_item = table_item
        self.table_state = table_state
        self.show_columns = show_columns
        self.item_id = item_id
        self.render_mapping = render_mapping
    
    def _header_cell(self, text: str, icon: str, hover: str, column: str = None) -> rx.Component:
        """Create a header cell with optional sorting functionality."""
        # Check if sorting is available (state has sort_value and set_sort_column)
        has_sorting = hasattr(self.table_state, 'sort_value') and hasattr(self.table_state, 'set_sort_column')
        
        if has_sorting and column:
            # Create sortable header with indicators
            is_sorted = self.table_state.sort_value == column
            sort_icon = rx.cond(
                is_sorted,
                rx.cond(
                    self.table_state.sort_reverse,
                    rx.icon("arrow-down-z-a", size=16),
                    rx.icon("arrow-down-a-z", size=16),
                ),
                rx.icon("arrow-up-down", size=16, opacity=0.4),
            )
            
            header_content = rx.hover_card.root(
                rx.hover_card.trigger(
                    rx.hstack(
                        rx.icon(icon, size=18),
                        rx.text(text),
                        sort_icon,
                        align="center",
                        spacing="2",
                        cursor="pointer",
                    ),
                ),
                rx.hover_card.content(
                    rx.markdown(hover)
                )
            )
            
            # Create a closure to capture the column value
            def create_sort_handler(col):
                return lambda: self.table_state.set_sort_column(col)
            
            return rx.table.column_header_cell(
                rx.box(
                    header_content,
                    on_click=create_sort_handler(column),
                    style={"cursor": "pointer", "user-select": "none"},
                )
            )
        else:
            # Non-sortable header (original behavior)
            return rx.table.column_header_cell(
                rx.hover_card.root(
                    rx.hover_card.trigger(
                        rx.hstack(
                            rx.icon(icon, size=18),
                            rx.text(text),
                            align="center",
                            spacing="2",
                        ),
                    ),
                    rx.hover_card.content(
                        rx.markdown(hover)
                    )
                )
            )
    
    def render_item(self, item, index) -> list[rx.Component]:
        elements = []
        for col in self.show_columns:
            element = item.data[col]
            elements.append(
                self.render_mapping[col](index, element)
            )
        return elements

    def show_item(self, item, index) -> rx.Component:
        bg_color = rx.cond(
            index % 2 == 0,
            rx.color("gray", 1),
            rx.color("accent", 2),
        )
        hover_color = rx.cond(
            index % 2 == 0,
            rx.color("gray", 3),
            rx.color("accent", 3),
        )
        elements = self.render_item(item=item, index=index)
        return rx.table.row(
            *elements,
            style={"_hover": {"bg": hover_color}, "bg": bg_color},
            align="center",
        )
    
    def generate_main_table(self) -> rx.Component:
        return rx.table.root(
            rx.table.header(
                rx.table.row(*[self._header_cell(text=c, icon=i, hover=h, column=c) for c, (i, h) in self.show_columns.items()]),
            ),
            rx.table.body(
                rx.foreach(
                    self.table_state.get_current_page,
                    lambda item, index: self.show_item(item, index),
                )
            ),
            variant="surface",
            size="3",
            width="100%",
        )

    def generate_pagination(self) -> rx.Component:
        return (
            rx.hstack(
                rx.text(
                    "Page ",
                    rx.code(self.table_state.page_number),
                    f" of {self.table_state.total_pages}",
                    justify="end",
                ),
                rx.hstack(
                    rx.icon_button(
                        rx.icon("chevrons-left", size=18),
                        on_click=self.table_state.first_page,
                        opacity=rx.cond(self.table_state.page_number == 1, 0.6, 1),
                        color_scheme=rx.cond(self.table_state.page_number == 1, "gray", "accent"),
                        variant="soft",
                    ),
                    rx.icon_button(
                        rx.icon("chevron-left", size=18),
                        on_click=self.table_state.prev_page,
                        opacity=rx.cond(self.table_state.page_number == 1, 0.6, 1),
                        color_scheme=rx.cond(self.table_state.page_number == 1, "gray", "accent"),
                        variant="soft",
                    ),
                    rx.icon_button(
                        rx.icon("chevron-right", size=18),
                        on_click=self.table_state.next_page,
                        opacity=rx.cond(
                            self.table_state.page_number == self.table_state.total_pages, 0.6, 1
                        ),
                        color_scheme=rx.cond(
                            self.table_state.page_number == self.table_state.total_pages,
                            "gray",
                            "accent",
                        ),
                        variant="soft",
                    ),
                    rx.icon_button(
                        rx.icon("chevrons-right", size=18),
                        on_click=self.table_state.last_page,
                        opacity=rx.cond(
                            self.table_state.page_number == self.table_state.total_pages, 0.6, 1
                        ),
                        color_scheme=rx.cond(
                            self.table_state.page_number == self.table_state.total_pages,
                            "gray",
                            "accent",
                        ),
                        variant="soft",
                    ),
                    align="center",
                    spacing="2",
                    justify="end",
                ),
                spacing="5",
                margin_top="1em",
                align="center",
                width="100%",
                justify="end",
            ),
        )
    
    def generate_table_actions(self) -> rx.Component:
        return rx.flex(
            rx.button(
                rx.icon("refresh-cw", size=20),
                "",
                size="3",
                variant="surface",
                display=["none", "none", "none", "flex"],
                on_click=self.table_state.load_entries(),
                loading=self.table_state.is_loading
            ),
            spacing="3"
        )

    def main_table(self) -> rx.Component:
        return rx.box(
            self.generate_table_actions(),
            self.generate_main_table(),
            self.generate_pagination(),
            width="100%",
        )
