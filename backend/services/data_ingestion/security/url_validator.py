"""
URL Validator for SSRF Prevention.

TASK-BE-P7-021: SSRF Prevention in Data Connectors

This module implements comprehensive URL validation to prevent Server-Side
Request Forgery (SSRF) attacks. It validates URLs against:

1. Hostname blocklist (localhost, metadata endpoints)
2. IP address blocking (private, loopback, link-local)
3. Domain allowlist
4. Scheme allowlist (HTTPS required, HTTP blocked)
5. Port restrictions (only 80 and 443 allowed)
6. DNS resolution verification (prevents DNS rebinding)
7. URL encoding attack prevention

Note: IP and hostname checks are performed BEFORE scheme checks to provide
more informative error messages for SSRF attempts.

References:
- OWASP SSRF Prevention Cheat Sheet:
  https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
"""

import ipaddress
import re
import socket
from typing import List, Optional, Set, Union
from urllib.parse import urlparse, unquote

from .exceptions import SSRFBlockedError


class URLValidator:
    """
    Validates URLs to prevent SSRF attacks.

    This validator implements defense-in-depth with multiple layers of
    protection. Validation order is optimized to provide the most
    informative error messages:

    1. Hostname blocklist - Block known dangerous hosts (localhost, metadata)
    2. IP validation - Block private/internal IPs
    3. Domain allowlist - Only trusted domains
    4. Scheme validation - Only HTTPS allowed
    5. Port validation - Only standard ports (80, 443)
    6. DNS validation - Verify resolved IP is public

    Example:
        >>> validator = URLValidator(allowed_domains=["api.epa.gov"])
        >>> validator.validate("https://api.epa.gov/data")
        True
        >>> validator.validate("http://localhost/admin")
        SSRFBlockedError: Hostname blocked: localhost
    """

    # Private IPv4 ranges that must be blocked
    PRIVATE_IPV4_NETWORKS = [
        ipaddress.ip_network("10.0.0.0/8"),       # Class A private
        ipaddress.ip_network("172.16.0.0/12"),    # Class B private
        ipaddress.ip_network("192.168.0.0/16"),   # Class C private
        ipaddress.ip_network("127.0.0.0/8"),      # Loopback
        ipaddress.ip_network("169.254.0.0/16"),   # Link-local (includes cloud metadata)
        ipaddress.ip_network("0.0.0.0/8"),        # Current network
    ]

    # Private IPv6 ranges that must be blocked
    PRIVATE_IPV6_NETWORKS = [
        ipaddress.ip_network("::1/128"),          # IPv6 localhost
        ipaddress.ip_network("fc00::/7"),         # IPv6 Unique Local Address
        ipaddress.ip_network("fe80::/10"),        # IPv6 Link-local
        ipaddress.ip_network("::ffff:0:0/96"),    # IPv4-mapped IPv6 (check inner IP)
    ]

    # Hostnames that are explicitly blocked
    BLOCKED_HOSTNAMES: Set[str] = {
        "localhost",
        "metadata.google.internal",
        "metadata.internal",
        "instance-data",
    }

    # Allowed URL schemes
    ALLOWED_SCHEMES: Set[str] = {"https"}

    # Allowed ports
    ALLOWED_PORTS: Set[int] = {80, 443}

    def __init__(self, allowed_domains: List[str]):
        """
        Initialize URLValidator with allowed domains.

        Args:
            allowed_domains: List of domain names that are allowed.
        """
        self.allowed_domains: Set[str] = set(d.lower() for d in allowed_domains)

    def validate(self, url: str) -> bool:
        """
        Validate that a URL is safe to fetch.

        Performs comprehensive validation. IP and hostname checks are
        performed BEFORE scheme checks to provide informative error
        messages for SSRF attempts.

        Args:
            url: The URL to validate.

        Returns:
            True if the URL is safe to fetch.

        Raises:
            SSRFBlockedError: If the URL fails any security check.
        """
        # Decode URL to prevent encoding bypass attacks
        decoded_url = unquote(url)

        # Parse URL
        try:
            parsed = urlparse(decoded_url)
        except Exception as e:
            raise SSRFBlockedError(f"Invalid URL format: {e}")

        # Get hostname (handle None) - extract early for security checks
        hostname = parsed.hostname
        if not hostname:
            raise SSRFBlockedError("URL has no hostname")

        hostname = hostname.lower()

        # SECURITY CHECKS - check dangerous targets FIRST
        # This order provides more informative error messages

        # 1. Check for blocked hostnames (localhost, metadata endpoints)
        self._validate_hostname_not_blocked(hostname)

        # 2. Check if hostname is an IP address - validate it's not private
        if self._is_ip_address(hostname):
            self._validate_ip_address(hostname)
            # IP addresses are blocked - not in allowlist by design
            raise SSRFBlockedError(
                f"Direct IP address access not allowed: {hostname}"
            )

        # 3. Check domain against allowlist (before scheme to give informative message)
        self._validate_domain_in_allowlist(hostname)

        # PROTOCOL CHECKS - after security-critical checks
        # 4. Validate scheme
        self._validate_scheme(parsed.scheme)

        # 5. Validate port
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        self._validate_port(port)

        # 6. DNS REBINDING PROTECTION - resolve and validate IP
        self._validate_dns_resolution(hostname)

        return True

    def _validate_scheme(self, scheme: str) -> None:
        """
        Validate URL scheme is allowed.

        Args:
            scheme: The URL scheme (e.g., 'https', 'http').

        Raises:
            SSRFBlockedError: If scheme is not allowed.
        """
        if not scheme:
            raise SSRFBlockedError("URL scheme is missing")

        scheme_lower = scheme.lower()
        if scheme_lower not in self.ALLOWED_SCHEMES:
            raise SSRFBlockedError(
                f"URL scheme not allowed: {scheme}. Only HTTPS is permitted."
            )

    def _validate_port(self, port: int) -> None:
        """
        Validate port is allowed.

        Args:
            port: The port number.

        Raises:
            SSRFBlockedError: If port is not allowed.
        """
        if port not in self.ALLOWED_PORTS:
            raise SSRFBlockedError(
                f"Port not allowed: {port}. Only ports 80 and 443 are permitted."
            )

    def _validate_hostname_not_blocked(self, hostname: str) -> None:
        """
        Validate hostname is not in blocklist.

        Args:
            hostname: The hostname to check.

        Raises:
            SSRFBlockedError: If hostname is blocked.
        """
        hostname_lower = hostname.lower()

        # Check exact match
        if hostname_lower in self.BLOCKED_HOSTNAMES:
            raise SSRFBlockedError(f"Hostname blocked: localhost")

        # Check if hostname ends with a blocked suffix
        for blocked in self.BLOCKED_HOSTNAMES:
            if hostname_lower.endswith("." + blocked):
                raise SSRFBlockedError(f"Hostname blocked: {hostname}")

    def _validate_domain_in_allowlist(self, hostname: str) -> None:
        """
        Validate domain is in allowlist.

        Args:
            hostname: The hostname to check.

        Raises:
            SSRFBlockedError: If domain is not in allowlist.
        """
        hostname_lower = hostname.lower()

        # Check exact match
        if hostname_lower in self.allowed_domains:
            return

        # Check if it's a subdomain of an allowed domain
        # For security, we don't allow arbitrary subdomains by default
        # The allowlist must explicitly include subdomains

        raise SSRFBlockedError(
            f"Domain not in allowlist: {hostname}"
        )

    def _is_ip_address(self, hostname: str) -> bool:
        """
        Check if hostname is an IP address.

        Handles various IP formats including:
        - Standard IPv4 (192.168.1.1)
        - IPv6 ([::1])
        - Decimal encoded (2130706433)
        - Octal encoded (0177.0.0.1)
        - Hex encoded (0x7f000001)

        Args:
            hostname: The hostname to check.

        Returns:
            True if hostname is an IP address.
        """
        # Strip brackets from IPv6
        clean_hostname = hostname.strip("[]")

        try:
            ipaddress.ip_address(clean_hostname)
            return True
        except ValueError:
            pass

        # Check for decimal encoded IP
        if hostname.isdigit():
            return True

        # Check for hex encoded IP
        if hostname.lower().startswith("0x"):
            return True

        # Check for octal encoded IP (starts with 0 but not 0x)
        if re.match(r'^0[0-7]+\.', hostname):
            return True

        return False

    def _validate_ip_address(self, ip_string: str) -> None:
        """
        Validate IP address is not private/internal.

        Handles various IP encoding formats.

        Args:
            ip_string: The IP address string.

        Raises:
            SSRFBlockedError: If IP is private/internal.
        """
        # Strip brackets from IPv6
        ip_string = ip_string.strip("[]")

        # Convert various formats to IP address
        try:
            # Try standard format first
            ip_addr = ipaddress.ip_address(ip_string)
        except ValueError:
            # Try decimal format (e.g., 2130706433 = 127.0.0.1)
            if ip_string.isdigit():
                try:
                    decimal_ip = int(ip_string)
                    # Convert decimal to IPv4
                    ip_addr = ipaddress.ip_address(decimal_ip)
                except (ValueError, OverflowError):
                    raise SSRFBlockedError(
                        f"Invalid IP address format: {ip_string}"
                    )
            # Try hex format (e.g., 0x7f000001 = 127.0.0.1)
            elif ip_string.lower().startswith("0x"):
                try:
                    hex_ip = int(ip_string, 16)
                    ip_addr = ipaddress.ip_address(hex_ip)
                except (ValueError, OverflowError):
                    raise SSRFBlockedError(
                        f"Invalid IP address format: {ip_string}"
                    )
            # Try octal format (e.g., 0177.0.0.1 = 127.0.0.1)
            elif re.match(r'^0[0-7]', ip_string):
                try:
                    # Parse octal IP parts
                    parts = ip_string.split(".")
                    decimal_parts = []
                    for part in parts:
                        if part.startswith("0") and len(part) > 1:
                            decimal_parts.append(int(part, 8))
                        else:
                            decimal_parts.append(int(part))
                    if len(decimal_parts) == 4:
                        ip_str = ".".join(str(p) for p in decimal_parts)
                        ip_addr = ipaddress.ip_address(ip_str)
                    else:
                        raise SSRFBlockedError(
                            f"Invalid IP address format: {ip_string}"
                        )
                except (ValueError, OverflowError):
                    raise SSRFBlockedError(
                        f"Invalid IP address format: {ip_string}"
                    )
            else:
                raise SSRFBlockedError(f"Invalid IP address format: {ip_string}")

        # Check against blocklists
        self._check_ip_is_private(ip_addr)

    def _check_ip_is_private(
        self,
        ip_addr: Union[ipaddress.IPv4Address, ipaddress.IPv6Address]
    ) -> None:
        """
        Check if IP address is private/internal.

        Args:
            ip_addr: The IP address to check.

        Raises:
            SSRFBlockedError: If IP is private/internal.
        """
        # Handle IPv4-mapped IPv6 addresses
        if isinstance(ip_addr, ipaddress.IPv6Address):
            # Check for IPv4-mapped IPv6 (::ffff:x.x.x.x)
            if ip_addr.ipv4_mapped:
                # Validate the inner IPv4 address
                self._check_ip_is_private(ip_addr.ipv4_mapped)
                return

            # Check IPv6 private ranges
            for network in self.PRIVATE_IPV6_NETWORKS:
                if ip_addr in network:
                    raise SSRFBlockedError(
                        f"URL points to private/internal IP address: {ip_addr}"
                    )
        else:
            # Check IPv4 private ranges
            for network in self.PRIVATE_IPV4_NETWORKS:
                if ip_addr in network:
                    raise SSRFBlockedError(
                        f"URL points to private/internal IP address: {ip_addr}"
                    )

    def _validate_dns_resolution(self, hostname: str) -> None:
        """
        Resolve hostname and validate the IP is not private.

        This prevents DNS rebinding attacks where an attacker's DNS
        returns a private IP.

        Args:
            hostname: The hostname to resolve.

        Raises:
            SSRFBlockedError: If DNS resolution fails or returns private IP.
        """
        try:
            # Resolve hostname to IP
            ip_string = socket.gethostbyname(hostname)
            ip_addr = ipaddress.ip_address(ip_string)

            # Validate resolved IP is not private
            self._check_ip_is_private(ip_addr)

        except socket.gaierror as e:
            raise SSRFBlockedError(f"DNS resolution failed for hostname: {hostname}")
        except SSRFBlockedError:
            # Re-raise with DNS-specific message
            raise SSRFBlockedError(
                f"DNS resolution returned private IP for hostname: {hostname}"
            )
