# """FastAPI application for AI Food Analyzer."""

# import os
# import tempfile
# import time
# from contextlib import asynccontextmanager
# from pathlib import Path

# from fastapi import FastAPI, File, HTTPException, Request, Response, UploadFile, status
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.middleware.trustedhost import TrustedHostMiddleware
# from loguru import logger
# from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

# from ai.providers.base import ProviderError
# from src.api.models import AnalysisResult, IngredientResponse, TotalsResponse
# from src.config import get_settings
# from src.core.analyzer import FoodAnalyzer
# from src.logging_config import get_logger, setup_logging
# from src.services.http_cache import clear_cache, get_cache_stats, setup_http_cache
# from src.storage.database import Database
# from src.telemetry.metrics import (
#     active_requests,
#     analysis_total,
#     database_up,
#     http_request_duration,
#     http_requests_total,
#     meal_recognized_total,
#     set_service_info,
# )
# from src.telemetry.tracing import instrument_fastapi, instrument_requests, setup_tracing
# from src.web.routes import mount_static
# from src.web.routes import router as web_router

# # ============================================================
# # STEP 1: Setup logging FIRST
# # ============================================================
# setup_logging()

# # ============================================================
# # STEP 2: Create specific loggers
# # ============================================================
# api_logger = get_logger("api", log_type="api")

# # ============================================================
# # STEP 3: Initialize settings and cache
# # ============================================================
# settings = get_settings()
# setup_http_cache(
#     cache_name="nutrition_api_cache",
#     expire_after=settings.NUTRITION_CACHE_TTL_SECONDS,
#     allowed_domains=["api.nal.usda.gov", "world.openfoodfacts.net"],
#     cache_dir=".cache",
# )

# # Set service info on startup
# set_service_info(version="1.0.0", environment="development")

# # ============================================================
# # STEP 4: Lifespan manager
# # ============================================================
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Startup
#     await Database.init_pool()
#     logger.info("Database initialized")

#     yield

#     # Shutdown
#     await Database.close()
#     logger.info("Database closed")

# # ============================================================
# # STEP 5: Create FastAPI app
# # ============================================================
# app = FastAPI(
#     title="AI Food Analyzer API",
#     description="""
#     Analyze meal photos for nutrition information.

#     ## Features
#     * Identify ingredients from photos
#     * Calculate total calories and macros
#     * Cache results for performance
#     """,
#     version="1.0.0",
#     contact={
#         "name": "Your Name",
#         "email": "your@email.com",
#     },
#     lifespan=lifespan
# )

# # ============================================================
# # STEP 6: Setup telemetry
# # ============================================================
# setup_tracing()
# instrument_fastapi(app)
# instrument_requests()

# # ============================================================
# # STEP 7: Middleware (order matters!)
# # ============================================================

# # 7.1 Trusted host middleware
# app.add_middleware(
#     TrustedHostMiddleware,
#     allowed_hosts=["*"],  # In production, specify your domain
# )

# # 7.2 CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ============================================================
# # STEP 8: Custom middleware
# # ============================================================

# @app.middleware("http")
# async def set_client_ip(request: Request, call_next):
#     """Extract real client IP from proxy headers (for use behind Nginx)."""
#     forwarded = request.headers.get("X-Forwarded-For")
#     if forwarded:
#         client_ip = forwarded.split(',')[0].strip()
#         request.state.client_ip = client_ip
#     response = await call_next(request)
#     return response

# @app.middleware("http")
# async def log_requests(request: Request, call_next):
#     """Log all HTTP requests with timing."""
#     t1 = time.perf_counter()
#     response = await call_next(request)
#     t2 = time.perf_counter()

#     client_ip = getattr(request.state, 'client_ip', request.client.host if request.client else "unknown")
#     api_logger.info(
#         f"{request.method} {request.url.path} | {response.status_code} | {t2-t1:.4f}s | Client: {client_ip}"
#     )
#     return response




# import os

# INSTANCE_ID = os.getenv("INSTANCE_ID", "1")

# @app.middleware("http")
# async def log_requests(request: Request, call_next):
#     """Log all HTTP requests with timing and instance ID."""
#     t1 = time.perf_counter()
#     response = await call_next(request)
#     t2 = time.perf_counter()

#     client_ip = getattr(request.state, 'client_ip', request.client.host if request.client else "unknown")

#     api_logger.info(
#         f"[Instance {INSTANCE_ID}] {request.method} {request.url.path} | {response.status_code} | {t2-t1:.4f}s | Client: {client_ip}"
#     )

#     return response







# @app.middleware("http")
# async def metrics_middleware(request: Request, call_next):
#     """Track HTTP metrics."""
#     active_requests.inc()
#     start_time = time.time()

#     response = await call_next(request)

#     duration = time.time() - start_time
#     active_requests.dec()

#     endpoint = request.url.path
#     method = request.method
#     status_code = response.status_code

#     http_requests_total.labels(
#         method=method,
#         endpoint=endpoint,
#         status_code=status_code
#     ).inc()

#     http_request_duration.labels(
#         method=method,
#         endpoint=endpoint
#     ).observe(duration)

#     return response

# # ============================================================
# # STEP 9: Static files and routes
# # ============================================================
# mount_static(app)
# app.include_router(web_router)

# # ============================================================
# # STEP 10: Initialize analyzer
# # ============================================================
# analyzer = FoodAnalyzer()

# # ============================================================
# # STEP 11: Endpoints
# # ============================================================

# @app.get("/health")
# async def read_health():
#     """Health check endpoint with database status."""
#     db_ok = await Database.health_check()
#     database_up.set(1 if db_ok else 0)

#     return {
#         "status": "ok" if db_ok else "degraded",
#         "database": "connected" if db_ok else "disconnected",
#         "timestamp": time.time(),
#         "cache_enabled": settings.HTTP_CACHE_ENABLED,
#     }

# @app.get("/metrics")
# async def metrics_endpoint():
#     """Prometheus metrics endpoint."""
#     return Response(
#         content=generate_latest(),
#         media_type=CONTENT_TYPE_LATEST
#     )

# @app.get("/cache/stats")
# async def cache_stats():
#     """Get HTTP cache statistics."""
#     stats = get_cache_stats()
#     if stats:
#         return stats
#     return {
#         "status": "disabled",
#         "message": "Cache not initialized or requests-cache not installed",
#     }

# @app.post("/cache/clear")
# async def clear_http_cache():
#     """Clear the HTTP cache."""
#     success = clear_cache()
#     if success:
#         return {"message": "Cache cleared successfully"}
#     else:
#         raise HTTPException(status_code=500, detail="Failed to clear cache")

# @app.post(
#     "/analyze",
#     response_model=AnalysisResult,
#     summary="Analyze a meal photo",
#     description="Upload a JPEG or PNG image of a meal to get nutrition analysis",
#     response_description="Nutritional breakdown of the meal",
# )
# async def analyze(file: UploadFile = File(...)):
#     logger.info(
#         f"Request received - File: {file.filename}, Size: {file.size}, Type: {file.content_type}"
#     )

#     if file.content_type not in {"image/jpeg", "image/png"}:
#         logger.error(
#             f"Unsupported media type: {file.content_type}. Allowed: image/jpeg, image/png"
#         )
#         analysis_total.labels(status="failure").inc()
#         raise HTTPException(
#             status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
#             detail="File type should be one of: .jpg, .jpeg, .png",
#         )

#     if file.size and file.size > settings.MAX_IMAGE_SIZE_MB * 1024 * 1024:
#         logger.error(
#             f"File too large: {file.size} bytes. Max allowed: {settings.MAX_IMAGE_SIZE_MB * 1024 * 1024} bytes"
#         )
#         analysis_total.labels(status="failure").inc()
#         raise HTTPException(
#             status_code=status.HTTP_413_CONTENT_TOO_LARGE,
#             detail=f"Filesize is too large. Maximum allowed filesize is {settings.MAX_IMAGE_SIZE_MB} MB.",
#         )

#     tmp_name = None
#     try:
#         if file.filename:
#             suff = Path(file.filename).suffix
#         else:
#             suff = ".png"
#         logger.debug(f"File extension: {suff}")

#         with tempfile.NamedTemporaryFile(delete=False, suffix=suff) as tmp:
#             content = await file.read()
#             tmp.write(content)
#             tmp_name = tmp.name
#             logger.debug(f"Temp file created: {tmp_name}")

#         logger.info(f"Starting analysis of {tmp_name}")
#         res = await analyzer.analyze_async(tmp.name)
#         logger.info(f"Analysis completed. Ingredients: {len(res['ingredients'])}")

#         if not res["ingredients"]:
#             logger.warning("No ingredients recognized in image")
#             analysis_total.labels(status="no_meal").inc()
#         else:
#             analysis_total.labels(status="success").inc()
#             meal_recognized_total.inc()

#         ingredients_response = []
#         for ingredient in res["ingredients"]:
#             facts = res["nutrition_per_ingredient"][ingredient.name]
#             grams = ingredient.estimated_grams
#             ingredients_response.append(
#                 IngredientResponse(
#                     name=ingredient.name,
#                     grams=grams,
#                     kcal=(grams / 100) * facts.kcal_per_100g,
#                     protein_g=(grams / 100) * facts.protein_g_per_100g,
#                     carbs_g=(grams / 100) * facts.carbs_g_per_100g,
#                     fat_g=(grams / 100) * facts.fat_g_per_100g,
#                 )
#             )

#         response = AnalysisResult(
#             ingredients=ingredients_response,
#             totals=TotalsResponse(
#                 kcal=res["totals"].kcal,
#                 protein_g=res["totals"].protein_g,
#                 carbs_g=res["totals"].carbs_g,
#                 fat_g=res["totals"].fat_g,
#             ),
#             meal_recognized=len(res["ingredients"]) > 0,
#         )

#         return response

#     except ProviderError as e:
#         analysis_total.labels(status="failure").inc()
#         error_str = str(e)
#         if "503" in error_str or "UNAVAILABLE" in error_str:
#             logger.warning(f"Service unavailable (503): {e}")
#             raise HTTPException(
#                 status_code=503,
#                 detail="Service temporarily unavailable. Please try again later.",
#             )
#         else:
#             logger.error(f"Provider error (non-503): {e}")
#             raise HTTPException(
#                 status_code=500,
#                 detail="External service not working. Please try again later.",
#             )

#     except Exception as e:
#         analysis_total.labels(status="failure").inc()
#         logger.exception(f"Unexpected error during analysis: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

#     finally:
#         if tmp_name:
#             try:
#                 os.unlink(tmp_name)
#                 logger.debug(f"Temp file deleted: {tmp_name}")
#             except Exception as e:
#                 logger.warning(f"Failed to delete temp file: {e}")

# # ============================================================
# # STEP 12: Additional endpoints
# # ============================================================

# @app.get("/analysis/{analysis_id}", response_model=AnalysisResult)
# async def get_analysis(analysis_id: int):
#     """Retrieve a previously analyzed meal by ID."""
#     logger.info(f"Retrieving analysis with ID: {analysis_id}")

#     try:
#         result = await Database.get_by_id(analysis_id)

#         if not result:
#             logger.warning(f"Analysis with ID {analysis_id} not found")
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"Analysis with ID {analysis_id} not found"
#             )

#         ingredients_response = []
#         for ingredient in result.get('ingredients', []):
#             ingredients_response.append(
#                 IngredientResponse(
#                     name=ingredient.get('name'),
#                     grams=ingredient.get('estimated_grams'),
#                     kcal=ingredient.get('kcal', 0),
#                     protein_g=ingredient.get('protein_g', 0),
#                     carbs_g=ingredient.get('carbs_g', 0),
#                     fat_g=ingredient.get('fat_g', 0),
#                 )
#             )

#         response = AnalysisResult(
#             ingredients=ingredients_response,
#             totals=TotalsResponse(
#                 kcal=result.get('total_kcal', 0),
#                 protein_g=result.get('total_protein_g', 0),
#                 carbs_g=result.get('total_carbs_g', 0),
#                 fat_g=result.get('total_fat_g', 0),
#             ),
#             meal_recognized=len(ingredients_response) > 0,
#         )

#         return response

#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.exception(f"Error retrieving analysis {analysis_id}: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Error retrieving analysis: {str(e)}"
#         )

# @app.get("/analyses")
# async def list_analyses(limit: int = 10):
#     """List recent analyses."""
#     logger.info(f"Listing analyses with limit: {limit}")

#     try:
#         results = await Database.get_last_n(limit)

#         return {
#             "total": len(results),
#             "analyses": [
#                 {
#                     "id": r.get('id'),
#                     "image_path": r.get('image_path'),
#                     "total_kcal": r.get('total_kcal', 0),
#                     "created_at": r.get('created_at'),
#                     "meal_recognized": r.get('meal_recognized', False)
#                 }
#                 for r in results
#             ]
#         }
#     except Exception as e:
#         logger.exception(f"Error listing analyses: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Error listing analyses: {str(e)}"
#         )













































"""FastAPI application for AI Food Analyzer."""

import os
import tempfile
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from loguru import logger
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from ai.providers.base import ProviderError
from src.api.models import AnalysisResult, IngredientResponse, TotalsResponse
from src.config import get_settings
from src.core.analyzer import FoodAnalyzer
from src.logging_config import get_logger, setup_logging
from src.services.http_cache import clear_cache, get_cache_stats, setup_http_cache
from src.storage.database import Database
from src.telemetry.metrics import (
    active_requests,
    analysis_total,
    database_up,
    http_request_duration,
    http_requests_total,
    meal_recognized_total,
    set_service_info,
)
from src.telemetry.tracing import instrument_fastapi, instrument_requests, setup_tracing
from src.web.routes import mount_static
from src.web.routes import router as web_router

# ============================================================
# STEP 1: Setup logging FIRST
# ============================================================
setup_logging()

# ============================================================
# STEP 2: Create specific loggers
# ============================================================
api_logger = get_logger("api", log_type="api")

# ============================================================
# STEP 3: Initialize settings and cache
# ============================================================
settings = get_settings()
setup_http_cache(
    cache_name="nutrition_api_cache",
    expire_after=settings.NUTRITION_CACHE_TTL_SECONDS,
    allowed_domains=["api.nal.usda.gov", "world.openfoodfacts.net"],
    cache_dir=".cache",
)

# Set service info on startup
set_service_info(version="1.0.0", environment="development")

# Get instance ID for load balancing
INSTANCE_ID = os.getenv("INSTANCE_ID", "1")

# ============================================================
# STEP 4: Lifespan manager
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await Database.init_pool()
    logger.info(f"Database initialized (Instance {INSTANCE_ID})")

    yield

    # Shutdown
    await Database.close()
    logger.info(f"Database closed (Instance {INSTANCE_ID})")

# ============================================================
# STEP 5: Create FastAPI app
# ============================================================
app = FastAPI(
    title="AI Food Analyzer API",
    description="""
    Analyze meal photos for nutrition information.

    ## Features
    * Identify ingredients from photos
    * Calculate total calories and macros
    * Cache results for performance
    """,
    version="1.0.0",
    contact={
        "name": "Your Name",
        "email": "your@email.com",
    },
    lifespan=lifespan
)

# ============================================================
# STEP 6: Setup telemetry
# ============================================================
setup_tracing()
instrument_fastapi(app)
instrument_requests()

# ============================================================
# STEP 7: Middleware (order matters!)
# ============================================================

# 7.1 Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],  # In production, specify your domain
)

# 7.2 CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# STEP 8: Custom middleware
# ============================================================

@app.middleware("http")
async def set_client_ip(request: Request, call_next):
    """Extract real client IP from proxy headers (for use behind Nginx)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(',')[0].strip()
        request.state.client_ip = client_ip
    response = await call_next(request)
    return response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with timing and instance ID."""
    t1 = time.perf_counter()
    response = await call_next(request)
    t2 = time.perf_counter()

    client_ip = getattr(request.state, 'client_ip', request.client.host if request.client else "unknown")

    api_logger.info(
        f"[Instance {INSTANCE_ID}] {request.method} {request.url.path} | {response.status_code} | {t2-t1:.4f}s | Client: {client_ip}"
    )

    return response

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Track HTTP metrics."""
    active_requests.inc()
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time
    active_requests.dec()

    endpoint = request.url.path
    method = request.method
    status_code = response.status_code

    http_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status_code=status_code
    ).inc()

    http_request_duration.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)

    return response

# ============================================================
# STEP 9: Static files and routes
# ============================================================
mount_static(app)
app.include_router(web_router)

# ============================================================
# STEP 10: Initialize analyzer
# ============================================================
analyzer = FoodAnalyzer()

# ============================================================
# STEP 11: Endpoints
# ============================================================

@app.get("/health")
async def read_health():
    """Health check endpoint with database status."""
    db_ok = await Database.health_check()
    database_up.set(1 if db_ok else 0)

    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "timestamp": time.time(),
        "cache_enabled": settings.HTTP_CACHE_ENABLED,
        "instance_id": INSTANCE_ID,  # Add instance ID to health check
    }

@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@app.get("/cache/stats")
async def cache_stats():
    """Get HTTP cache statistics."""
    stats = get_cache_stats()
    if stats:
        return stats
    return {
        "status": "disabled",
        "message": "Cache not initialized or requests-cache not installed",
    }

@app.post("/cache/clear")
async def clear_http_cache():
    """Clear the HTTP cache."""
    success = clear_cache()
    if success:
        return {"message": "Cache cleared successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to clear cache")

@app.post(
    "/analyze",
    response_model=AnalysisResult,
    summary="Analyze a meal photo",
    description="Upload a JPEG or PNG image of a meal to get nutrition analysis",
    response_description="Nutritional breakdown of the meal",
)
async def analyze(file: UploadFile = File(...)):
    logger.info(
        f"[Instance {INSTANCE_ID}] Request received - File: {file.filename}, Size: {file.size}, Type: {file.content_type}"
    )

    if file.content_type not in {"image/jpeg", "image/png"}:
        logger.error(
            f"[Instance {INSTANCE_ID}] Unsupported media type: {file.content_type}"
        )
        analysis_total.labels(status="failure").inc()
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File type should be one of: .jpg, .jpeg, .png",
        )

    if file.size and file.size > settings.MAX_IMAGE_SIZE_MB * 1024 * 1024:
        logger.error(
            f"[Instance {INSTANCE_ID}] File too large: {file.size} bytes"
        )
        analysis_total.labels(status="failure").inc()
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Filesize is too large. Maximum allowed filesize is {settings.MAX_IMAGE_SIZE_MB} MB.",
        )

    tmp_name = None
    try:
        if file.filename:
            suff = Path(file.filename).suffix
        else:
            suff = ".png"
        logger.debug(f"[Instance {INSTANCE_ID}] File extension: {suff}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=suff) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_name = tmp.name
            logger.debug(f"[Instance {INSTANCE_ID}] Temp file created: {tmp_name}")

        logger.info(f"[Instance {INSTANCE_ID}] Starting analysis of {tmp_name}")
        res = await analyzer.analyze_async(tmp.name)
        logger.info(f"[Instance {INSTANCE_ID}] Analysis completed. Ingredients: {len(res['ingredients'])}")

        if not res["ingredients"]:
            logger.warning(f"[Instance {INSTANCE_ID}] No ingredients recognized in image")
            analysis_total.labels(status="no_meal").inc()
        else:
            analysis_total.labels(status="success").inc()
            meal_recognized_total.inc()

        ingredients_response = []
        for ingredient in res["ingredients"]:
            facts = res["nutrition_per_ingredient"][ingredient.name]
            grams = ingredient.estimated_grams
            ingredients_response.append(
                IngredientResponse(
                    name=ingredient.name,
                    grams=grams,
                    kcal=(grams / 100) * facts.kcal_per_100g,
                    protein_g=(grams / 100) * facts.protein_g_per_100g,
                    carbs_g=(grams / 100) * facts.carbs_g_per_100g,
                    fat_g=(grams / 100) * facts.fat_g_per_100g,
                )
            )

        response = AnalysisResult(
            ingredients=ingredients_response,
            totals=TotalsResponse(
                kcal=res["totals"].kcal,
                protein_g=res["totals"].protein_g,
                carbs_g=res["totals"].carbs_g,
                fat_g=res["totals"].fat_g,
            ),
            meal_recognized=len(res["ingredients"]) > 0,
        )

        return response

    except ProviderError as e:
        analysis_total.labels(status="failure").inc()
        error_str = str(e)
        if "503" in error_str or "UNAVAILABLE" in error_str:
            logger.warning(f"[Instance {INSTANCE_ID}] Service unavailable (503): {e}")
            raise HTTPException(
                status_code=503,
                detail="Service temporarily unavailable. Please try again later.",
            )
        else:
            logger.error(f"[Instance {INSTANCE_ID}] Provider error (non-503): {e}")
            raise HTTPException(
                status_code=500,
                detail="External service not working. Please try again later.",
            )

    except Exception as e:
        analysis_total.labels(status="failure").inc()
        logger.exception(f"[Instance {INSTANCE_ID}] Unexpected error during analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if tmp_name:
            try:
                os.unlink(tmp_name)
                logger.debug(f"[Instance {INSTANCE_ID}] Temp file deleted: {tmp_name}")
            except Exception as e:
                logger.warning(f"[Instance {INSTANCE_ID}] Failed to delete temp file: {e}")

# ============================================================
# STEP 12: Additional endpoints
# ============================================================

@app.get("/analysis/{analysis_id}", response_model=AnalysisResult)
async def get_analysis(analysis_id: int):
    """Retrieve a previously analyzed meal by ID."""
    logger.info(f"[Instance {INSTANCE_ID}] Retrieving analysis with ID: {analysis_id}")

    try:
        result = await Database.get_by_id(analysis_id)

        if not result:
            logger.warning(f"[Instance {INSTANCE_ID}] Analysis with ID {analysis_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis with ID {analysis_id} not found"
            )

        ingredients_response = []
        for ingredient in result.get('ingredients', []):
            ingredients_response.append(
                IngredientResponse(
                    name=ingredient.get('name'),
                    grams=ingredient.get('estimated_grams'),
                    kcal=ingredient.get('kcal', 0),
                    protein_g=ingredient.get('protein_g', 0),
                    carbs_g=ingredient.get('carbs_g', 0),
                    fat_g=ingredient.get('fat_g', 0),
                )
            )

        response = AnalysisResult(
            ingredients=ingredients_response,
            totals=TotalsResponse(
                kcal=result.get('total_kcal', 0),
                protein_g=result.get('total_protein_g', 0),
                carbs_g=result.get('total_carbs_g', 0),
                fat_g=result.get('total_fat_g', 0),
            ),
            meal_recognized=len(ingredients_response) > 0,
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[Instance {INSTANCE_ID}] Error retrieving analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving analysis: {str(e)}"
        )

@app.get("/analyses")
async def list_analyses(limit: int = 10):
    """List recent analyses."""
    logger.info(f"[Instance {INSTANCE_ID}] Listing analyses with limit: {limit}")

    try:
        results = await Database.get_last_n(limit)

        return {
            "total": len(results),
            "analyses": [
                {
                    "id": r.get('id'),
                    "image_path": r.get('image_path'),
                    "total_kcal": r.get('total_kcal', 0),
                    "created_at": r.get('created_at'),
                    "meal_recognized": r.get('meal_recognized', False)
                }
                for r in results
            ]
        }
    except Exception as e:
        logger.exception(f"[Instance {INSTANCE_ID}] Error listing analyses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing analyses: {str(e)}"
        )
