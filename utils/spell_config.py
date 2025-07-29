
# Spell Checker Configuration - Optimized for Speed
SPELL_CHECK_CONFIG = {
    # Minimum query length to trigger spell check
    'min_query_length': 3,
    
    # Fuzzy matching cutoff (0.0 to 1.0, higher = stricter but faster)
    'fuzzy_cutoff': 0.7,  # Increased for better precision and speed
    
    # Maximum number of files to process for suggestions (reduced for speed)
    'max_files_sample': 50,
    
    # Maximum number of suggestions to consider
    'max_suggestions': 1,  # Reduced to 1 for faster processing
    
    # Enable caching
    'enable_caching': True,
    
    # Cache size limits
    'query_cache_size': 1000,
    'misspell_cache_size': 500,
    
    # Words to always preserve in queries
    'preserve_words': [
        'the', 'a', 'an', 'and', 'or', 'in', 'on', 'at', 'to', 'for',
        'movie', 'film', 'series', 'season', 'episode', 'part', 'vol'
    ],
    
    # Common noise words to remove (optimized list)
    'noise_words': [
        'please', 'send', 'give', 'share', 'upload', 'download', 
        'link', 'file', 'want', 'need', 'looking', 'search'
    ],
    
    # Performance settings
    'async_timeout': 2.0,  # Maximum time to spend on spell check
    'enable_quick_check': True,  # Enable quick exact match checks
}
