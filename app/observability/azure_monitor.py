import os

from dotenv import load_dotenv
from azure.monitor.opentelemetry import configure_azure_monitor


load_dotenv()


def configure_monitoring() -> None:
    connection_string = os.getenv(
        "APPLICATIONINSIGHTS_CONNECTION_STRING"
    )

    if not connection_string:
        print(
            "[Azure Monitor] "
            "APPLICATIONINSIGHTS_CONNECTION_STRING "
            "not configured. Telemetry disabled."
        )
        return

    configure_azure_monitor(
        connection_string=connection_string,
        enable_live_metrics=True,
    )

    print(
        "[Azure Monitor] "
        "OpenTelemetry configured successfully."
    )