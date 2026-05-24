# """Logging configuration using loguru - with separate files for different log types."""

# from typing import Optional
# import os
# import sys
# from pathlib import Path

# from loguru import logger

# from src.config import get_settings

# settings = get_settings()


# def setup_logging():
#     """Configure loguru logging with separate files for different log types."""

#     # Remove default handler
#     logger.remove()

#     # Get log level from settings
#     log_level = settings.LOG_LEVEL.upper()

#     # Create logs directory
#     log_dir = Path("logs")
#     log_dir.mkdir(exist_ok=True)

#     # ============================================================
#     # 1. MAIN APPLICATION LOG (console + file)
#     # ============================================================

#     # Console handler (human-readable, with colors)
#     logger.add(
#         sys.stdout,
#         format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
#         level=log_level,
#         colorize=True,
#         filter=lambda record: record["extra"].get("log_type", "app") == "app"
#     )

#     # Main app log file
#     logger.add(
#         log_dir / "app.log",
#         format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
#         level=log_level,
#         rotation="100 MB",
#         retention="30 days",
#         compression="zip",
#         filter=lambda record: record["extra"].get("log_type", "app") == "app"
#     )

#     # ============================================================
#     # 2. TELEMETRY/TRACING LOG (OpenTelemetry spans)
#     # ============================================================
#     logger.add(
#         log_dir / "traces.log",
#         format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
#         level="INFO",
#         rotation="50 MB",
#         retention="7 days",
#         filter=lambda record: record["extra"].get("log_type") == "trace"
#     )

#     # ============================================================
#     # 3. COST TELEMETRY LOG
#     # ============================================================
#     logger.add(
#         log_dir / "costs.log",
#         format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
#         level="INFO",
#         rotation="50 MB",
#         retention="90 days",
#         filter=lambda record: record["extra"].get("log_type") == "cost"
#     )

#     # ============================================================
#     # 4. API REQUEST LOG (HTTP requests/responses)
#     # ============================================================
#     logger.add(
#         log_dir / "api.log",
#         format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
#         level="INFO",
#         rotation="100 MB",
#         retention="14 days",
#         filter=lambda record: record["extra"].get("log_type") == "api"
#     )

#     # ============================================================
#     # 5. ERROR LOG (all errors in one place)
#     # ============================================================
#     logger.add(
#         log_dir / "errors.log",
#         format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
#         level="ERROR",
#         rotation="50 MB",
#         retention="90 days",
#         filter=lambda record: record["level"].name == "ERROR"
#     )

#     # ============================================================
#     # 6. DEBUG LOG (detailed debugging, only when LOG_LEVEL=DEBUG)
#     # ============================================================
#     if log_level == "DEBUG":
#         logger.add(
#             log_dir / "debug.log",
#             format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
#             level="DEBUG",
#             rotation="50 MB",
#             retention="3 days",
#         )

#     # Suppress noisy third-party libraries
#     logger.disable("httpx")
#     logger.disable("httpcore")
#     logger.disable("urllib3")

#     # Bind initial context
#     logger.bind(service="food-analyzer")

#     logger.info(f"Logging initialized at level {log_level}")
#     logger.info(f"Log files in: {log_dir.absolute()}/")
#     logger.info(f"  - app.log (application)")
#     logger.info(f"  - traces.log (OpenTelemetry spans)")
#     logger.info(f"  - costs.log (cost telemetry)")
#     logger.info(f"  - api.log (API requests)")
#     logger.info(f"  - errors.log (all errors)")

#     return logger


# def get_logger(name: Optional[str] = None, log_type: str = "app"):
#     """Get a logger instance with optional context and type."""
#     if name:
#         return logger.bind(module=name, log_type=log_type)
#     return logger.bind(log_type=log_type)












# from typing import Optional

# """Logging configuration using loguru with separate files for different log types.

# Log files structure:
#     logs/
#     ├── app.log      - General application messages
#     ├── api.log      - HTTP request/response logs
#     ├── costs.log    - Cost telemetry (API spending)
#     ├── traces.log   - OpenTelemetry spans
#     ├── errors.log   - All errors (consolidated)
#     └── debug.log    - Detailed debug (only when LOG_LEVEL=DEBUG)
# """

# import sys
# from pathlib import Path

# from loguru import logger

# from src.config import get_settings

# # Track if logging has been initialized
# _LOGGING_SETUP_DONE = False
# _settings = None


# def _get_settings():
#     """Get settings instance (lazy loading to avoid circular imports)."""
#     global _settings
#     if _settings is None:
#         _settings = get_settings()
#     return _settings


# def setup_logging():
#     """Configure loguru logging with separate files for different log types."""
#     global _LOGGING_SETUP_DONE

#     if _LOGGING_SETUP_DONE:
#         return logger

#     settings = _get_settings()
#     log_level = settings.LOG_LEVEL.upper()

#     # Create logs directory
#     log_dir = Path("logs")
#     log_dir.mkdir(exist_ok=True)

#     # Remove default handler
#     logger.remove()

#     # ============================================================
#     # 1. CONSOLE HANDLER (human-readable, colored)
#     # ============================================================
#     # Only shows general app messages, not API logs or traces
#     logger.add(
#         sys.stdout,
#         format=(
#             "<green>{time:HH:mm:ss}</green> | "
#             "<level>{level: <8}</level> | "
#             "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
#             "<level>{message}</level>"
#         ),
#         level=log_level,
#         colorize=True,
#         filter=lambda record: record["extra"].get("log_type", "app") == "app"
#     )

#     # ============================================================
#     # 2. MAIN APPLICATION LOG (app.log)
#     # ============================================================
#     logger.add(
#         log_dir / "app.log",
#         format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
#         level=log_level,
#         rotation="100 MB",
#         retention="30 days",
#         compression="zip",
#         filter=lambda record: record["extra"].get("log_type", "app") == "app"
#     )

#     # ============================================================
#     # 3. API REQUEST LOG (api.log)
#     # ============================================================
#     # Logs HTTP requests, responses, durations
#     logger.add(
#         log_dir / "api.log",
#         format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
#         level="INFO",
#         rotation="100 MB",
#         retention="14 days",
#         compression="zip",
#         filter=lambda record: record["extra"].get("log_type") == "api"
#     )

#     # ============================================================
#     # 4. COST TELEMETRY LOG (costs.log)
#     # ============================================================
#     # Tracks API spending, token usage, costs per call
#     logger.add(
#         log_dir / "costs.log",
#         format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
#         level="INFO",
#         rotation="50 MB",
#         retention="90 days",
#         compression="zip",
#         filter=lambda record: record["extra"].get("log_type") == "cost"
#     )

#     # ============================================================
#     # 5. OPENTELEMETRY TRACES LOG (traces.log)
#     # ============================================================
#     # Logs span information, durations, attributes
#     logger.add(
#         log_dir / "traces.log",
#         format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
#         level="INFO",
#         rotation="50 MB",
#         retention="7 days",
#         compression="zip",
#         filter=lambda record: record["extra"].get("log_type") == "trace"
#     )

#     # ============================================================
#     # 6. ERRORS ONLY LOG (errors.log)
#     # ============================================================
#     # Consolidated error log for debugging
#     logger.add(
#         log_dir / "errors.log",
#         format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
#         level="ERROR",
#         rotation="50 MB",
#         retention="90 days",
#         compression="zip",
#     )

#     # ============================================================
#     # 7. DEBUG LOG (debug.log) - only when LOG_LEVEL=DEBUG
#     # ============================================================
#     if log_level == "DEBUG":
#         logger.add(
#             log_dir / "debug.log",
#             format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
#             level="DEBUG",
#             rotation="50 MB",
#             retention="3 days",
#             compression="zip",
#         )

#     # ============================================================
#     # Suppress noisy third-party libraries
#     # ============================================================
#     logger.disable("httpx")
#     logger.disable("httpcore")
#     logger.disable("urllib3")
#     logger.disable("requests_cache")

#     # Bind initial context
#     logger.bind(service="food-analyzer")

#     _LOGGING_SETUP_DONE = True

#     # Log startup information
#     logger.info(f"Logging initialized | Level: {log_level}")
#     logger.info(f"Log directory: {log_dir.absolute()}/")
#     logger.info("Log files:")
#     logger.info("  ├── app.log     - Application messages")
#     logger.info("  ├── api.log     - HTTP requests")
#     logger.info("  ├── costs.log   - Cost telemetry")
#     logger.info("  ├── traces.log  - OpenTelemetry spans")
#     logger.info("  ├── errors.log  - All errors")
#     if log_level == "DEBUG":
#         logger.info("  └── debug.log   - Debug messages")
#     else:
#         logger.info("  └── (set LOG_LEVEL=DEBUG for debug.log)")

#     return logger


# def get_logger(name: Optional[str] = None, log_type: str = "app"):
#     """Get a logger instance with optional context and log type.

#     Args:
#         name: Module/component name for context
#         log_type: Type of logs ('app', 'api', 'cost', 'trace')

#     Returns:
#         Logger instance bound with the specified context
#     """
#     if name:
#         return logger.bind(module=name, log_type=log_type)
#     return logger.bind(log_type=log_type)


# def get_log_files_info() -> dict:
#     """Get information about log files.

#     Returns:
#         Dictionary with log file paths and sizes
#     """
#     log_dir = Path("logs")
#     if not log_dir.exists():
#         return {"error": "Log directory not found"}

#     files_info = {}
#     for log_file in ["app.log", "api.log", "costs.log", "traces.log", "errors.log", "debug.log"]:
#         file_path = log_dir / log_file
#         if file_path.exists():
#             files_info[log_file] = {
#                 "path": str(file_path.absolute()),
#                 "size_bytes": file_path.stat().st_size,
#                 "size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
#             }

#     return files_info



































# import sys
# from pathlib import Path
# from typing import Optional

# from loguru import logger

# from src.config import get_settings

# """Logging configuration using loguru with separate files for different log types.

# Log files structure:
#     logs/
#     ├── app.log      - General application messages
#     ├── api.log      - HTTP request/response logs
#     ├── costs.log    - Cost telemetry (API spending)
#     ├── traces.log   - OpenTelemetry spans
#     ├── errors.log   - All errors (consolidated)
#     └── debug.log    - Detailed debug (only when LOG_LEVEL=DEBUG)
# """



# # Track if logging has been initialized
# _LOGGING_SETUP_DONE = False
# _settings = None


# def _get_settings():
#     """Get settings instance (lazy loading to avoid circular imports)."""
#     global _settings
#     if _settings is None:
#         _settings = get_settings()
#     return _settings


# def setup_logging():
#     """Configure loguru logging with separate files for different log types."""
#     global _LOGGING_SETUP_DONE

#     if _LOGGING_SETUP_DONE:
#         return logger

#     settings = _get_settings()
#     log_level = settings.LOG_LEVEL.upper()

#     # Create logs directory
#     log_dir = Path("logs")
#     log_dir.mkdir(exist_ok=True)

#     # Remove default handler
#     logger.remove()

#     # ============================================================
#     # 1. CONSOLE HANDLER (human-readable, colored)
#     # ============================================================
#     # Only shows general app messages, not API logs or traces
#     logger.add(
#         sys.stdout,
#         format=(
#             "<green>{time:HH:mm:ss}</green> | "
#             "<level>{level: <8}</level> | "
#             "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
#             "<level>{message}</level>"
#         ),
#         level=log_level,
#         colorize=True,
#         filter=lambda record: record["extra"].get("log_type", "app") == "app"
#     )

#     # ============================================================
#     # 2. MAIN APPLICATION LOG (app.log)
#     # ============================================================
#     logger.add(
#         log_dir / "app.log",
#         format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
#         level=log_level,
#         rotation="100 MB",
#         retention="30 days",
#         compression="zip",
#         filter=lambda record: record["extra"].get("log_type", "app") == "app"
#     )

#     # ============================================================
#     # 3. API REQUEST LOG (api.log)
#     # ============================================================
#     # Logs HTTP requests, responses, durations
#     logger.add(
#         log_dir / "api.log",
#         format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
#         level="INFO",
#         rotation="100 MB",
#         retention="14 days",
#         compression="zip",
#         filter=lambda record: record["extra"].get("log_type") == "api"
#     )

#     # ============================================================
#     # 4. COST TELEMETRY LOG (costs.log)
#     # ============================================================
#     # Tracks API spending, token usage, costs per call
#     logger.add(
#         log_dir / "costs.log",
#         format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
#         level="INFO",
#         rotation="50 MB",
#         retention="90 days",
#         compression="zip",
#         filter=lambda record: record["extra"].get("log_type") == "cost"
#     )

#     # ============================================================
#     # 5. OPENTELEMETRY TRACES LOG (traces.log)
#     # ============================================================
#     # Logs span information, durations, attributes
#     logger.add(
#         log_dir / "traces.log",
#         format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
#         level="INFO",
#         rotation="50 MB",
#         retention="7 days",
#         compression="zip",
#         filter=lambda record: record["extra"].get("log_type") == "trace"
#     )

#     # ============================================================
#     # 6. ERRORS ONLY LOG (errors.log)
#     # ============================================================
#     # Consolidated error log for debugging
#     logger.add(
#         log_dir / "errors.log",
#         format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
#         level="ERROR",
#         rotation="50 MB",
#         retention="90 days",
#         compression="zip",
#     )

#     # ============================================================
#     # 7. DEBUG LOG (debug.log) - only when LOG_LEVEL=DEBUG
#     # ============================================================
#     if log_level == "DEBUG":
#         logger.add(
#             log_dir / "debug.log",
#             format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
#             level="DEBUG",
#             rotation="50 MB",
#             retention="3 days",
#             compression="zip",
#         )

#     # ============================================================
#     # Suppress noisy third-party libraries
#     # ============================================================
#     logger.disable("httpx")
#     logger.disable("httpcore")
#     logger.disable("urllib3")
#     logger.disable("requests_cache")

#     # Bind initial context
#     logger.bind(service="food-analyzer")

#     _LOGGING_SETUP_DONE = True

#     # Log startup information
#     logger.info(f"Logging initialized | Level: {log_level}")
#     logger.info(f"Log directory: {log_dir.absolute()}/")
#     logger.info("Log files:")
#     logger.info("  ├── app.log     - Application messages")
#     logger.info("  ├── api.log     - HTTP requests")
#     logger.info("  ├── costs.log   - Cost telemetry")
#     logger.info("  ├── traces.log  - OpenTelemetry spans")
#     logger.info("  ├── errors.log  - All errors")
#     if log_level == "DEBUG":
#         logger.info("  └── debug.log   - Debug messages")
#     else:
#         logger.info("  └── (set LOG_LEVEL=DEBUG for debug.log)")

#     return logger


# def get_logger(name: Optional[str] = None, log_type: str = "app"):
#     """Get a logger instance with optional context and log type.

#     Args:
#         name: Module/component name for context
#         log_type: Type of logs ('app', 'api', 'cost', 'trace')

#     Returns:
#         Logger instance bound with the specified context
#     """
#     if name:
#         return logger.bind(module=name, log_type=log_type)
#     return logger.bind(log_type=log_type)


# def get_log_files_info() -> dict:
#     """Get information about log files.

#     Returns:
#         Dictionary with log file paths and sizes
#     """
#     log_dir = Path("logs")
#     if not log_dir.exists():
#         return {"error": "Log directory not found"}

#     files_info = {}
#     for log_file in ["app.log", "api.log", "costs.log", "traces.log", "errors.log", "debug.log"]:
#         file_path = log_dir / log_file
#         if file_path.exists():
#             files_info[log_file] = {
#                 "path": str(file_path.absolute()),
#                 "size_bytes": file_path.stat().st_size,
#                 "size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
#             }

#     return files_info




































# """Logging configuration using loguru with separate files for different log types."""

# import os
# import sys
# from pathlib import Path
# from typing import Optional

# from loguru import logger

# from src.config import get_settings

# # Track if logging has been initialized
# _LOGGING_SETUP_DONE = False
# _settings = None


# def _get_settings():
#     """Get settings instance (lazy loading to avoid circular imports)."""
#     global _settings
#     if _settings is None:
#         _settings = get_settings()
#     return _settings


# def setup_logging():
#     """Configure loguru logging with separate files for different log types."""
#     global _LOGGING_SETUP_DONE

#     if _LOGGING_SETUP_DONE:
#         return logger

#     settings = _get_settings()
#     log_level = settings.LOG_LEVEL.upper()

#     # Check if we're in Docker/container environment
#     in_container = os.path.exists("/.dockerenv") or os.getenv("LOG_FORMAT") == "json"

#     # Create logs directory (only if not in container or if file logging is desired)
#     log_dir = Path("logs")
#     if not in_container:
#         log_dir.mkdir(exist_ok=True)

#     # Remove default handler
#     logger.remove()

#     # ============================================================
#     # CONSOLE HANDLER (JSON for Docker/Loki, pretty for dev)
#     # ============================================================
#     if in_container:
#         # JSON format for Loki - sends structured logs
#         logger.add(
#             sys.stdout,
#             format="{message}",
#             level=log_level,
#             serialize=True,  # ← JSON output!
#         )
#     else:
#         # Pretty format for development
#         logger.add(
#             sys.stdout,
#             format=(
#                 "<green>{time:HH:mm:ss}</green> | "
#                 "<level>{level: <8}</level> | "
#                 "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
#                 "<level>{message}</level>"
#             ),
#             level=log_level,
#             colorize=True,
#             filter=lambda record: record["extra"].get("log_type", "app") == "app"
#         )

#     # ============================================================
#     # FILE HANDLERS (only in development, not in Docker)
#     # ============================================================
#     if not in_container:
#         # Main application log
#         logger.add(
#             log_dir / "app.log",
#             format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
#             level=log_level,
#             rotation="100 MB",
#             retention="30 days",
#             compression="zip",
#             filter=lambda record: record["extra"].get("log_type", "app") == "app"
#         )

#         # API request log
#         logger.add(
#             log_dir / "api.log",
#             format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
#             level="INFO",
#             rotation="100 MB",
#             retention="14 days",
#             compression="zip",
#             filter=lambda record: record["extra"].get("log_type") == "api"
#         )

#         # Cost telemetry log
#         logger.add(
#             log_dir / "costs.log",
#             format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
#             level="INFO",
#             rotation="50 MB",
#             retention="90 days",
#             compression="zip",
#             filter=lambda record: record["extra"].get("log_type") == "cost"
#         )

#         # OpenTelemetry traces log
#         logger.add(
#             log_dir / "traces.log",
#             format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
#             level="INFO",
#             rotation="50 MB",
#             retention="7 days",
#             compression="zip",
#             filter=lambda record: record["extra"].get("log_type") == "trace"
#         )

#         # Errors only log
#         logger.add(
#             log_dir / "errors.log",
#             format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
#             level="ERROR",
#             rotation="50 MB",
#             retention="90 days",
#             compression="zip",
#         )

#         # Debug log (only when LOG_LEVEL=DEBUG)
#         if log_level == "DEBUG":
#             logger.add(
#                 log_dir / "debug.log",
#                 format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
#                 level="DEBUG",
#                 rotation="50 MB",
#                 retention="3 days",
#                 compression="zip",
#             )

#     # ============================================================
#     # Suppress noisy third-party libraries
#     # ============================================================
#     logger.disable("httpx")
#     logger.disable("httpcore")
#     logger.disable("urllib3")
#     logger.disable("requests_cache")

#     # Bind initial context
#     logger.bind(service="food-analyzer")

#     _LOGGING_SETUP_DONE = True

#     # Log startup information
#     logger.info(f"Logging initialized | Level: {log_level} | Format: {'JSON' if in_container else 'Pretty'}")

#     if not in_container:
#         logger.info(f"Log directory: {log_dir.absolute()}/")
#         logger.info("Log files:")
#         logger.info(f"  ├── app.log     - Application messages")
#         logger.info(f"  ├── api.log     - HTTP requests")
#         logger.info(f"  ├── costs.log   - Cost telemetry")
#         logger.info(f"  ├── traces.log  - OpenTelemetry spans")
#         logger.info(f"  └── errors.log  - All errors")
#     else:
#         logger.info("Logging to stdout (JSON format for Loki)")

#     return logger


# def get_logger(name: Optional[str] = None, log_type: str = "app"):
#     """Get a logger instance with optional context and log type."""
#     if name:
#         return logger.bind(module=name, log_type=log_type)
#     return logger.bind(log_type=log_type)


# def get_log_files_info() -> dict:
#     """Get information about log files."""
#     log_dir = Path("logs")
#     if not log_dir.exists():
#         return {"error": "Log directory not found"}

#     files_info = {}
#     for log_file in ["app.log", "api.log", "costs.log", "traces.log", "errors.log", "debug.log"]:
#         file_path = log_dir / log_file
#         if file_path.exists():
#             files_info[log_file] = {
#                 "path": str(file_path.absolute()),
#                 "size_bytes": file_path.stat().st_size,
#                 "size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
#             }

#     return files_info
























































"""Logging configuration using loguru with separate files for different log types."""

import os
import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from src.config import get_settings

# Track if logging has been initialized
_LOGGING_SETUP_DONE = False
_settings = None


def _get_settings():
    """Get settings instance (lazy loading to avoid circular imports)."""
    global _settings
    if _settings is None:
        _settings = get_settings()
    return _settings


def setup_logging():
    """Configure loguru logging with separate files for different log types."""
    global _LOGGING_SETUP_DONE

    if _LOGGING_SETUP_DONE:
        return logger

    settings = _get_settings()
    log_level = settings.LOG_LEVEL.upper()

    # Check if we're in Docker/container environment
    in_container = os.path.exists("/.dockerenv") or os.getenv("LOG_FORMAT") == "json"

    # Create logs directory (only if not in container or if file logging is desired)
    log_dir = Path("logs")
    if not in_container:
        log_dir.mkdir(exist_ok=True)

    # Remove default handler
    logger.remove()

    # ============================================================
    # CONSOLE HANDLER (JSON for Docker/Loki, pretty for dev)
    # ============================================================
    if in_container:
        # JSON format for Loki - sends structured logs
        logger.add(
            sys.stdout,
            format="{message}",
            level=log_level,
            serialize=True,  # ← JSON output!
        )
    else:
        # Pretty format for development
        logger.add(
            sys.stdout,
            format=(
                "<green>{time:HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
                "<level>{message}</level>"
            ),
            level=log_level,
            colorize=True,
            filter=lambda record: record["extra"].get("log_type", "app") == "app"
        )

    # ============================================================
    # FILE HANDLERS (only in development, not in Docker)
    # ============================================================
    if not in_container:
        # Main application log
        logger.add(
            log_dir / "app.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=log_level,
            rotation="100 MB",
            retention="30 days",
            compression="zip",
            filter=lambda record: record["extra"].get("log_type", "app") == "app"
        )

        # API request log
        logger.add(
            log_dir / "api.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
            level="INFO",
            rotation="100 MB",
            retention="14 days",
            compression="zip",
            filter=lambda record: record["extra"].get("log_type") == "api"
        )

        # Cost telemetry log
        logger.add(
            log_dir / "costs.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
            level="INFO",
            rotation="50 MB",
            retention="90 days",
            compression="zip",
            filter=lambda record: record["extra"].get("log_type") == "cost"
        )

        # OpenTelemetry traces log
        logger.add(
            log_dir / "traces.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
            level="INFO",
            rotation="50 MB",
            retention="7 days",
            compression="zip",
            filter=lambda record: record["extra"].get("log_type") == "trace"
        )

        # Errors only log
        logger.add(
            log_dir / "errors.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
            level="ERROR",
            rotation="50 MB",
            retention="90 days",
            compression="zip",
        )

        # Debug log (only when LOG_LEVEL=DEBUG)
        if log_level == "DEBUG":
            logger.add(
                log_dir / "debug.log",
                format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
                level="DEBUG",
                rotation="50 MB",
                retention="3 days",
                compression="zip",
            )

    # ============================================================
    # Suppress noisy third-party libraries
    # ============================================================
    logger.disable("httpx")
    logger.disable("httpcore")
    logger.disable("urllib3")
    logger.disable("requests_cache")

    # Bind initial context
    logger.bind(service="food-analyzer")

    _LOGGING_SETUP_DONE = True

    # Log startup information
    logger.info(f"Logging initialized | Level: {log_level} | Format: {'JSON' if in_container else 'Pretty'}")

    if not in_container:
        logger.info(f"Log directory: {log_dir.absolute()}/")
        logger.info("Log files:")
        logger.info("  ├── app.log     - Application messages")
        logger.info("  ├── api.log     - HTTP requests")
        logger.info("  ├── costs.log   - Cost telemetry")
        logger.info("  ├── traces.log  - OpenTelemetry spans")
        logger.info("  └── errors.log  - All errors")
    else:
        logger.info("Logging to stdout (JSON format for Loki)")

    return logger


def get_logger(name: Optional[str] = None, log_type: str = "app"):
    """Get a logger instance with optional context and log type."""
    if name:
        return logger.bind(module=name, log_type=log_type)
    return logger.bind(log_type=log_type)


def get_log_files_info() -> dict:
    """Get information about log files."""
    log_dir = Path("logs")
    if not log_dir.exists():
        return {"error": "Log directory not found"}

    files_info = {}
    for log_file in ["app.log", "api.log", "costs.log", "traces.log", "errors.log", "debug.log"]:
        file_path = log_dir / log_file
        if file_path.exists():
            files_info[log_file] = {
                "path": str(file_path.absolute()),
                "size_bytes": file_path.stat().st_size,
                "size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
            }

    return files_info
