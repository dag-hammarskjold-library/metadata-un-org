from flask_caching import Cache
from metadata.config import GLOBAL_CONFIG

CACHE_SERVERS = GLOBAL_CONFIG.CACHE_SERVERS

# memcached
cache = Cache(config={
    'CACHE_TYPE': 'memcached',
    'CACHE_DEFAULT_TIMEOUT': 0,
    'CACHE_MEMCACHED_SERVERS': CACHE_SERVERS
})

# Redis
#cache = Cache(config={
#    'CACHE_TYPE': 'redis',
#    'CACHE_DEFAULT_TIMEOUT': 0,
#    'CACHE_REDIS_HOST': '',
#    'CACHE_REDIS_PORT': 6379,
#})
