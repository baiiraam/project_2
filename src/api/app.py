from fastapi import FastAPI, File, UploadFile, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import time
import logging
import tempfile
import os

# All imports at top (required by ruff)
from src.services.http_cache import setup_http_cache, get_cache_stats, clear_cache
from src.config import Settings
from src.core.analyzer import FoodAnalyzer
from src.logging_config import setup_logging
from src.api.models import IngredientResponse, AnalysisResult, TotalsResponse

# Initialize cache (after imports)
settings = Settings()
setup_http_cache(
    cache_name="nutrition_api_cache",
    expire_after=settings.NUTRITION_CACHE_TTL_SECONDS,
    allowed_domains=["api.nal.usda.gov", "world.openfoodfacts.net"],
    cache_dir=".cache",
)

setup_logging()

# Rest of your code remains the same...

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Food Analyzer API",
    description="Analyze meal photos for nutrition information",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    t1 = time.perf_counter()
    resp = await call_next(request)
    t2 = time.perf_counter()
    time_spent = t2 - t1
    logger.info(
        f"Method: {request.method} | "
        f"Path: {request.url.path} | "
        f"Status: {resp.status_code} | "
        f"Duration: {time_spent:.4f}s | "
    )
    return resp


analyzer = FoodAnalyzer()


@app.get("/")
def read_root():
    return {"message": "AI Food Analyzer API", "version": "1.0.0"}


@app.get("/health")
def read_health():
    return {"status": "healthy", "cache_enabled": True}


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


@app.post("/analyze", response_model=AnalysisResult)
async def analyze(file: UploadFile = File(...)):
    logger.info(
        f"Request received - File: {file.filename}, Size: {file.size}, Type: {file.content_type}"
    )

    if file.content_type not in {"image/jpeg", "image/png"}:
        logger.error(
            f"Unsupported media type: {file.content_type}. Allowed: image/jpeg, image/png"
        )
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File type should be one of: .jpg, .jpeg, .png",
        )

    if file.size and file.size > settings.MAX_IMAGE_SIZE_MB * 1024 * 1024:
        logger.error(
            f"File too large: {file.size} bytes. Max allowed: {settings.MAX_IMAGE_SIZE_MB * 1024 * 1024} bytes"
        )
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
        logger.debug(f"File extension: {suff}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=suff) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_name = tmp.name
            logger.debug(f"Temp file created: {tmp_name}")

        logger.info(f"Starting analysis of {tmp_name}")
        res = await analyzer.analyze_async(tmp.name)
        logger.info(f"Analysis completed. Ingredients: {len(res['ingredients'])}")

        if not res["ingredients"]:
            logger.warning("No ingredients recognized in image")

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

    except Exception as e:
        logger.exception(f"Error during analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if tmp_name:
            try:
                os.unlink(tmp_name)
                logger.debug(f"Temp file deleted: {tmp_name}")
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")
