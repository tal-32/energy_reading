import os
from datetime import datetime

import httpx
from nicegui import ui
from pydantic import ValidationError

from shared_lib.model import DATE_FORMAT, ReadingInput

# --- Configuration ---
PRODUCER_URL = os.getenv("PRODUCER_URL", "http://producer:8000")
CONSUMER_URL = os.getenv("CONSUMER_URL", "http://consumer:8000")

# Persistent client for connection pooling
client = httpx.AsyncClient(timeout=10.0)

# --- Logic ---


async def send_reading(
    site_id: str, device_id: str, power_reading: float, timestamp: str
) -> None:
    """Sends a new reading to the Ingestion (Producer) API."""
    try:
        # Validate locally before even trying the network
        payload = ReadingInput(
            site_id=site_id,
            device_id=device_id,
            power_reading=power_reading,
            timestamp=timestamp,
        )
    except ValidationError as e:
        ui.notify(f"Validation Error: {e.errors()[0]['msg']}", type="warning")
        return

    try:
        response = await client.post(
            f"{PRODUCER_URL}/readings", json=payload.model_dump()
        )

        # Check status INSIDE the try block to avoid UnboundLocalError
        if response.is_success:
            # We show the success and the site_id
            ui.notify(
                f"""✅ Reading sent for {site_id}:
                Response: {response.text}
                Status: {response.status_code}""",
                type="positive",
            )
        else:
            # We show the user exactly why the server rejected it
            ui.notify(
                f"❌ Server Error {response.status_code}: {response.text}",
                type="negative",
            )

    except httpx.HTTPError as e:
        ui.notify(f"📡 Connection to Producer failed: {str(e)}", type="negative")


async def fetch_readings(site_id: str, container: ui.column) -> None:
    """Fetches historical readings from the Consumer API and renders a table."""
    if not site_id:
        ui.notify("Please enter a Site ID to search", type="warning")
        return

    # Phase 1: Show Loading State
    container.clear()
    with container:
        ui.spinner(size="lg").classes("self-center mt-4")

    try:
        response = await client.get(f"{CONSUMER_URL}/sites/{site_id}/readings")

        if response.status_code != httpx.codes.OK:
            ui.notify(f"❌ Consumer API error: {response.status_code}", type="negative")
            container.clear()
            return

        data = response.json()

        # Phase 2: Render Data
        container.clear()  # Removes the spinner
        with container:
            if not data:
                ui.label(f"No readings found for site '{site_id}'.").classes(
                    "text-gray-500 italic"
                )
            else:
                columns = [
                    {
                        "name": "timestamp",
                        "label": "Timestamp",
                        "field": "timestamp",
                        "sortable": True,
                    },
                    {
                        "name": "value",
                        "label": "Reading (kWh)",
                        "field": "power_reading",
                        "sortable": True,
                    },
                ]
                ui.table(columns=columns, rows=data, pagination=10).classes(
                    "w-full mt-4 shadow-sm"
                )

    except httpx.HTTPError as e:
        ui.notify(f"📡 Connection to Consumer failed: {str(e)}", type="negative")
        container.clear()


# --- UI Definition ---


def init_ui() -> None:
    """Defines the layout of the dashboard."""
    ui.colors(primary="#3b82f6", secondary="#64748b", accent="#10b981")
    ui.query("body").style("background-color: #f8fafc; font-family: sans-serif;")

    with ui.column().classes("w-full items-center p-8"):
        with ui.card().classes("w-full max-w-4xl p-6 shadow-xl rounded-xl"):
            ui.label("Energy Metrics Dashboard").classes(
                "text-3xl font-bold text-slate-800 mb-2"
            )
            ui.label("Interface for Ingestion and Data Retrieval").classes(
                "text-slate-500 mb-6"
            )

            with ui.tabs().classes("w-full border-b") as tabs:
                submit_tab = ui.tab("Submit Reading", icon="bolt")
                view_tab = ui.tab("View History", icon="history")

            with ui.tab_panels(tabs, value=submit_tab).classes("w-full p-4"):
                # SUBMIT PANEL
                with ui.tab_panel(submit_tab):
                    with ui.column().classes("gap-4"):
                        ui.markdown("### Send to Ingestion API")
                        s_id = (
                            ui.input("Site ID", value="site-001")
                            .props("outlined dense")
                            .classes("w-full")
                        )
                        d_id = (
                            ui.input("Device ID", value="meter-42")
                            .props("outlined dense")
                            .classes("w-full")
                        )
                        val = (
                            ui.number("Power reading", value=0.0, format="%.2f")
                            .props("outlined dense")
                            .classes("w-full")
                        )
                        t_stamp = (
                            ui.input(
                                "Timestamp", value=datetime.now().strftime(DATE_FORMAT)
                            )
                            .props("outlined dense")
                            .classes("w-full")
                        )

                        ui.button(
                            "Dispatch Reading",
                            on_click=lambda: send_reading(
                                site_id=s_id.value,
                                device_id=d_id.value,
                                power_reading=val.value,
                                timestamp=t_stamp.value,
                            ),
                            icon="send",
                        ).classes("w-48 py-2")

                # VIEW PANEL
                with ui.tab_panel(view_tab):
                    with ui.column().classes("gap-4"):
                        ui.markdown("### Fetch Site Readings")
                        results = ui.column().classes("w-full mt-4")
                        with ui.row().classes("w-full items-center"):
                            search_id = (
                                ui.input("Enter Site ID", value="site-001")
                                .props("outlined dense")
                                .classes("grow")
                            )
                            ui.button(
                                "Fetch",
                                on_click=lambda: fetch_readings(
                                    search_id.value, results
                                ),
                                icon="search",
                            ).classes("px-6")


# --- Main Entry Point ---

if __name__ in {"__main__", "__mp_main__"}:
    init_ui()
    # Check if we are in development mode for hot-reload
    is_dev = os.getenv("ENVIRONMENT") == "development"
    ui.run(
        title="Energy System UI", host="0.0.0.0", port=8080, reload=is_dev, dark=False
    )
