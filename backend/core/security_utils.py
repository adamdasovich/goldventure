"""
Security Utilities for GoldVenture Platform

This module provides centralized security functions for:
- URL validation (SSRF prevention)
- IP address validation
- DNS rebinding protection
- Input sanitization

All network-related code should use these utilities to ensure consistent security.
"""

import re
import socket
import ipaddress
import logging
from typing import Tuple, Optional, List
from urllib.parse import urlparse
from functools import lru_cache

logger = logging.getLogger(__name__)

# =============================================================================
# BLOCKED HOSTS AND IPs (SSRF PREVENTION)
# =============================================================================

# Cloud metadata endpoints - CRITICAL to block
CLOUD_METADATA_HOSTS = frozenset([
    # AWS
    '169.254.169.254',
    'instance-data.ec2.internal',
    # GCP
    'metadata.google.internal',
    'metadata.goog',
    # Azure
    '169.254.169.254',  # Azure also uses this
    # DigitalOcean
    '169.254.169.254',  # DO also uses this
    # Oracle Cloud
    '169.254.169.254',
    # Alibaba Cloud
    '100.100.100.200',
])

# Localhost variations
LOCALHOST_HOSTS = frozenset([
    'localhost',
    'localhost.localdomain',
    '127.0.0.1',
    '::1',
    '0.0.0.0',
    '0',
])

# =============================================================================
# ALLOWED DOMAINS FOR DOCUMENT FETCHING
# =============================================================================

# Domains explicitly allowed for document downloads
ALLOWED_DOCUMENT_DOMAINS = frozenset([
    # Regulatory/Filing sites
    'sedar.com',
    'sedarplus.ca',
    'sec.gov',
    'edgar.sec.gov',

    # News wire services
    'newswire.ca',
    'globenewswire.com',
    'businesswire.com',
    'prnewswire.com',
    'accesswire.com',
    'newsfilecorp.com',

    # Cloud storage (for internal uploads)
    's3.amazonaws.com',
    'storage.googleapis.com',
    'blob.core.windows.net',
    'digitaloceanspaces.com',
])

# TLDs that are generally safe for mining company websites
ALLOWED_TLDS = frozenset(['.com', '.ca', '.gov', '.io', '.net', '.org', '.co', '.au', '.uk'])


# =============================================================================
# IP ADDRESS VALIDATION
# =============================================================================

def is_private_ip(ip_str: str) -> bool:
    """
    Check if an IP address is private/internal.

    Args:
        ip_str: IP address as string (IPv4 or IPv6)

    Returns:
        True if IP is private/internal, False if public
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        return (
            ip.is_private or
            ip.is_loopback or
            ip.is_link_local or
            ip.is_reserved or
            ip.is_multicast or
            ip.is_unspecified
        )
    except ValueError:
        # Invalid IP address format - treat as unsafe
        return True


def is_valid_public_ip(ip_str: str) -> Tuple[bool, str]:
    """
    Validate that an IP address is a valid public IP.

    Args:
        ip_str: IP address as string

    Returns:
        Tuple of (is_valid, reason)
    """
    if not ip_str:
        return False, "Empty IP address"

    # Basic format validation
    ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
    if not ip_pattern.match(ip_str):
        return False, f"Invalid IP format: {ip_str}"

    try:
        ip = ipaddress.ip_address(ip_str)

        if ip.is_private:
            return False, f"Private IP not allowed: {ip_str}"
        if ip.is_loopback:
            return False, f"Loopback IP not allowed: {ip_str}"
        if ip.is_link_local:
            return False, f"Link-local IP not allowed: {ip_str}"
        if ip.is_reserved:
            return False, f"Reserved IP not allowed: {ip_str}"
        if ip.is_multicast:
            return False, f"Multicast IP not allowed: {ip_str}"
        if ip.is_unspecified:
            return False, f"Unspecified IP not allowed: {ip_str}"

        # Check for cloud metadata IP
        if ip_str in CLOUD_METADATA_HOSTS:
            return False, f"Cloud metadata IP blocked: {ip_str}"

        return True, "Valid public IP"

    except ValueError as e:
        return False, f"Invalid IP address: {e}"


def validate_ip_for_ssh(ip_str: str) -> Tuple[bool, str]:
    """
    Validate an IP address before using it in SSH commands.
    Prevents command injection via malicious IP strings.

    Args:
        ip_str: IP address to validate

    Returns:
        Tuple of (is_valid, reason)
    """
    if not ip_str:
        return False, "Empty IP address"

    # Must be a valid IPv4 address format (strict)
    ip_pattern = re.compile(r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$')
    match = ip_pattern.match(ip_str)

    if not match:
        return False, f"Invalid IP format (must be IPv4): {ip_str}"

    # Each octet must be 0-255
    for octet in match.groups():
        if int(octet) > 255:
            return False, f"Invalid IP octet value: {octet}"

    # Must not contain any shell metacharacters (defense in depth)
    dangerous_chars = set(';|&$`\'"\\<>(){}[]!#')
    if any(c in ip_str for c in dangerous_chars):
        return False, f"IP contains dangerous characters: {ip_str}"

    # Validate it's a public IP (not internal)
    return is_valid_public_ip(ip_str)


# =============================================================================
# URL VALIDATION (SSRF PREVENTION)
# =============================================================================

def resolve_hostname(hostname: str) -> Optional[str]:
    """
    Resolve hostname to IP address.
    This should be called at REQUEST TIME to prevent DNS rebinding.

    Args:
        hostname: The hostname to resolve

    Returns:
        IP address string or None if resolution fails
    """
    try:
        # Use getaddrinfo for both IPv4 and IPv6
        results = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        if results:
            # Return first IP address
            return results[0][4][0]
    except socket.gaierror:
        pass
    return None


def is_safe_url(url: str, resolve_dns: bool = True) -> Tuple[bool, str]:
    """
    Check if a URL is safe to fetch (SSRF prevention).

    This function validates:
    1. URL has valid scheme (http/https only)
    2. Hostname is not internal/private
    3. Resolved IP is not internal/private (DNS rebinding protection)
    4. Not a cloud metadata endpoint

    Args:
        url: The URL to validate
        resolve_dns: If True, resolve DNS and check IP (prevents DNS rebinding)

    Returns:
        Tuple of (is_safe, reason)
    """
    if not url:
        return False, "Empty URL"

    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"Invalid URL format: {e}"

    # Must be http or https
    if parsed.scheme not in ('http', 'https'):
        return False, f"Invalid scheme: {parsed.scheme} (only http/https allowed)"

    hostname = parsed.hostname
    if not hostname:
        return False, "No hostname in URL"

    hostname_lower = hostname.lower()

    # Check for localhost variations
    if hostname_lower in LOCALHOST_HOSTS:
        return False, f"Localhost access blocked: {hostname}"

    # Check for cloud metadata endpoints
    if hostname_lower in CLOUD_METADATA_HOSTS:
        return False, f"Cloud metadata access blocked: {hostname}"

    # Check if hostname is already an IP address
    try:
        ip = ipaddress.ip_address(hostname)
        if is_private_ip(hostname):
            return False, f"Private IP address blocked: {hostname}"
    except ValueError:
        # Not an IP address, it's a hostname - continue validation
        pass

    # Check for IP-based hostname evasion attempts
    # (e.g., 0x7f.0.0.1, 017700000001, 2130706433)
    hex_ip_pattern = re.compile(r'^0x[0-9a-f]+', re.IGNORECASE)
    octal_ip_pattern = re.compile(r'^0[0-7]+$')
    decimal_ip_pattern = re.compile(r'^\d{10,}$')

    if (hex_ip_pattern.match(hostname_lower) or
        octal_ip_pattern.match(hostname_lower) or
        decimal_ip_pattern.match(hostname_lower)):
        return False, f"Encoded IP address blocked: {hostname}"

    # DNS resolution to prevent DNS rebinding attacks
    if resolve_dns:
        resolved_ip = resolve_hostname(hostname)
        if resolved_ip:
            if is_private_ip(resolved_ip):
                return False, f"Hostname resolves to private IP: {hostname} -> {resolved_ip}"
            if resolved_ip in CLOUD_METADATA_HOSTS:
                return False, f"Hostname resolves to metadata IP: {hostname} -> {resolved_ip}"

    return True, "URL is safe"


def check_url_safety(url: str, resolve_dns: bool = False) -> bool:
    """
    Simple boolean wrapper for is_safe_url().
    Use this when you only need a True/False result without the reason.

    Args:
        url: The URL to validate
        resolve_dns: Whether to resolve and validate DNS (default: False for performance)

    Returns:
        True if URL is safe, False otherwise
    """
    is_safe, _ = is_safe_url(url, resolve_dns=resolve_dns)
    return is_safe


def is_safe_document_url(url: str) -> Tuple[bool, str]:
    """
    Check if a URL is safe for fetching documents (PDFs, etc.).
    More permissive than is_safe_url - allows any HTTPS URL to trusted TLDs.

    Args:
        url: The URL to validate

    Returns:
        Tuple of (is_safe, reason)
    """
    # First, do basic safety check
    is_safe, reason = is_safe_url(url, resolve_dns=True)
    if not is_safe:
        return False, reason

    parsed = urlparse(url)
    hostname = parsed.hostname.lower() if parsed.hostname else ''

    # Check explicitly allowed domains first
    for allowed_domain in ALLOWED_DOCUMENT_DOMAINS:
        if hostname == allowed_domain or hostname.endswith('.' + allowed_domain):
            return True, f"Allowed domain: {allowed_domain}"

    # For HTTPS URLs with PDF in path, allow trusted TLDs
    if parsed.scheme == 'https':
        if any(hostname.endswith(tld) for tld in ALLOWED_TLDS):
            if '.pdf' in parsed.path.lower():
                return True, f"HTTPS PDF from trusted TLD: {hostname}"

    # Log blocked URLs for monitoring
    logger.warning(f"Document URL blocked: {url}")
    return False, f"Domain not in allowlist: {hostname}"


def validate_redirect_url(original_url: str, redirect_url: str) -> Tuple[bool, str]:
    """
    Validate a redirect URL before following it.
    Prevents SSRF via redirects.

    Args:
        original_url: The original URL that was requested
        redirect_url: The URL the server is redirecting to

    Returns:
        Tuple of (is_safe, reason)
    """
    # Handle relative redirects
    if redirect_url.startswith('/'):
        parsed_original = urlparse(original_url)
        redirect_url = f"{parsed_original.scheme}://{parsed_original.netloc}{redirect_url}"

    # Validate the redirect destination
    return is_safe_url(redirect_url, resolve_dns=True)


# =============================================================================
# INPUT SANITIZATION
# =============================================================================

def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize a filename to prevent path traversal and other attacks.

    Args:
        filename: The filename to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized filename
    """
    if not filename:
        return "unnamed"

    # Remove path components
    filename = filename.replace('/', '_').replace('\\', '_')

    # Remove null bytes
    filename = filename.replace('\x00', '')

    # Remove other dangerous characters
    filename = re.sub(r'[<>:"|?*]', '_', filename)

    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')

    # Truncate if too long
    if len(filename) > max_length:
        # Preserve extension if present
        if '.' in filename:
            name, ext = filename.rsplit('.', 1)
            ext = ext[:10]  # Max 10 char extension
            name = name[:max_length - len(ext) - 1]
            filename = f"{name}.{ext}"
        else:
            filename = filename[:max_length]

    return filename or "unnamed"


def sanitize_for_shell(value: str) -> str:
    """
    Sanitize a value for use in shell commands.
    Use this sparingly - prefer subprocess with list args instead.

    Args:
        value: The value to sanitize

    Returns:
        Sanitized value safe for shell use
    """
    if not value:
        return ""

    # Remove all shell metacharacters
    dangerous_chars = set(';|&$`\'"\\<>(){}[]!#\n\r\t')
    return ''.join(c for c in value if c not in dangerous_chars)


# =============================================================================
# EXPONENTIAL BACKOFF UTILITIES
# =============================================================================

def calculate_backoff(attempt: int, base_delay: int = 60, max_delay: int = 3600) -> int:
    """
    Calculate exponential backoff delay for retries.

    Args:
        attempt: The retry attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds

    Returns:
        Delay in seconds
    """
    delay = base_delay * (2 ** attempt)
    return min(delay, max_delay)


# =============================================================================
# REQUEST IP EXTRACTION (X-Forwarded-For Handling)
# =============================================================================

def get_client_ip(request) -> str:
    """
    Safely extract the client IP address from a Django request.

    SECURITY: X-Forwarded-For can be spoofed by attackers. This function:
    1. Only trusts X-Forwarded-For if TRUSTED_PROXY_IPS is configured in settings
    2. Validates the direct connection is from a trusted proxy before using XFF
    3. Falls back to REMOTE_ADDR (the actual TCP connection IP) otherwise

    For production behind a load balancer:
    1. Configure TRUSTED_PROXY_IPS in settings.py with your LB/proxy IPs
    2. Configure your proxy to strip any client-provided X-Forwarded-For

    Args:
        request: Django HttpRequest object

    Returns:
        Client IP address as string
    """
    from django.conf import settings

    # Get the direct connection IP (cannot be spoofed at application layer)
    remote_addr = request.META.get('REMOTE_ADDR', '')

    # Check if we have trusted proxies configured
    trusted_proxies = getattr(settings, 'TRUSTED_PROXY_IPS', None)

    if not trusted_proxies:
        # No trusted proxies configured - always use REMOTE_ADDR
        # This is the safest default
        return remote_addr

    # Convert to set for O(1) lookup
    if isinstance(trusted_proxies, (list, tuple)):
        trusted_proxies = set(trusted_proxies)

    # Only trust X-Forwarded-For if request came from a trusted proxy
    if remote_addr in trusted_proxies:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if x_forwarded_for:
            # X-Forwarded-For format: "client, proxy1, proxy2"
            # The leftmost IP is the original client (if proxies are trusted)
            client_ip = x_forwarded_for.split(',')[0].strip()
            # Basic validation - ensure it looks like an IP
            if client_ip and _is_valid_ip_format(client_ip):
                return client_ip

    # Fall back to direct connection IP
    return remote_addr


def _is_valid_ip_format(ip_str: str) -> bool:
    """
    Quick validation that a string looks like a valid IP address.
    Used to prevent injection via malformed X-Forwarded-For values.

    Args:
        ip_str: String to validate

    Returns:
        True if string is a valid IPv4 or IPv6 address format
    """
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False


# =============================================================================
# CONSTANTS FOR EXTERNAL USE
# =============================================================================

# Export these for use in other modules
__all__ = [
    # IP validation
    'is_private_ip',
    'is_valid_public_ip',
    'validate_ip_for_ssh',
    'get_client_ip',

    # URL validation
    'is_safe_url',
    'is_safe_document_url',
    'validate_redirect_url',
    'resolve_hostname',

    # Input sanitization
    'sanitize_filename',
    'sanitize_for_shell',

    # Utilities
    'calculate_backoff',

    # Constants
    'ALLOWED_DOCUMENT_DOMAINS',
    'CLOUD_METADATA_HOSTS',
]
