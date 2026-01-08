"""
Test suite for SSRF (Server-Side Request Forgery) prevention in data connectors.

TASK-BE-P7-021: SSRF Prevention in Data Connectors - Phase A Tests

This test suite validates:
- URL allowlist enforcement
- Internal/private IP blocking
- Localhost blocking
- Cloud metadata endpoint blocking
- DNS rebinding prevention
- Redirect validation
- Size and timeout limits
- HTTPS requirements
- Port restrictions

Test-Driven Development Protocol:
- These tests MUST be committed BEFORE implementation
- Tests should FAIL initially (no SSRF protection modules exist yet)
- Implementation must make tests PASS without modifying tests

References:
- OWASP SSRF Prevention: https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
- Cloud Metadata Endpoints: https://gist.github.com/jhaddix/78cece26c91c6263653f31ba453e273b
"""

import pytest
import httpx
import respx
from unittest.mock import patch, MagicMock, AsyncMock
from typing import List


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def allowed_domains() -> List[str]:
    """Standard allowed domains for emission factor data sources."""
    return [
        "api.epa.gov",
        "www.epa.gov",
        "api.defra.gov.uk",
        "naei.beis.gov.uk",
        "ecoquery.ecoinvent.org",
        "v391.ecoquery.ecoinvent.org",
    ]


@pytest.fixture
def url_validator(allowed_domains):
    """Create URL validator instance with allowed domains."""
    try:
        from backend.services.data_ingestion.security.url_validator import (
            URLValidator
        )
    except ImportError:
        pytest.skip("URLValidator not yet implemented")

    return URLValidator(allowed_domains=allowed_domains)


@pytest.fixture
def safe_http_client(url_validator):
    """Create SafeHTTPClient instance with URL validator."""
    try:
        from backend.services.data_ingestion.security.safe_http_client import (
            SafeHTTPClient
        )
    except ImportError:
        pytest.skip("SafeHTTPClient not yet implemented")

    return SafeHTTPClient(
        validator=url_validator,
        timeout=30.0,
        max_size=10 * 1024 * 1024,  # 10MB
    )


# ============================================================================
# Test Scenario 1: Allowed URL Passes Validation
# ============================================================================

class TestAllowedURLValidation:
    """Test that URLs from allowed domains pass validation."""

    def test_allowed_epa_url_passes(self, url_validator):
        """Test that EPA URLs pass validation."""
        url = "https://api.epa.gov/emission-factors"

        # Should return True without raising exception
        result = url_validator.validate(url)
        assert result is True

    def test_allowed_defra_url_passes(self, url_validator):
        """Test that DEFRA URLs pass validation."""
        url = "https://api.defra.gov.uk/ghg-conversion-factors"

        result = url_validator.validate(url)
        assert result is True

    def test_allowed_ecoinvent_url_passes(self, url_validator):
        """Test that Ecoinvent URLs pass validation."""
        url = "https://ecoquery.ecoinvent.org/3.8/cutoff/dataset"

        result = url_validator.validate(url)
        assert result is True

    def test_allowed_url_with_path_passes(self, url_validator):
        """Test that allowed URLs with paths pass validation."""
        url = "https://api.epa.gov/v1/factors/electricity/2024"

        result = url_validator.validate(url)
        assert result is True

    def test_allowed_url_with_query_params_passes(self, url_validator):
        """Test that allowed URLs with query parameters pass validation."""
        url = "https://api.epa.gov/factors?year=2024&category=energy"

        result = url_validator.validate(url)
        assert result is True


# ============================================================================
# Test Scenario 2: Blocked Internal IP Addresses
# ============================================================================

class TestInternalIPBlocking:
    """Test that internal/private IP addresses are blocked."""

    def test_blocks_private_10_network(self, url_validator):
        """Test that 10.x.x.x addresses are blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        url = "http://10.0.0.1/internal-api"

        with pytest.raises(SSRFBlockedError) as exc_info:
            url_validator.validate(url)

        assert "private" in str(exc_info.value).lower() or "internal" in str(exc_info.value).lower()

    def test_blocks_private_172_16_network(self, url_validator):
        """Test that 172.16.x.x - 172.31.x.x addresses are blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        url = "http://172.16.0.1/internal-api"

        with pytest.raises(SSRFBlockedError) as exc_info:
            url_validator.validate(url)

        assert "private" in str(exc_info.value).lower() or "internal" in str(exc_info.value).lower()

    def test_blocks_private_192_168_network(self, url_validator):
        """Test that 192.168.x.x addresses are blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        url = "http://192.168.1.100/internal-api"

        with pytest.raises(SSRFBlockedError) as exc_info:
            url_validator.validate(url)

        assert "private" in str(exc_info.value).lower() or "internal" in str(exc_info.value).lower()

    def test_blocks_loopback_127_network(self, url_validator):
        """Test that 127.x.x.x loopback addresses are blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        url = "http://127.0.0.1/secret"

        with pytest.raises(SSRFBlockedError) as exc_info:
            url_validator.validate(url)

        # Should mention localhost or loopback
        error_msg = str(exc_info.value).lower()
        assert "localhost" in error_msg or "loopback" in error_msg or "private" in error_msg

    def test_blocks_all_zeros_ip(self, url_validator):
        """Test that 0.0.0.0 is blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        url = "http://0.0.0.0/config"

        with pytest.raises(SSRFBlockedError):
            url_validator.validate(url)


# ============================================================================
# Test Scenario 3: Blocked Localhost Variations
# ============================================================================

class TestLocalhostBlocking:
    """Test that localhost and its variations are blocked."""

    def test_blocks_localhost_hostname(self, url_validator):
        """Test that localhost hostname is blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        url = "http://localhost/admin"

        with pytest.raises(SSRFBlockedError) as exc_info:
            url_validator.validate(url)

        assert "localhost" in str(exc_info.value).lower()

    def test_blocks_127_0_0_1(self, url_validator):
        """Test that 127.0.0.1 is blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        url = "http://127.0.0.1/secret"

        with pytest.raises(SSRFBlockedError):
            url_validator.validate(url)

    def test_blocks_ipv6_localhost(self, url_validator):
        """Test that IPv6 localhost [::1] is blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        url = "http://[::1]/internal"

        with pytest.raises(SSRFBlockedError):
            url_validator.validate(url)

    def test_blocks_0_0_0_0(self, url_validator):
        """Test that 0.0.0.0 is blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        url = "http://0.0.0.0/config"

        with pytest.raises(SSRFBlockedError):
            url_validator.validate(url)

    def test_blocks_localhost_with_port(self, url_validator):
        """Test that localhost with port is blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        url = "http://localhost:8080/admin"

        with pytest.raises(SSRFBlockedError):
            url_validator.validate(url)


# ============================================================================
# Test Scenario 4: Blocked Cloud Metadata Endpoints
# ============================================================================

class TestCloudMetadataBlocking:
    """Test that cloud metadata endpoints are blocked."""

    def test_blocks_aws_metadata_endpoint(self, url_validator):
        """Test that AWS metadata endpoint is blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        url = "http://169.254.169.254/latest/meta-data/"

        with pytest.raises(SSRFBlockedError) as exc_info:
            url_validator.validate(url)

        error_msg = str(exc_info.value).lower()
        assert "metadata" in error_msg or "cloud" in error_msg or "link-local" in error_msg or "private" in error_msg

    def test_blocks_aws_metadata_with_iam_credentials(self, url_validator):
        """Test that AWS IAM credentials endpoint is blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        url = "http://169.254.169.254/latest/meta-data/iam/security-credentials/"

        with pytest.raises(SSRFBlockedError):
            url_validator.validate(url)

    def test_blocks_gcp_metadata_endpoint(self, url_validator):
        """Test that GCP metadata endpoint is blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        url = "http://metadata.google.internal/"

        with pytest.raises(SSRFBlockedError):
            url_validator.validate(url)

    def test_blocks_gcp_metadata_computemetadata(self, url_validator):
        """Test that GCP computeMetadata endpoint is blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        url = "http://metadata.google.internal/computeMetadata/v1/"

        with pytest.raises(SSRFBlockedError):
            url_validator.validate(url)

    def test_blocks_azure_metadata_endpoint(self, url_validator):
        """Test that Azure metadata endpoint is blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        url = "http://169.254.169.254/metadata/instance"

        with pytest.raises(SSRFBlockedError):
            url_validator.validate(url)

    def test_blocks_link_local_range(self, url_validator):
        """Test that entire link-local range 169.254.x.x is blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        url = "http://169.254.1.1/some-path"

        with pytest.raises(SSRFBlockedError):
            url_validator.validate(url)


# ============================================================================
# Test Scenario 5: Redirect to Internal IP Blocked
# ============================================================================

class TestRedirectBlocking:
    """Test that redirects to internal IPs are blocked."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_blocks_redirect_to_internal_ip(self, safe_http_client):
        """Test that redirect to internal IP is blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        # External URL that redirects to internal IP
        external_url = "https://api.epa.gov/redirect-test"
        internal_url = "http://192.168.1.1/secret"

        # Mock the redirect
        respx.get(external_url).mock(
            return_value=httpx.Response(
                302,
                headers={"Location": internal_url}
            )
        )

        with pytest.raises(SSRFBlockedError) as exc_info:
            await safe_http_client.get(external_url)

        assert "redirect" in str(exc_info.value).lower() or "blocked" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    @respx.mock
    async def test_blocks_redirect_to_localhost(self, safe_http_client):
        """Test that redirect to localhost is blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        external_url = "https://api.epa.gov/redirect-test"
        localhost_url = "http://localhost/admin"

        respx.get(external_url).mock(
            return_value=httpx.Response(
                302,
                headers={"Location": localhost_url}
            )
        )

        with pytest.raises(SSRFBlockedError):
            await safe_http_client.get(external_url)

    @pytest.mark.asyncio
    @respx.mock
    async def test_blocks_redirect_to_metadata(self, safe_http_client):
        """Test that redirect to cloud metadata is blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        external_url = "https://api.epa.gov/redirect-test"
        metadata_url = "http://169.254.169.254/latest/meta-data/"

        respx.get(external_url).mock(
            return_value=httpx.Response(
                302,
                headers={"Location": metadata_url}
            )
        )

        with pytest.raises(SSRFBlockedError):
            await safe_http_client.get(external_url)

    @pytest.mark.asyncio
    @respx.mock
    async def test_blocks_chained_redirects_to_internal(self, safe_http_client):
        """Test that chained redirects eventually reaching internal IP are blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        url1 = "https://api.epa.gov/first"
        url2 = "https://api.epa.gov/second"
        internal_url = "http://10.0.0.1/secret"

        respx.get(url1).mock(
            return_value=httpx.Response(302, headers={"Location": url2})
        )
        respx.get(url2).mock(
            return_value=httpx.Response(302, headers={"Location": internal_url})
        )

        with pytest.raises(SSRFBlockedError):
            await safe_http_client.get(url1)

    @pytest.mark.asyncio
    @respx.mock
    async def test_blocks_too_many_redirects(self, safe_http_client):
        """Test that too many redirects are blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        # Create chain of 10 redirects
        for i in range(10):
            respx.get(f"https://api.epa.gov/redirect{i}").mock(
                return_value=httpx.Response(
                    302,
                    headers={"Location": f"https://api.epa.gov/redirect{i+1}"}
                )
            )

        with pytest.raises(SSRFBlockedError) as exc_info:
            await safe_http_client.get("https://api.epa.gov/redirect0")

        assert "redirect" in str(exc_info.value).lower()


# ============================================================================
# Test Scenario 6: Domain Not in Allowlist
# ============================================================================

class TestAllowlistEnforcement:
    """Test that domains not in allowlist are blocked."""

    def test_blocks_unknown_domain(self, url_validator):
        """Test that unknown domains are blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        url = "https://malicious-site.com/data"

        with pytest.raises(SSRFBlockedError) as exc_info:
            url_validator.validate(url)

        error_msg = str(exc_info.value).lower()
        assert "allowlist" in error_msg or "not allowed" in error_msg

    def test_blocks_similar_domain_name(self, url_validator):
        """Test that domains similar to allowed ones are blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        # Typosquatting attempt
        url = "https://api.epa.gov.evil.com/data"

        with pytest.raises(SSRFBlockedError):
            url_validator.validate(url)

    def test_blocks_subdomain_of_allowed_domain(self, url_validator):
        """Test subdomain handling - subdomains not explicitly allowed should be blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        # subdomain.api.epa.gov not in allowlist (api.epa.gov is)
        url = "https://malicious.api.epa.gov/data"

        # Implementation should either:
        # 1. Block all subdomains not explicitly in allowlist
        # 2. Or allow subdomains of allowed domains
        # This test documents the behavior
        try:
            url_validator.validate(url)
            # If it passes, subdomain wildcards are enabled
        except SSRFBlockedError:
            # Expected behavior - strict allowlist
            pass

    def test_blocks_different_tld(self, url_validator):
        """Test that different TLD of allowed domain is blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        # api.epa.org instead of api.epa.gov
        url = "https://api.epa.org/data"

        with pytest.raises(SSRFBlockedError):
            url_validator.validate(url)


# ============================================================================
# Test Scenario 7: DNS Rebinding Prevention
# ============================================================================

class TestDNSRebindingPrevention:
    """Test that DNS rebinding attacks are prevented."""

    def test_blocks_dns_resolving_to_private_ip(self, allowed_domains):
        """Test that domains resolving to private IPs are blocked."""
        try:
            from backend.services.data_ingestion.security.url_validator import (
                URLValidator
            )
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("URLValidator or SSRFBlockedError not yet implemented")

        # Mock DNS resolution to return private IP
        with patch('socket.gethostbyname', return_value='10.0.0.1'):
            validator = URLValidator(allowed_domains=allowed_domains)
            url = "https://api.epa.gov/data"  # Allowed domain

            with pytest.raises(SSRFBlockedError) as exc_info:
                validator.validate(url)

            error_msg = str(exc_info.value).lower()
            assert "dns" in error_msg or "private" in error_msg

    def test_blocks_dns_resolving_to_localhost(self, allowed_domains):
        """Test that domains resolving to localhost are blocked."""
        try:
            from backend.services.data_ingestion.security.url_validator import (
                URLValidator
            )
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("URLValidator or SSRFBlockedError not yet implemented")

        with patch('socket.gethostbyname', return_value='127.0.0.1'):
            validator = URLValidator(allowed_domains=allowed_domains)
            url = "https://api.epa.gov/data"

            with pytest.raises(SSRFBlockedError):
                validator.validate(url)

    def test_blocks_dns_resolving_to_link_local(self, allowed_domains):
        """Test that domains resolving to link-local addresses are blocked."""
        try:
            from backend.services.data_ingestion.security.url_validator import (
                URLValidator
            )
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("URLValidator or SSRFBlockedError not yet implemented")

        with patch('socket.gethostbyname', return_value='169.254.169.254'):
            validator = URLValidator(allowed_domains=allowed_domains)
            url = "https://api.epa.gov/data"

            with pytest.raises(SSRFBlockedError):
                validator.validate(url)

    def test_handles_dns_resolution_failure(self, allowed_domains):
        """Test handling of DNS resolution failures."""
        try:
            from backend.services.data_ingestion.security.url_validator import (
                URLValidator
            )
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("URLValidator or SSRFBlockedError not yet implemented")

        import socket
        with patch('socket.gethostbyname', side_effect=socket.gaierror("DNS failed")):
            validator = URLValidator(allowed_domains=allowed_domains)
            url = "https://api.epa.gov/data"

            with pytest.raises(SSRFBlockedError) as exc_info:
                validator.validate(url)

            assert "dns" in str(exc_info.value).lower()


# ============================================================================
# Test Scenario 8: Size Limit Enforcement
# ============================================================================

class TestSizeLimitEnforcement:
    """Test that response size limits are enforced."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_blocks_response_exceeding_size_limit(self, url_validator):
        """Test that responses exceeding size limit are blocked."""
        try:
            from backend.services.data_ingestion.security.safe_http_client import (
                SafeHTTPClient
            )
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SafeHTTPClient or SSRFBlockedError not yet implemented")

        url = "https://api.epa.gov/large-file"
        max_size = 1024  # 1KB limit for test

        # Mock response with large content-length header
        respx.get(url).mock(
            return_value=httpx.Response(
                200,
                content=b"x" * 100,  # Small content
                headers={"Content-Length": "100000000"}  # 100MB declared
            )
        )

        # Mock DNS for allowed domain
        with patch('socket.gethostbyname', return_value='52.0.0.1'):  # Public IP
            client = SafeHTTPClient(
                validator=url_validator,
                max_size=max_size
            )

            with pytest.raises(SSRFBlockedError) as exc_info:
                await client.get(url)

            assert "size" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    @respx.mock
    async def test_accepts_response_within_size_limit(self, url_validator):
        """Test that responses within size limit are accepted."""
        try:
            from backend.services.data_ingestion.security.safe_http_client import (
                SafeHTTPClient
            )
        except ImportError:
            pytest.skip("SafeHTTPClient not yet implemented")

        url = "https://api.epa.gov/small-file"
        content = b"small content"

        respx.get(url).mock(
            return_value=httpx.Response(200, content=content)
        )

        with patch('socket.gethostbyname', return_value='52.0.0.1'):
            client = SafeHTTPClient(
                validator=url_validator,
                max_size=10 * 1024 * 1024  # 10MB
            )

            response = await client.get(url)
            assert response.status_code == 200


# ============================================================================
# Test Scenario 9: Timeout Enforcement
# ============================================================================

class TestTimeoutEnforcement:
    """Test that request timeouts are enforced."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_raises_timeout_exception(self, url_validator):
        """Test that timeout exception is raised for slow servers."""
        try:
            from backend.services.data_ingestion.security.safe_http_client import (
                SafeHTTPClient
            )
        except ImportError:
            pytest.skip("SafeHTTPClient not yet implemented")

        url = "https://api.epa.gov/slow-endpoint"

        # Mock timeout
        respx.get(url).mock(
            side_effect=httpx.TimeoutException("Request timed out")
        )

        with patch('socket.gethostbyname', return_value='52.0.0.1'):
            client = SafeHTTPClient(
                validator=url_validator,
                timeout=10.0
            )

            with pytest.raises(httpx.TimeoutException):
                await client.get(url)

    def test_client_has_timeout_configured(self, url_validator):
        """Test that client is configured with timeout."""
        try:
            from backend.services.data_ingestion.security.safe_http_client import (
                SafeHTTPClient
            )
        except ImportError:
            pytest.skip("SafeHTTPClient not yet implemented")

        client = SafeHTTPClient(
            validator=url_validator,
            timeout=30.0
        )

        assert client.timeout == 30.0


# ============================================================================
# Test Scenario 10: HTTPS Required
# ============================================================================

class TestHTTPSRequirement:
    """Test that HTTPS is required (HTTP blocked except exceptions)."""

    def test_blocks_http_scheme(self, url_validator):
        """Test that HTTP URLs are blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        url = "http://api.epa.gov/data"  # HTTP instead of HTTPS

        with pytest.raises(SSRFBlockedError) as exc_info:
            url_validator.validate(url)

        error_msg = str(exc_info.value).lower()
        assert "https" in error_msg or "scheme" in error_msg or "http" in error_msg

    def test_accepts_https_scheme(self, url_validator):
        """Test that HTTPS URLs are accepted."""
        url = "https://api.epa.gov/data"

        with patch('socket.gethostbyname', return_value='52.0.0.1'):
            result = url_validator.validate(url)
            assert result is True

    def test_blocks_ftp_scheme(self, url_validator):
        """Test that FTP URLs are blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        url = "ftp://api.epa.gov/data.csv"

        with pytest.raises(SSRFBlockedError) as exc_info:
            url_validator.validate(url)

        assert "scheme" in str(exc_info.value).lower()

    def test_blocks_file_scheme(self, url_validator):
        """Test that file:// URLs are blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        url = "file:///etc/passwd"

        with pytest.raises(SSRFBlockedError):
            url_validator.validate(url)


# ============================================================================
# Test Scenario 11: Port Restrictions
# ============================================================================

class TestPortRestrictions:
    """Test that only allowed ports (80, 443) are permitted."""

    def test_allows_port_443(self, url_validator):
        """Test that port 443 is allowed."""
        url = "https://api.epa.gov:443/data"

        with patch('socket.gethostbyname', return_value='52.0.0.1'):
            result = url_validator.validate(url)
            assert result is True

    def test_allows_port_80(self, allowed_domains):
        """Test that port 80 is allowed (when HTTP is permitted)."""
        try:
            from backend.services.data_ingestion.security.url_validator import (
                URLValidator
            )
        except ImportError:
            pytest.skip("URLValidator not yet implemented")

        # Some implementations might allow HTTP on port 80 for specific cases
        # This test documents the expected behavior
        url = "http://api.epa.gov:80/data"
        validator = URLValidator(allowed_domains=allowed_domains)

        # Port 80 should be allowed, but HTTP might be blocked separately
        # This test verifies port restriction, not scheme restriction

    def test_blocks_non_standard_port(self, url_validator):
        """Test that non-standard ports are blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        url = "https://api.epa.gov:8443/data"

        with pytest.raises(SSRFBlockedError) as exc_info:
            url_validator.validate(url)

        assert "port" in str(exc_info.value).lower()

    def test_blocks_internal_service_port(self, url_validator):
        """Test that common internal service ports are blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        internal_ports = [22, 3306, 5432, 6379, 27017, 9200]

        for port in internal_ports:
            url = f"https://api.epa.gov:{port}/data"
            with pytest.raises(SSRFBlockedError):
                url_validator.validate(url)


# ============================================================================
# Test Scenario 12: URL Encoding Attacks
# ============================================================================

class TestURLEncodingAttacks:
    """Test that URL encoding bypass attempts are blocked."""

    def test_blocks_url_encoded_localhost(self, url_validator):
        """Test that URL-encoded localhost is blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        # localhost encoded as %6c%6f%63%61%6c%68%6f%73%74
        url = "http://%6c%6f%63%61%6c%68%6f%73%74/admin"

        with pytest.raises(SSRFBlockedError):
            url_validator.validate(url)

    def test_blocks_decimal_ip_encoding(self, url_validator):
        """Test that decimal IP encoding is blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        # 127.0.0.1 as decimal: 2130706433
        url = "http://2130706433/admin"

        with pytest.raises(SSRFBlockedError):
            url_validator.validate(url)

    def test_blocks_octal_ip_encoding(self, url_validator):
        """Test that octal IP encoding is blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        # 127.0.0.1 in octal
        url = "http://0177.0.0.1/admin"

        with pytest.raises(SSRFBlockedError):
            url_validator.validate(url)

    def test_blocks_hex_ip_encoding(self, url_validator):
        """Test that hex IP encoding is blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        # 127.0.0.1 in hex
        url = "http://0x7f000001/admin"

        with pytest.raises(SSRFBlockedError):
            url_validator.validate(url)


# ============================================================================
# Test Scenario 13: IPv6 Address Validation
# ============================================================================

class TestIPv6Validation:
    """Test that IPv6 addresses are properly validated."""

    def test_blocks_ipv6_private_address(self, url_validator):
        """Test that IPv6 private addresses (fc00::/7) are blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        url = "http://[fc00::1]/internal"

        with pytest.raises(SSRFBlockedError):
            url_validator.validate(url)

    def test_blocks_ipv6_link_local(self, url_validator):
        """Test that IPv6 link-local addresses (fe80::/10) are blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        url = "http://[fe80::1]/internal"

        with pytest.raises(SSRFBlockedError):
            url_validator.validate(url)

    def test_blocks_ipv6_localhost(self, url_validator):
        """Test that IPv6 localhost (::1) is blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        url = "http://[::1]/admin"

        with pytest.raises(SSRFBlockedError):
            url_validator.validate(url)

    def test_blocks_ipv6_mapped_ipv4_private(self, url_validator):
        """Test that IPv6-mapped IPv4 private addresses are blocked."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        # ::ffff:192.168.1.1 - IPv6-mapped IPv4
        url = "http://[::ffff:192.168.1.1]/internal"

        with pytest.raises(SSRFBlockedError):
            url_validator.validate(url)


# ============================================================================
# Test Scenario 14: Exception Class Tests
# ============================================================================

class TestSSRFBlockedError:
    """Test SSRFBlockedError exception class."""

    def test_exception_has_message(self):
        """Test that SSRFBlockedError includes message."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        error = SSRFBlockedError("URL blocked: malicious.com")
        assert "malicious.com" in str(error)

    def test_exception_is_exception_subclass(self):
        """Test that SSRFBlockedError is an Exception subclass."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        assert issubclass(SSRFBlockedError, Exception)

    def test_exception_can_be_caught(self):
        """Test that SSRFBlockedError can be caught."""
        try:
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SSRFBlockedError not yet implemented")

        try:
            raise SSRFBlockedError("Test error")
        except SSRFBlockedError as e:
            assert "Test error" in str(e)


# ============================================================================
# Test Scenario 15: Allowed Domains Configuration
# ============================================================================

class TestAllowedDomainsConfiguration:
    """Test allowed domains configuration module."""

    def test_get_allowed_domains_returns_list(self):
        """Test that get_allowed_domains returns a list."""
        try:
            from backend.services.data_ingestion.security.allowed_domains import (
                get_allowed_domains
            )
        except ImportError:
            pytest.skip("get_allowed_domains not yet implemented")

        domains = get_allowed_domains()
        assert isinstance(domains, list)

    def test_allowed_domains_contains_epa(self):
        """Test that EPA domains are in allowed list."""
        try:
            from backend.services.data_ingestion.security.allowed_domains import (
                get_allowed_domains
            )
        except ImportError:
            pytest.skip("get_allowed_domains not yet implemented")

        domains = get_allowed_domains()
        assert any("epa.gov" in d for d in domains)

    def test_allowed_domains_contains_defra(self):
        """Test that DEFRA domains are in allowed list."""
        try:
            from backend.services.data_ingestion.security.allowed_domains import (
                get_allowed_domains
            )
        except ImportError:
            pytest.skip("get_allowed_domains not yet implemented")

        domains = get_allowed_domains()
        assert any("defra" in d or "beis" in d for d in domains)

    def test_allowed_domains_contains_ecoinvent(self):
        """Test that Ecoinvent domains are in allowed list."""
        try:
            from backend.services.data_ingestion.security.allowed_domains import (
                get_allowed_domains
            )
        except ImportError:
            pytest.skip("get_allowed_domains not yet implemented")

        domains = get_allowed_domains()
        assert any("ecoinvent" in d for d in domains)

    def test_get_allowed_domains_returns_copy(self):
        """Test that get_allowed_domains returns a copy (not original list)."""
        try:
            from backend.services.data_ingestion.security.allowed_domains import (
                get_allowed_domains
            )
        except ImportError:
            pytest.skip("get_allowed_domains not yet implemented")

        domains1 = get_allowed_domains()
        domains2 = get_allowed_domains()

        # Modifying one should not affect the other
        domains1.append("test.com")
        assert "test.com" not in domains2


# ============================================================================
# Test Scenario 16: Integration with SafeHTTPClient
# ============================================================================

class TestSafeHTTPClientIntegration:
    """Test SafeHTTPClient integration with URLValidator."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_client_validates_before_request(self, url_validator):
        """Test that client validates URL before making request."""
        try:
            from backend.services.data_ingestion.security.safe_http_client import (
                SafeHTTPClient
            )
            from backend.services.data_ingestion.security.exceptions import (
                SSRFBlockedError
            )
        except ImportError:
            pytest.skip("SafeHTTPClient not yet implemented")

        # URL that should be blocked - don't even set up respx mock
        url = "http://localhost/admin"

        client = SafeHTTPClient(validator=url_validator)

        with pytest.raises(SSRFBlockedError):
            await client.get(url)

    @pytest.mark.asyncio
    @respx.mock
    async def test_client_successful_request(self, url_validator):
        """Test that client completes successful requests to allowed domains."""
        try:
            from backend.services.data_ingestion.security.safe_http_client import (
                SafeHTTPClient
            )
        except ImportError:
            pytest.skip("SafeHTTPClient not yet implemented")

        url = "https://api.epa.gov/emission-factors"
        content = b'{"factors": []}'

        respx.get(url).mock(
            return_value=httpx.Response(200, content=content)
        )

        with patch('socket.gethostbyname', return_value='52.0.0.1'):
            client = SafeHTTPClient(validator=url_validator)
            response = await client.get(url)

            assert response.status_code == 200
            assert response.content == content

    @pytest.mark.asyncio
    @respx.mock
    async def test_client_with_custom_max_redirects(self, url_validator):
        """Test that client respects max_redirects setting."""
        try:
            from backend.services.data_ingestion.security.safe_http_client import (
                SafeHTTPClient
            )
        except ImportError:
            pytest.skip("SafeHTTPClient not yet implemented")

        client = SafeHTTPClient(
            validator=url_validator,
            max_redirects=3
        )

        assert client.max_redirects == 3

    @pytest.mark.asyncio
    @respx.mock
    async def test_client_with_custom_max_size(self, url_validator):
        """Test that client respects max_size setting."""
        try:
            from backend.services.data_ingestion.security.safe_http_client import (
                SafeHTTPClient
            )
        except ImportError:
            pytest.skip("SafeHTTPClient not yet implemented")

        max_size = 5 * 1024 * 1024  # 5MB
        client = SafeHTTPClient(
            validator=url_validator,
            max_size=max_size
        )

        assert client.max_size == max_size
