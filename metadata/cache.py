from flask_caching import Cache

cache = Cache(config={
    'CACHE_TYPE': 'memcached',
    'CACHE_DEFAULT_TIMEOUT': 0
})
