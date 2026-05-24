"""Prometheus metrics for AI Food Analyzer."""

from prometheus_client import Counter, Gauge, Histogram, Info

# ============================================================
# API Metrics
# ============================================================

# HTTP request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30)
)

# Active requests gauge
active_requests = Gauge(
    'active_requests',
    'Number of active requests being processed'
)

# ============================================================
# Analysis Metrics
# ============================================================

# Analysis counters
analysis_total = Counter(
    'analysis_total',
    'Total number of meal analyses performed',
    ['status']  # success, failure
)

meal_recognized_total = Counter(
    'meal_recognized_total',
    'Total number of meals successfully recognized'
)

ingredients_processed_total = Counter(
    'ingredients_processed_total',
    'Total number of ingredients processed',
    ['source']  # ai, cache
)

# ============================================================
# Cost Metrics
# ============================================================

# Cost tracking
cost_usd_total = Counter(
    'cost_usd_total',
    'Total API costs in USD',
    ['provider', 'model', 'operation']
)

tokens_used_total = Counter(
    'tokens_used_total',
    'Total tokens used',
    ['provider', 'model', 'type']  # type: prompt, completion
)

# ============================================================
# Cache Metrics
# ============================================================

# Cache performance
cache_hits_total = Counter(
    'cache_hits_total',
    'Total number of cache hits',
    ['cache_type']  # nutrition, vlm, http
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total number of cache misses',
    ['cache_type']
)

# ============================================================
# Database Metrics
# ============================================================

# Database connection status
database_up = Gauge(
    'database_up',
    'Database connection status (1 = up, 0 = down)'
)

database_queries_total = Counter(
    'database_queries_total',
    'Total number of database queries',
    ['operation']  # select, insert, update, delete
)

database_query_duration = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['operation'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1)
)

# ============================================================
# AI Service Metrics
# ============================================================

# AI provider metrics
ai_requests_total = Counter(
    'ai_requests_total',
    'Total number of AI provider requests',
    ['provider', 'model', 'status']  # status: success, error
)

ai_request_duration = Histogram(
    'ai_request_duration_seconds',
    'AI provider request duration in seconds',
    ['provider', 'model'],
    buckets=(0.1, 0.5, 1, 2, 5, 10, 20, 30, 60)
)

# Failover metrics
failover_attempts_total = Counter(
    'failover_attempts_total',
    'Total number of failover attempts',
    ['provider', 'fallback_provider']
)

# ============================================================
# Nutrition Provider Metrics
# ============================================================

nutrition_requests_total = Counter(
    'nutrition_requests_total',
    'Total number of nutrition API requests',
    ['provider', 'status']  # provider: usda, openfoodfacts, mock
)

nutrition_lookup_duration = Histogram(
    'nutrition_lookup_duration_seconds',
    'Nutrition lookup duration in seconds',
    ['provider'],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5)
)

# ============================================================
# System Metrics
# ============================================================

# Service info
service_info = Info(
    'service_info',
    'Service information'
)

# Queue sizes
image_queue_size = Gauge(
    'image_queue_size',
    'Number of images waiting to be processed'
)

# ============================================================
# Helper function to update service info
# ============================================================

def set_service_info(version: str, environment: str):
    """Set service information metrics."""
    service_info.info({
        'version': version,
        'environment': environment,
        'service': 'ai-food-analyzer'
    })
