"""Unit tests for streaming recovery and rate limit handling.

Tests verify:
- RateLimitInfo calculates usage percentage correctly
- StreamInterruptedError preserves partial content
- AIStreamChunk can carry error and rate limit info
- BaseProvider._stream_with_recovery wrapper behavior
"""

import time
from collections.abc import AsyncIterator

import pytest

from src.ai.gateway import AIStreamChunk, RateLimitInfo, StreamInterruptedError
from src.ai.providers.base import BaseProvider


class TestRateLimitInfoUsagePercentage:
    """Test RateLimitInfo usage_percentage property."""

    def test_usage_percentage_zero_when_no_limit(self):
        """Test usage percentage is 0 when limit is 0."""
        info = RateLimitInfo(limit_requests=0, remaining_requests=0)
        assert info.usage_percentage == 0.0

    def test_usage_percentage_zero_when_full_remaining(self):
        """Test usage percentage is 0 when all requests remaining."""
        info = RateLimitInfo(limit_requests=100, remaining_requests=100)
        assert info.usage_percentage == 0.0

    def test_usage_percentage_half(self):
        """Test usage percentage is 0.5 when half used."""
        info = RateLimitInfo(limit_requests=100, remaining_requests=50)
        assert info.usage_percentage == 0.5

    def test_usage_percentage_calculation(self):
        """Test usage percentage calculation is correct."""
        info = RateLimitInfo(limit_requests=100, remaining_requests=15)
        assert info.usage_percentage == 0.85

    def test_usage_percentage_full(self):
        """Test usage percentage is 1.0 when none remaining."""
        info = RateLimitInfo(limit_requests=100, remaining_requests=0)
        assert info.usage_percentage == 1.0


class TestRateLimitInfoIsApproachingLimit:
    """Test RateLimitInfo is_approaching_limit property."""

    def test_is_approaching_limit_below_80(self):
        """Test is_approaching_limit is False when below 80%."""
        info = RateLimitInfo(limit_requests=100, remaining_requests=25)
        assert info.is_approaching_limit is False

    def test_is_approaching_limit_at_80(self):
        """Test is_approaching_limit is True at exactly 80%."""
        info = RateLimitInfo(limit_requests=100, remaining_requests=20)
        assert info.is_approaching_limit is True

    def test_is_approaching_limit_above_80(self):
        """Test is_approaching_limit is True above 80%."""
        info = RateLimitInfo(limit_requests=100, remaining_requests=10)
        assert info.is_approaching_limit is True

    def test_is_approaching_limit_full(self):
        """Test is_approaching_limit is True when fully used."""
        info = RateLimitInfo(limit_requests=100, remaining_requests=0)
        assert info.is_approaching_limit is True


class TestRateLimitInfoSecondsUntilReset:
    """Test RateLimitInfo seconds_until_reset property."""

    def test_seconds_until_reset_none_when_no_time(self):
        """Test seconds_until_reset is None when no reset_time."""
        info = RateLimitInfo()
        assert info.seconds_until_reset is None

    def test_seconds_until_reset_calculation(self):
        """Test seconds_until_reset calculation is correct."""
        future_time = time.time() + 60
        info = RateLimitInfo(reset_time=future_time)
        # Should be approximately 60 seconds
        assert 55 <= info.seconds_until_reset <= 65

    def test_seconds_until_reset_zero_when_past(self):
        """Test seconds_until_reset is 0 when reset time passed."""
        past_time = time.time() - 10
        info = RateLimitInfo(reset_time=past_time)
        assert info.seconds_until_reset == 0


class TestRateLimitInfoTokens:
    """Test RateLimitInfo token tracking."""

    def test_token_limits_stored(self):
        """Test token limit fields are stored correctly."""
        info = RateLimitInfo(
            limit_tokens=100000,
            remaining_tokens=50000,
        )
        assert info.limit_tokens == 100000
        assert info.remaining_tokens == 50000

    def test_default_token_values(self):
        """Test token fields default to 0."""
        info = RateLimitInfo()
        assert info.limit_tokens == 0
        assert info.remaining_tokens == 0


class TestStreamInterruptedError:
    """Test StreamInterruptedError exception."""

    def test_error_stores_partial_content(self):
        """Test error stores partial content."""
        error = StreamInterruptedError("partial text here", ValueError("test"))
        assert error.partial_content == "partial text here"

    def test_error_stores_cause(self):
        """Test error stores cause exception."""
        cause = ValueError("network error")
        error = StreamInterruptedError("partial", cause)
        assert error.cause is cause

    def test_error_message_includes_length(self):
        """Test error message includes partial content length."""
        error = StreamInterruptedError("partial text here", ValueError("test"))
        # Message should mention the 17 characters
        assert "17" in str(error)

    def test_error_inherits_from_exception(self):
        """Test error is a proper Exception."""
        error = StreamInterruptedError("partial", ValueError("test"))
        assert isinstance(error, Exception)


class TestAIStreamChunkError:
    """Test AIStreamChunk error field."""

    def test_chunk_error_default_none(self):
        """Test chunk error defaults to None."""
        chunk = AIStreamChunk(content="text")
        assert chunk.error is None

    def test_chunk_with_error_info(self):
        """Test chunk can include error info."""
        chunk = AIStreamChunk(
            content="[interrupted]",
            is_final=True,
            error={"type": "TimeoutError", "message": "Connection lost"},
        )
        assert chunk.error is not None
        assert chunk.error["type"] == "TimeoutError"
        assert chunk.error["message"] == "Connection lost"

    def test_chunk_error_with_partial_length(self):
        """Test chunk error can track partial content length."""
        chunk = AIStreamChunk(
            content="[interrupted]",
            is_final=True,
            error={
                "type": "ConnectionError",
                "message": "Stream died",
                "partial_content_length": 42,
            },
        )
        assert chunk.error["partial_content_length"] == 42


class TestAIStreamChunkRateLimit:
    """Test AIStreamChunk rate_limit field."""

    def test_chunk_rate_limit_default_none(self):
        """Test chunk rate_limit defaults to None."""
        chunk = AIStreamChunk(content="text")
        assert chunk.rate_limit is None

    def test_chunk_with_rate_limit(self):
        """Test chunk can include rate limit info."""
        rate_limit = RateLimitInfo(limit_requests=100, remaining_requests=50)
        chunk = AIStreamChunk(content="text", rate_limit=rate_limit)
        assert chunk.rate_limit is not None
        assert chunk.rate_limit.usage_percentage == 0.5

    def test_chunk_rate_limit_approaching(self):
        """Test chunk rate_limit is_approaching_limit."""
        rate_limit = RateLimitInfo(limit_requests=100, remaining_requests=10)
        chunk = AIStreamChunk(content="text", rate_limit=rate_limit)
        assert chunk.rate_limit.is_approaching_limit is True


class ConcreteTestProvider(BaseProvider):
    """Concrete provider implementation for testing."""

    name = "test"
    display_name = "Test Provider"

    async def initialize(self) -> bool:
        return True

    def is_available(self) -> bool:
        return True

    async def generate(self, prompt, config):
        pass

    async def chat(self, messages, config):
        pass


class TestStreamWithRecoverySuccess:
    """Test _stream_with_recovery on successful streams."""

    @pytest.mark.asyncio
    async def test_yields_all_chunks(self):
        """Test recovery wrapper yields all chunks on success."""
        provider = ConcreteTestProvider()

        async def mock_stream() -> AsyncIterator[AIStreamChunk]:
            yield AIStreamChunk(content="Hello ")
            yield AIStreamChunk(content="world!")
            yield AIStreamChunk(content="", is_final=True)

        chunks = []
        async for chunk in provider._stream_with_recovery(mock_stream()):
            chunks.append(chunk)

        assert len(chunks) == 3

    @pytest.mark.asyncio
    async def test_preserves_content(self):
        """Test recovery wrapper preserves chunk content."""
        provider = ConcreteTestProvider()

        async def mock_stream() -> AsyncIterator[AIStreamChunk]:
            yield AIStreamChunk(content="Hello ")
            yield AIStreamChunk(content="world!")

        chunks = []
        async for chunk in provider._stream_with_recovery(mock_stream()):
            chunks.append(chunk)

        assert chunks[0].content == "Hello "
        assert chunks[1].content == "world!"

    @pytest.mark.asyncio
    async def test_preserves_is_final(self):
        """Test recovery wrapper preserves is_final flag."""
        provider = ConcreteTestProvider()

        async def mock_stream() -> AsyncIterator[AIStreamChunk]:
            yield AIStreamChunk(content="text", is_final=False)
            yield AIStreamChunk(content="", is_final=True)

        chunks = []
        async for chunk in provider._stream_with_recovery(mock_stream()):
            chunks.append(chunk)

        assert chunks[0].is_final is False
        assert chunks[1].is_final is True


class TestStreamWithRecoveryError:
    """Test _stream_with_recovery on stream errors."""

    @pytest.mark.asyncio
    async def test_yields_interrupt_marker_on_error(self):
        """Test recovery wrapper yields interrupt marker on error."""
        provider = ConcreteTestProvider()

        async def mock_stream() -> AsyncIterator[AIStreamChunk]:
            yield AIStreamChunk(content="Partial ")
            yield AIStreamChunk(content="content")
            raise ConnectionError("Stream died")

        chunks = []
        with pytest.raises(StreamInterruptedError):
            async for chunk in provider._stream_with_recovery(mock_stream()):
                chunks.append(chunk)

        # Should have yielded 2 partial chunks plus 1 error chunk = 3 total
        assert len(chunks) == 3
        # Last chunk should have interrupt marker (default is "[Response interrupted]")
        assert "interrupted" in chunks[-1].content.lower()

    @pytest.mark.asyncio
    async def test_error_chunk_is_final(self):
        """Test error chunk has is_final=True."""
        provider = ConcreteTestProvider()

        async def mock_stream() -> AsyncIterator[AIStreamChunk]:
            yield AIStreamChunk(content="Partial")
            raise ConnectionError("Stream died")

        chunks = []
        with pytest.raises(StreamInterruptedError):
            async for chunk in provider._stream_with_recovery(mock_stream()):
                chunks.append(chunk)

        assert chunks[-1].is_final is True

    @pytest.mark.asyncio
    async def test_error_chunk_has_error_info(self):
        """Test error chunk has error details."""
        provider = ConcreteTestProvider()

        async def mock_stream() -> AsyncIterator[AIStreamChunk]:
            yield AIStreamChunk(content="Partial")
            raise ConnectionError("Stream died")

        chunks = []
        with pytest.raises(StreamInterruptedError):
            async for chunk in provider._stream_with_recovery(mock_stream()):
                chunks.append(chunk)

        assert chunks[-1].error is not None
        assert chunks[-1].error["type"] == "ConnectionError"

    @pytest.mark.asyncio
    async def test_exception_has_partial_content(self):
        """Test raised exception has partial content."""
        provider = ConcreteTestProvider()

        async def mock_stream() -> AsyncIterator[AIStreamChunk]:
            yield AIStreamChunk(content="Partial ")
            yield AIStreamChunk(content="content")
            raise ConnectionError("Stream died")

        with pytest.raises(StreamInterruptedError) as exc_info:
            async for _ in provider._stream_with_recovery(mock_stream()):
                pass

        assert exc_info.value.partial_content == "Partial content"

    @pytest.mark.asyncio
    async def test_custom_interrupt_marker(self):
        """Test custom interrupt marker can be specified."""
        provider = ConcreteTestProvider()

        async def mock_stream() -> AsyncIterator[AIStreamChunk]:
            yield AIStreamChunk(content="Partial")
            raise ConnectionError("Stream died")

        chunks = []
        with pytest.raises(StreamInterruptedError):
            async for chunk in provider._stream_with_recovery(
                mock_stream(), interrupt_marker="\n[CUSTOM MARKER]"
            ):
                chunks.append(chunk)

        assert "[CUSTOM MARKER]" in chunks[-1].content


class TestBaseProviderRateLimitParsing:
    """Test BaseProvider rate limit header parsing."""

    def test_parse_rate_limit_headers(self):
        """Test parsing standard rate limit headers."""
        provider = ConcreteTestProvider()
        headers = {
            "x-ratelimit-limit-requests": "100",
            "x-ratelimit-remaining-requests": "50",
            "x-ratelimit-limit-tokens": "1000000",
            "x-ratelimit-remaining-tokens": "500000",
        }
        rate_limit = provider._parse_rate_limit_headers(headers)

        assert rate_limit.limit_requests == 100
        assert rate_limit.remaining_requests == 50
        assert rate_limit.limit_tokens == 1000000
        assert rate_limit.remaining_tokens == 500000

    def test_parse_rate_limit_headers_with_retry_after(self):
        """Test parsing Retry-After header."""
        provider = ConcreteTestProvider()
        headers = {
            "x-ratelimit-limit-requests": "100",
            "x-ratelimit-remaining-requests": "0",
            "retry-after": "60",
        }
        rate_limit = provider._parse_rate_limit_headers(headers)

        assert rate_limit.reset_time is not None
        # Should be approximately 60 seconds from now
        assert rate_limit.seconds_until_reset is not None
        assert 55 <= rate_limit.seconds_until_reset <= 65

    def test_parse_rate_limit_headers_missing(self):
        """Test parsing when headers are missing."""
        provider = ConcreteTestProvider()
        headers = {}
        rate_limit = provider._parse_rate_limit_headers(headers)

        assert rate_limit.limit_requests == 0
        assert rate_limit.remaining_requests == 0
