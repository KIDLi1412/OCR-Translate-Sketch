"""
Test module for the translation functionality.
Tests the TranslationProcessor class and its methods.
"""

import pytest
from unittest.mock import Mock, patch

from translator import TranslationProcessor, TranslationError


class TestTranslationProcessor:
    """Test cases for TranslationProcessor class."""

    def test_init(self):
        """Test TranslationProcessor initialization."""
        processor = TranslationProcessor()
        assert processor.translator is not None
        assert processor.cache == {}
        assert processor.max_cache_size == 1000
        assert processor.cache_ttl == 3600
        assert processor.max_retries == 3
        assert processor.retry_delay == 1.0

    def test_cache_validity(self):
        """Test cache validity checking."""
        processor = TranslationProcessor()
        
        # Test with current timestamp (should be valid)
        import time
        current_time = time.time()
        assert processor._is_cache_valid(current_time) is True
        
        # Test with old timestamp (should be invalid)
        old_time = current_time - 4000  # 4000 seconds ago
        assert processor._is_cache_valid(old_time) is False

    def test_cache_operations(self):
        """Test cache operations."""
        processor = TranslationProcessor()
        
        # Test caching a translation
        processor._cache_translation("hello", "你好")
        assert "hello" in processor.cache
        assert processor.cache["hello"][0] == "你好"
        
        # Test retrieving cached translation
        cached = processor._get_cached_translation("hello")
        assert cached == "你好"
        
        # Test retrieving non-existent translation
        cached = processor._get_cached_translation("nonexistent")
        assert cached is None

    @patch('translator.Translator')
    def test_translate_text_success(self, mock_translator_class):
        """Test successful text translation."""
        # Setup mock
        mock_translator = Mock()
        mock_result = Mock()
        mock_result.text = "你好"
        mock_translator.translate.return_value = mock_result
        mock_translator_class.return_value = mock_translator
        
        processor = TranslationProcessor()
        result = processor.translate_text("hello")
        
        assert result == "你好"
        mock_translator.translate.assert_called_once_with(
            "hello", dest="zh-cn", src="en"
        )

    @patch('translator.Translator')
    def test_translate_text_with_cache(self, mock_translator_class):
        """Test text translation with caching."""
        # Setup mock
        mock_translator = Mock()
        mock_result = Mock()
        mock_result.text = "你好"
        mock_translator.translate.return_value = mock_result
        mock_translator_class.return_value = mock_translator
        
        processor = TranslationProcessor()
        
        # First translation (should call API)
        result1 = processor.translate_text("hello")
        assert result1 == "你好"
        assert mock_translator.translate.call_count == 1
        
        # Second translation (should use cache)
        result2 = processor.translate_text("hello")
        assert result2 == "你好"
        assert mock_translator.translate.call_count == 1  # Should not increase

    @patch('translator.Translator')
    def test_translate_text_empty_input(self, mock_translator_class):
        """Test translation with empty input."""
        processor = TranslationProcessor()
        
        # Test empty string
        result = processor.translate_text("")
        assert result == ""
        
        # Test whitespace only
        result = processor.translate_text("   ")
        assert result == "   "
        
        # Mock should only be called once during initialization, not for empty inputs
        assert mock_translator_class.call_count == 1  # Only during __init__
        mock_translator_instance = mock_translator_class.return_value
        mock_translator_instance.translate.assert_not_called()  # translate method should not be called

    @patch('translator.Translator')
    def test_translate_text_failure(self, mock_translator_class):
        """Test translation failure handling."""
        # Setup mock to raise exception
        mock_translator = Mock()
        mock_translator.translate.side_effect = Exception("Network error")
        mock_translator_class.return_value = mock_translator
        
        processor = TranslationProcessor()
        
        with pytest.raises(TranslationError) as exc_info:
            processor.translate_text("hello")
        
        assert "Network error" in str(exc_info.value)
        assert exc_info.value.original_text == "hello"

    def test_translate_ocr_data(self):
        """Test OCR data translation method."""
        processor = TranslationProcessor()
        
        with patch.object(processor, 'translate_text') as mock_translate:
            mock_translate.return_value = "测试文本"
            
            result = processor.translate_ocr_data("test text")
            
            assert result == "测试文本"
            mock_translate.assert_called_once_with("test text", target_lang="zh-cn", source_lang="en")

    def test_get_cache_stats(self):
        """Test cache statistics."""
        processor = TranslationProcessor()
        
        # Test empty cache
        stats = processor.get_cache_stats()
        assert stats["total_entries"] == 0
        assert stats["valid_entries"] == 0
        assert stats["expired_entries"] == 0
        
        # Test with cached data
        processor._cache_translation("hello", "你好")
        stats = processor.get_cache_stats()
        assert stats["total_entries"] == 1
        assert stats["valid_entries"] == 1
        assert stats["expired_entries"] == 0

    def test_clear_cache(self):
        """Test cache clearing."""
        processor = TranslationProcessor()
        
        # Add some data to cache
        processor._cache_translation("hello", "你好")
        assert len(processor.cache) == 1
        
        # Clear cache
        processor.clear_cache()
        assert len(processor.cache) == 0
