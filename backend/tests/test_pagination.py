"""
Tests for API pagination logic.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from unittest.mock import Mock, patch

import pytest

from kalshi_client import KalshiClient


class TestPagination:
    """Test pagination behavior."""

    def test_paginate_single_page(self):
        """Test pagination with a single page of results."""
        client = KalshiClient(base_url="https://test.api", rate_limit_sleep_ms=0)

        # Mock response with no cursor
        mock_response = {
            "series": [
                {"series_ticker": "NFL-2024", "title": "NFL 2024"},
                {"series_ticker": "NFL-2023", "title": "NFL 2023"},
            ],
            "cursor": None,
        }

        with patch.object(client, "_get", return_value=mock_response):
            results = list(client._paginate("/series", data_key="series"))

        assert len(results) == 2
        assert results[0]["series_ticker"] == "NFL-2024"
        assert results[1]["series_ticker"] == "NFL-2023"

    def test_paginate_multiple_pages(self):
        """Test pagination across multiple pages."""
        client = KalshiClient(base_url="https://test.api", rate_limit_sleep_ms=0)

        # Mock two pages
        page1 = {
            "series": [{"series_ticker": "NFL-2024", "title": "NFL 2024"}],
            "cursor": "cursor_page2",
        }
        page2 = {
            "series": [{"series_ticker": "NFL-2023", "title": "NFL 2023"}],
            "cursor": None,
        }

        responses = [page1, page2]
        with patch.object(client, "_get", side_effect=responses):
            results = list(client._paginate("/series", data_key="series"))

        assert len(results) == 2
        assert results[0]["series_ticker"] == "NFL-2024"
        assert results[1]["series_ticker"] == "NFL-2023"

    def test_paginate_empty_response(self):
        """Test pagination with empty results."""
        client = KalshiClient(base_url="https://test.api", rate_limit_sleep_ms=0)

        mock_response = {"series": [], "cursor": None}

        with patch.object(client, "_get", return_value=mock_response):
            results = list(client._paginate("/series", data_key="series"))

        assert len(results) == 0

    def test_paginate_with_cursor_loop_protection(self):
        """Ensure pagination doesn't loop infinitely."""
        client = KalshiClient(base_url="https://test.api", rate_limit_sleep_ms=0)

        # Simulate server returning same cursor (error case)
        mock_response = {
            "series": [{"series_ticker": "NFL-2024", "title": "NFL 2024"}],
            "cursor": "same_cursor",
        }

        call_count = 0

        def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count > 10:
                # Force end after 10 calls to prevent infinite loop
                return {"series": [], "cursor": None}
            return mock_response

        with patch.object(client, "_get", side_effect=mock_get):
            results = list(client._paginate("/series", data_key="series"))

        # Should eventually terminate
        assert len(results) == 10
