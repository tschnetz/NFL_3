from flask_caching import Cache
import diskcache

# Initialize diskcache explicitly for Heroku's ephemeral storage
disk_cache = diskcache.Cache("cache-directory")  # Set directory for disk storage
cache = Cache(config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': "cache-directory",  # Directory for disk-based caching
    'CACHE_DEFAULT_TIMEOUT': 86400,  # Cache timeout set to 24 hours
})