from flask_caching import Cache

# memcached
cache = Cache(config={
    'CACHE_TYPE': 'memcached',
    'CACHE_DEFAULT_TIMEOUT': 0
})

# Redis
#cache = Cache(config={
#    'CACHE_TYPE': 'redis',
#    'CACHE_DEFAULT_TIMEOUT': 0,
#    'CACHE_REDIS_HOST': '',
#    'CACHE_REDIS_PORT': 6379,
#})
