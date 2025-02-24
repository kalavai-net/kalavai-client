import reflex as rx


def _job_badge(status: str):
    badge_mapping = {
        "running": ("check", "Running", "green"),
        "pending": ("pause", "Pending", "gray"),
        "working": ("loader", "Working", "yellow"),
        "error": ("ban", "Error", "red"),
    }
    icon, text, color_scheme = badge_mapping.get(
        status, ("loader", "", "gray")
    )
    return rx.badge(
        rx.icon(icon, size=16),
        text,
        color_scheme=color_scheme,
        radius="large",
        variant="surface",
        size="2",
    )

def _device_badge(status: bool):
    badge_mapping = {
        False: ("check-check", "", "green"),
        True: ("circle-x", "", "red"),
    }
    icon, text, color_scheme = badge_mapping.get(
        status, ("loader", "", "gray")
    )
    return rx.badge(
        rx.icon(icon, size=16),
        text,
        color_scheme=color_scheme,
        radius="large",
        variant="surface",
        size="2",
    )


def job_badge(status: str):
    return rx.match(
        status,
        ("running", _job_badge("running")),
        ("pending", _job_badge("pending")),
        ("working", _job_badge("working")),
        ("error", _job_badge("error")),
        _job_badge(""),
    )


def device_pressure_badge(status: bool):
    return rx.match(
        status,
        (True, _device_badge(True)),
        (False, _device_badge(False)),
    )

def device_status_badge(status: bool):
    return rx.match(
        status,
        (True, _device_badge(False)),
        (False, _device_badge(True)),
    )
