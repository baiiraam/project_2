# """OpenTelemetry tracing setup for the AI Food Analyzer."""

# import os

# from loguru import logger
# from opentelemetry import trace
# from opentelemetry.sdk.resources import SERVICE_NAME, Resource
# from opentelemetry.sdk.trace import TracerProvider
# from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter


# def setup_tracing(service_name: str = "ai-food-analyzer"):
#     """Initialize OpenTelemetry tracing with console exporter."""

#     # Create resource with service info
#     resource = Resource(attributes={
#         SERVICE_NAME: service_name,
#         "service.version": "1.0.0",
#         "deployment.environment": os.getenv("ENVIRONMENT", "development"),
#     })

#     # Set up tracer provider
#     provider = TracerProvider(resource=resource)

#     # Add console exporter (always - for debugging)
#     provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
#     logger.info("✅ Console span exporter enabled - traces will appear in terminal")

#     # Set global provider
#     trace.set_tracer_provider(provider)

#     logger.info("OpenTelemetry tracing initialized")
#     return trace.get_tracer(__name__)


# def get_tracer():
#     """Get the global tracer instance."""
#     return trace.get_tracer(__name__)


# def instrument_fastapi(app):
#     """Automatically instrument FastAPI app."""
#     try:
#         from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
#         FastAPIInstrumentor.instrument_app(app)
#         logger.info("✅ FastAPI instrumented with OpenTelemetry")
#     except ImportError:
#         logger.warning("opentelemetry-instrumentation-fastapi not installed")


# def instrument_requests():
#     """Automatically instrument requests library."""
#     try:
#         from opentelemetry.instrumentation.requests import RequestsInstrumentor
#         RequestsInstrumentor().instrument()
#         logger.info("✅ Requests library instrumented with OpenTelemetry")
#     except ImportError:
#         logger.warning("opentelemetry-instrumentation-requests not installed")


# def instrument_all():
#     """Instrument all available libraries."""
#     instrument_requests()






# """OpenTelemetry tracing setup for the AI Food Analyzer."""

# import os

# from loguru import logger
# from opentelemetry import trace
# from opentelemetry.sdk.resources import SERVICE_NAME, Resource
# from opentelemetry.sdk.trace import TracerProvider
# from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

# # Import trace logger from logging_config
# from src.logging_config import get_logger

# # Create trace-specific logger
# trace_logger = get_logger("tracing", log_type="trace")


# class LoguruSpanExporter(ConsoleSpanExporter):
#     """Custom exporter that writes spans to loguru (and thus to traces.log)."""

#     def export(self, spans):
#         for span in spans:
#             # Format span as readable log message
#             msg = (
#                 f"TRACE | {span.name} | "
#                 f"duration={ (span.end_time - span.start_time) / 1e9:.2f}s | "
#                 f"attributes={dict(span.attributes) if span.attributes else {}}"
#             )
#             trace_logger.info(msg)
#         return super().export(spans)


# def setup_tracing(service_name: str = "ai-food-analyzer"):
#     """Initialize OpenTelemetry tracing with console and file exporters."""

#     # Create resource with service info
#     resource = Resource(attributes={
#         SERVICE_NAME: service_name,
#         "service.version": "1.0.0",
#         "deployment.environment": os.getenv("ENVIRONMENT", "development"),
#     })

#     # Set up tracer provider
#     provider = TracerProvider(resource=resource)

#     # Add console exporter (always - for debugging)
#     provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
#     logger.info("✅ Console span exporter enabled - traces will appear in terminal")

#     # Add file exporter (writes to logs/traces.log)
#     provider.add_span_processor(BatchSpanProcessor(LoguruSpanExporter()))
#     logger.info("✅ File span exporter enabled - traces will appear in logs/traces.log")

#     # Set global provider
#     trace.set_tracer_provider(provider)

#     logger.info("OpenTelemetry tracing initialized")
#     return trace.get_tracer(__name__)


# def get_tracer():
#     """Get the global tracer instance."""
#     return trace.get_tracer(__name__)


# def instrument_fastapi(app):
#     """Automatically instrument FastAPI app."""
#     try:
#         from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
#         FastAPIInstrumentor.instrument_app(app)
#         logger.info("✅ FastAPI instrumented with OpenTelemetry")
#     except ImportError:
#         logger.warning("opentelemetry-instrumentation-fastapi not installed")


# def instrument_requests():
#     """Automatically instrument requests library."""
#     try:
#         from opentelemetry.instrumentation.requests import RequestsInstrumentor
#         RequestsInstrumentor().instrument()
#         logger.info("✅ Requests library instrumented with OpenTelemetry")
#     except ImportError:
#         logger.warning("opentelemetry-instrumentation-requests not installed")


# def instrument_all():
#     """Instrument all available libraries."""
#     instrument_requests()










































"""OpenTelemetry tracing setup for the AI Food Analyzer."""

import os

from loguru import logger
from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

# Import trace logger from logging_config
from src.logging_config import get_logger

# Create trace-specific logger
trace_logger = get_logger("tracing", log_type="trace")


class LoguruSpanExporter(ConsoleSpanExporter):
    """Custom exporter that writes spans to loguru (and thus to traces.log)."""

    def export(self, spans):
        for span in spans:
            # Calculate duration safely (handle None values)
            if span.start_time is not None and span.end_time is not None:
                duration = (span.end_time - span.start_time) / 1e9
            else:
                duration = 0.0

            # Format span as readable log message
            msg = (
                f"TRACE | {span.name} | "
                f"duration={duration:.2f}s | "
                f"attributes={dict(span.attributes) if span.attributes else {}}"
            )
            trace_logger.info(msg)
        return super().export(spans)


def setup_tracing(service_name: str = "ai-food-analyzer"):
    """Initialize OpenTelemetry tracing with console and file exporters."""

    # Create resource with service info
    resource = Resource(attributes={
        SERVICE_NAME: service_name,
        "service.version": "1.0.0",
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
    })

    # Set up tracer provider
    provider = TracerProvider(resource=resource)

    # Add console exporter (always - for debugging)
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    logger.info("✅ Console span exporter enabled - traces will appear in terminal")

    # Add file exporter (writes to logs/traces.log)
    provider.add_span_processor(BatchSpanProcessor(LoguruSpanExporter()))
    logger.info("✅ File span exporter enabled - traces will appear in logs/traces.log")

    # Set global provider
    trace.set_tracer_provider(provider)

    logger.info("OpenTelemetry tracing initialized")
    return trace.get_tracer(__name__)


def get_tracer():
    """Get the global tracer instance."""
    return trace.get_tracer(__name__)


def instrument_fastapi(app):
    """Automatically instrument FastAPI app."""
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)
        logger.info("✅ FastAPI instrumented with OpenTelemetry")
    except ImportError:
        logger.warning("opentelemetry-instrumentation-fastapi not installed")


def instrument_requests():
    """Automatically instrument requests library."""
    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        RequestsInstrumentor().instrument()
        logger.info("✅ Requests library instrumented with OpenTelemetry")
    except ImportError:
        logger.warning("opentelemetry-instrumentation-requests not installed")


def instrument_all():
    """Instrument all available libraries."""
    instrument_requests()
