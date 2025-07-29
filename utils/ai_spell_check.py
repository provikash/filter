
import re
import difflib
from typing import Optional, List, Set
import logging
import asyncio
from functools import lru_cache

logger = logging.getLogger(__name__)

class MovieSpellChecker:
    def __init__(self):
        # Cache for processed titles to avoid repeated processing
        self._title_cache = {}
        self._suggestion_cache = {}
        
        # Pre-compiled regex patterns for better performance
        self.noise_pattern = re.compile(r'\b(please|send|give|share|upload|download|link|file|want|need|looking|search)\b', re.IGNORECASE)
        self.whitespace_pattern = re.compile(r'\s+')
        self.repeated_chars_pattern = re.compile(r'\b\w*([a-z])\1{2,}\w*\b', re.IGNORECASE)
        self.mixed_pattern = re.compile(r'\b\w*[0-9]+[a-z]+\w*\b', re.IGNORECASE)
        
        # Common movie title patterns and terms to preserve
        self.preserve_patterns = [
            re.compile(r'\b(the|a|an)\b', re.IGNORECASE),
            re.compile(r'\b\d{4}\b'),
            re.compile(r'\b(part|vol|volume)\s*\d+\b', re.IGNORECASE),
            re.compile(r'\b(season|s)\s*\d+\b', re.IGNORECASE),
            re.compile(r'\b(episode|ep|e)\s*\d+\b', re.IGNORECASE),
            re.compile(r'\b(hd|4k|1080p|720p|480p)\b', re.IGNORECASE),
        ]
        
        # Terms that are commonly misspelled but should be preserved
        self.movie_terms = {
            'moive': 'movie', 'flim': 'film', 'serie': 'series',
            'episod': 'episode', 'seasn': 'season', 'seson': 'season',
            'movei': 'movie', 'filim': 'film', 'seriees': 'series'
        }

    @lru_cache(maxsize=1000)
    def clean_search_query(self, query: str) -> str:
        """Clean search query while preserving movie-specific terms - cached for performance"""
        if not query or len(query.strip()) < 2:
            return query
            
        # Remove excessive whitespace
        query = self.whitespace_pattern.sub(' ', query.strip())
        
        # Remove common request words but preserve movie terms
        query = self.noise_pattern.sub('', query)
        
        # Fix common movie term misspellings
        words = query.split()
        corrected_words = []
        for word in words:
            corrected_word = self.movie_terms.get(word.lower(), word)
            corrected_words.append(corrected_word)
        
        return ' '.join(corrected_words).strip()

    def extract_movie_titles_fast(self, files: List) -> Set[str]:
        """Fast extraction of clean movie titles from file list"""
        titles = set()
        for file in files[:50]:  # Limit to first 50 for speed
            # Quick title extraction - remove common prefixes/suffixes
            title = file.file_name
            
            # Remove file extension
            title = re.sub(r'\.[a-z0-9]{2,4}$', '', title, flags=re.IGNORECASE)
            
            # Remove common movie file patterns
            title = re.sub(r'\b(1080p|720p|480p|hdtv|webrip|bluray|dvdrip|x264|x265)\b.*', '', title, flags=re.IGNORECASE)
            title = re.sub(r'\[.*?\]|\(.*?\)', '', title)  # Remove brackets content
            title = re.sub(r'\b\d{4}\b.*', '', title)  # Remove year and everything after
            
            # Clean up
            title = self.whitespace_pattern.sub(' ', title.strip())
            
            if len(title.split()) >= 2:  # Only keep titles with at least 2 words
                titles.add(title)
                
        return titles

    def suggest_correction_fast(self, original_query: str, available_titles: Set[str]) -> Optional[str]:
        """Fast suggestion using optimized fuzzy matching"""
        if not available_titles:
            return None
            
        # Use cache if available
        cache_key = f"{original_query}:{len(available_titles)}"
        if cache_key in self._suggestion_cache:
            return self._suggestion_cache[cache_key]
            
        cleaned_query = self.clean_search_query(original_query)
        
        # If query is too short, don't suggest corrections
        if len(cleaned_query.split()) < 2:
            return None
            
        # Convert to lowercase for comparison
        query_lower = cleaned_query.lower()
        titles_lower = [title.lower() for title in available_titles]
        
        # Quick exact match check first
        if query_lower in titles_lower:
            result = None  # Don't suggest if exact match exists
        else:
            # Use difflib with optimized parameters
            best_matches = difflib.get_close_matches(
                query_lower, 
                titles_lower,
                n=1, 
                cutoff=0.7  # Slightly higher cutoff for better precision
            )
            
            result = None
            if best_matches:
                # Find original case version
                for title in available_titles:
                    if title.lower() == best_matches[0]:
                        result = title
                        break
        
        # Cache the result
        self._suggestion_cache[cache_key] = result
        return result

    @lru_cache(maxsize=500)
    def is_likely_misspelled(self, query: str) -> bool:
        """Check if query is likely misspelled based on patterns - cached"""
        # Don't check very short queries
        if len(query.split()) < 2:
            return False
            
        # Check for obvious misspellings using pre-compiled patterns
        if self.repeated_chars_pattern.search(query) or self.mixed_pattern.search(query):
            return True
                
        return False

# Initialize the spell checker
spell_checker = MovieSpellChecker()

async def ai_spell_check(chat_id: int, wrong_name: str) -> Optional[str]:
    """Optimized AI spell check function with faster response times"""
    try:
        # Quick validation
        if not wrong_name or len(wrong_name.strip()) < 3:
            return None
            
        # Import here to avoid circular imports
        from database.ia_filterdb import get_search_results
        
        # Clean the input query
        cleaned_query = spell_checker.clean_search_query(wrong_name)
        
        # If cleaning made the query too short, return None
        if len(cleaned_query.split()) < 2:
            return None
            
        # Quick misspelling check
        if not spell_checker.is_likely_misspelled(cleaned_query):
            return None
            
        # Get sample movie titles with reduced count for speed
        sample_files, _, _ = await get_search_results(chat_id, "", max_results=50)
        
        if not sample_files:
            return None
            
        # Fast title extraction
        available_titles = spell_checker.extract_movie_titles_fast(sample_files)
        
        if not available_titles:
            return None
        
        # Get suggestion with optimized matching
        suggestion = spell_checker.suggest_correction_fast(cleaned_query, available_titles)
        
        if suggestion and suggestion.lower() != cleaned_query.lower():
            return suggestion
            
        return None
        
    except Exception as e:
        logger.error(f"AI spell check error: {e}")
        return None

# Utility function to clear caches if needed
def clear_spell_check_cache():
    """Clear spell checker caches to free memory"""
    spell_checker.clean_search_query.cache_clear()
    spell_checker.is_likely_misspelled.cache_clear()
    spell_checker._suggestion_cache.clear()
    spell_checker._title_cache.clear()
          
