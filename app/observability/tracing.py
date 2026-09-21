from opentelemetry import trace


tracer = trace.get_tracer(
    "healthcare-rag"
)


def get_tracer():
    return tracer