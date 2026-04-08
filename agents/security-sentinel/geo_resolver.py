"""
W-SEC-001 Security Sentinel — Geo Resolver
IP to Geolocation with caching for map visualization.

Uses ip-api.com (free, 45 req/min) with aggressive caching.
"""

import asyncio
import aiohttp
from typing import Optional, Dict
from functools import lru_cache
import re

# In-memory cache for geo lookups
GEO_CACHE: Dict[str, Optional[Dict]] = {}

# Private/reserved IP ranges (no geo)
PRIVATE_RANGES = [
    (r'^10\.', 'Private'),
    (r'^172\.(1[6-9]|2[0-9]|3[01])\.', 'Private'),
    (r'^192\.168\.', 'Private'),
    (r'^127\.', 'Loopback'),
    (r'^169\.254\.', 'Link-local'),
    (r'^0\.', 'Invalid'),
]


def is_private_ip(ip: str) -> bool:
    """Check if IP is private/reserved."""
    for pattern, _ in PRIVATE_RANGES:
        if re.match(pattern, ip):
            return True
    return False


async def resolve_ip_geo(ip: str) -> Optional[Dict]:
    """
    Resolve IP to geolocation.

    Returns:
        Dict with lat, lon, country, city or None if unresolvable.
    """
    # Check cache first
    if ip in GEO_CACHE:
        return GEO_CACHE[ip]

    # Skip private IPs
    if is_private_ip(ip):
        GEO_CACHE[ip] = None
        return None

    try:
        async with aiohttp.ClientSession() as session:
            # ip-api.com is free for non-commercial (45 req/min)
            url = f"http://ip-api.com/json/{ip}?fields=status,lat,lon,country,countryCode,city"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=2)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("status") == "success":
                        result = {
                            "lat": data.get("lat"),
                            "lon": data.get("lon"),
                            "country": data.get("countryCode"),
                            "country_name": data.get("country"),
                            "city": data.get("city"),
                        }
                        GEO_CACHE[ip] = result
                        return result
    except Exception:
        pass

    GEO_CACHE[ip] = None
    return None


async def batch_resolve_ips(ips: list, max_concurrent: int = 5) -> Dict[str, Optional[Dict]]:
    """
    Resolve multiple IPs concurrently with rate limiting.

    Args:
        ips: List of IP addresses
        max_concurrent: Max concurrent lookups

    Returns:
        Dict mapping IP to geo data
    """
    results = {}

    # Filter out already cached and private IPs
    to_resolve = [ip for ip in ips if ip not in GEO_CACHE and not is_private_ip(ip)]

    # Add cached results
    for ip in ips:
        if ip in GEO_CACHE:
            results[ip] = GEO_CACHE[ip]
        elif is_private_ip(ip):
            results[ip] = None

    # Resolve new IPs with rate limiting
    semaphore = asyncio.Semaphore(max_concurrent)

    async def resolve_with_limit(ip):
        async with semaphore:
            return ip, await resolve_ip_geo(ip)

    if to_resolve:
        tasks = [resolve_with_limit(ip) for ip in to_resolve[:20]]  # Limit to 20 lookups
        resolved = await asyncio.gather(*tasks, return_exceptions=True)

        for item in resolved:
            if isinstance(item, tuple):
                ip, geo = item
                results[ip] = geo

    return results


def build_geo_points(incidents: list) -> list:
    """
    Build geo points from incidents for map visualization.

    Returns list of {ip, lat, lon, country, count, severity}
    """
    # Collect unique IPs with event counts
    ip_data = {}

    for inc in incidents:
        for actor in inc.actors:
            ip = actor.get("ip")
            if not ip or is_private_ip(ip):
                continue

            if ip not in ip_data:
                ip_data[ip] = {
                    "count": 0,
                    "severity": inc.severity,
                }

            ip_data[ip]["count"] += inc.event_count

            # Escalate severity
            severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
            if severity_order.get(inc.severity, 0) > severity_order.get(ip_data[ip]["severity"], 0):
                ip_data[ip]["severity"] = inc.severity

    # Build geo points from cache
    geo_points = []

    for ip, data in ip_data.items():
        if ip in GEO_CACHE and GEO_CACHE[ip]:
            geo = GEO_CACHE[ip]
            geo_points.append({
                "ip": ip,
                "lat": geo["lat"],
                "lon": geo["lon"],
                "country": geo.get("country"),
                "city": geo.get("city"),
                "count": data["count"],
                "severity": data["severity"],
            })

    return geo_points


async def enrich_incidents_geo(incidents: list) -> list:
    """
    Enrich incidents with geo data and return geo points.

    Call this periodically to resolve new IPs.
    """
    # Collect all IPs
    all_ips = set()
    for inc in incidents:
        for actor in inc.actors:
            ip = actor.get("ip")
            if ip and not is_private_ip(ip):
                all_ips.add(ip)

    # Batch resolve (with rate limiting)
    await batch_resolve_ips(list(all_ips))

    # Build geo points
    return build_geo_points(incidents)


def get_cached_geo_points(incidents: list) -> list:
    """
    Get geo points using only cached data (no new lookups).
    Fast for SSE streaming.
    """
    return build_geo_points(incidents)
