"""
This module provides translation functionality using Google Translate API.
It handles text translation from English to Chinese with error handling,
retry mechanisms, and caching for improved reliability and performance.
"""

import logging
import time
from typing import Dict, Optional, Tuple

from googletrans import Translator
from googletrans.models import Translated

from config import config


class TranslationError(Exception):
    """Custom exception for translation-related errors."""

    def __init__(self, message: str, original_text: str = ""):
        super().__init__(message)
        self.original_text = original_text


class TranslationProcessor:
    """
    Handles text translation using Google Translate API.
    Provides caching, error handling, and retry mechanisms for reliable translation.
    """

    def __init__(self):
        """Initialize the translation processor with Google Translate client."""
        self.translator = Translator()
        self.cache: Dict[str, Tuple[str, float]] = {}
        self.max_cache_size = getattr(config, "TRANSLATION_CACHE_SIZE", 1000)
        self.cache_ttl = getattr(config, "TRANSLATION_CACHE_TTL", 3600)  # 1 hour
        self.max_retries = getattr(config, "TRANSLATION_MAX_RETRIES", 3)
        self.retry_delay = getattr(config, "TRANSLATION_RETRY_DELAY", 1.0)

    def _is_cache_valid(self, timestamp: float) -> bool:
        """
        Check if a cached translation is still valid based on TTL.

        Args:
            timestamp (float): The timestamp when the translation was cached.

        Returns:
            bool: True if the cache entry is still valid, False otherwise.
        """
        return time.time() - timestamp < self.cache_ttl

    def _clean_cache(self):
        """Remove expired entries from the translation cache."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp >= self.cache_ttl
        ]
        for key in expired_keys:
            del self.cache[key]

        # If cache is still too large, remove oldest entries
        if len(self.cache) > self.max_cache_size:
            sorted_items = sorted(self.cache.items(), key=lambda x: x[1][1])
            items_to_remove = len(self.cache) - self.max_cache_size
            for key, _ in sorted_items[:items_to_remove]:
                del self.cache[key]

    def _get_cached_translation(self, text: str) -> Optional[str]:
        """
        Retrieve a cached translation if available and valid.

        Args:
            text (str): The original text to look up in cache.

        Returns:
            Optional[str]: The cached translation if found and valid, None otherwise.
        """
        if text in self.cache:
            translation, timestamp = self.cache[text]
            if self._is_cache_valid(timestamp):
                return translation
            else:
                # Remove expired entry
                del self.cache[text]
        return None

    def _cache_translation(self, text: str, translation: str):
        """
        Cache a translation result.

        Args:
            text (str): The original text.
            translation (str): The translated text.
        """
        self._clean_cache()
        self.cache[text] = (translation, time.time())

    def _translate_with_retry(self, text: str, target_lang: str = "zh-cn", 
                            source_lang: str = "en") -> Translated:
        """
        Perform translation with retry mechanism and error handling.

        Args:
            text (str): The text to translate.
            target_lang (str): Target language code (default: "zh-cn" for Chinese).
            source_lang (str): Source language code (default: "en" for English).

        Returns:
            Translated: The translation result from googletrans.

        Raises:
            TranslationError: If translation fails after all retries.
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                logging.debug(f"Translation attempt {attempt + 1} for text: '{text[:50]}...'")
                
                result = self.translator.translate(
                    text, 
                    dest=target_lang, 
                    src=source_lang
                )
                
                if result and result.text:
                    logging.debug(f"Translation successful: '{text[:50]}...' -> '{result.text[:50]}...'")
                    return result
                else:
                    raise TranslationError("Empty translation result")
                    
            except (Exception) as e:
                last_error = e
                logging.warning(f"Translation attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                    
        # All retries failed
        error_msg = f"Translation failed after {self.max_retries} attempts"
        if last_error:
            error_msg += f": {last_error}"
        raise TranslationError(error_msg, text)

    def translate_text(self, text: str, target_lang: str = "zh-cn", 
                      source_lang: str = "en") -> str:
        """
        Translate text from source language to target language.

        Args:
            text (str): The text to translate.
            target_lang (str): Target language code (default: "zh-cn" for Chinese).
            source_lang (str): Source language code (default: "en" for English).

        Returns:
            str: The translated text.

        Raises:
            TranslationError: If translation fails.
        """
        if not text or not text.strip():
            return text

        # Check cache first
        cached_result = self._get_cached_translation(text)
        if cached_result is not None:
            logging.debug(f"Using cached translation for: '{text[:50]}...'")
            return cached_result

        try:
            # Perform translation
            result = self._translate_with_retry(text, target_lang, source_lang)
            
            # Cache the result
            self._cache_translation(text, result.text)
            
            return result.text
            
        except TranslationError:
            raise
        except Exception as e:
            error_msg = f"Unexpected error during translation: {e}"
            logging.error(error_msg)
            raise TranslationError(error_msg, text)

    def translate_ocr_data(self, ocr_text: str) -> str:
        """
        Translate OCR recognized text from English to Chinese.

        Args:
            ocr_text (str): The OCR recognized text (expected to be in English).

        Returns:
            str: The Chinese translation of the input text.

        Raises:
            TranslationError: If translation fails.
        """
        return self.translate_text(ocr_text, target_lang="zh-cn", source_lang="en")

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get statistics about the translation cache.

        Returns:
            Dict[str, int]: Cache statistics including size and valid entries.
        """
        current_time = time.time()
        valid_entries = sum(
            1 for _, timestamp in self.cache.values()
            if current_time - timestamp < self.cache_ttl
        )
        
        return {
            "total_entries": len(self.cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self.cache) - valid_entries
        }

    def clear_cache(self):
        """Clear all cached translations."""
        self.cache.clear()
        logging.info("Translation cache cleared")
