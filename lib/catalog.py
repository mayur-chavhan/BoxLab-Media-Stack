"""
Service catalog with metadata and dependencies.
Defines all available self-hosted applications.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class Service:
    """Represents a self-hosted application service."""
    key: str
    name: str
    category: str
    description: str
    requires: Tuple[str, ...] = ()
    tags: Tuple[str, ...] = ()


SERVICE_CATEGORIES: Dict[str, str] = {
    "servarr": "📺 Media Management",
    "media-server": "🎬 Media Servers & Portals",
    "indexer": "🔍 Indexers & Bypass",
    "download": "⬇️  Download Clients",
    "automation": "🤖 Automation & Optimization",
    "infra": "🔧 Infrastructure & Utilities",
}

SERVICES: List[Service] = [
    # Servarr Apps
    Service("sonarr", "Sonarr", "servarr", "Automates TV series libraries"),
    Service("radarr", "Radarr", "servarr", "Movie automation companion"),
    Service("lidarr", "Lidarr", "servarr", "Music automation for Servarr"),
    Service("readarr", "Readarr", "servarr", "Book download automation"),
    Service("mylar3", "Mylar3", "servarr", "Comic book manager"),
    Service("kapowarr", "Kapowarr", "servarr", "Another comic-focused downloader"),
    Service("bazarr", "Bazarr", "servarr", "Subtitle automation companion", requires=("sonarr", "radarr")),
    
    # Media Servers
    Service("plex", "Plex", "media-server", "Commercial media server"),
    Service("tautulli", "Tautulli", "media-server", "Plex monitoring dashboard", requires=("plex",)),
    Service("jellyfin", "Jellyfin", "media-server", "Open-source media server"),
    Service("overseerr", "Overseerr", "media-server", "Requests for Plex/Servarr", requires=("plex", "sonarr", "radarr")),
    Service("jellyseerr", "Jellyseerr", "media-server", "Requests for Jellyfin", requires=("jellyfin",)),
    Service("wizarr", "Wizarr", "media-server", "One-click invites for Plex/Jellyfin", requires=("plex", "jellyfin")),
    Service("jellystat", "Jellystat", "media-server", "Jellyfin analytics", requires=("jellyfin",)),
    Service("audiobookshelf", "Audiobookshelf", "media-server", "Self-hosted audiobooks and podcasts"),
    Service("homarr", "Homarr", "media-server", "Landing dashboard for your stack"),
    
    # Indexers
    Service("prowlarr", "Prowlarr", "indexer", "Indexer aggregator and sync"),
    Service("jackett", "Jackett", "indexer", "Indexer proxy alternative"),
    Service("flaresolverr", "Flaresolverr", "indexer", "Cloudflare bypass helper"),
    
    # Download Clients
    Service("qbittorrent", "qBittorrent", "download", "BitTorrent client"),
    Service("sabnzbd", "SABnzbd", "download", "Usenet downloader"),
    
    # Automation
    Service("tdarr", "Tdarr", "automation", "Distributed media transcoding"),
    Service("decluttarr", "Decluttarr", "automation", "Queue cleanup for Servarr"),
    Service("janitorr", "Janitorr", "automation", "Library hygiene automation"),
    Service("profilarr", "Profilarr", "automation", "Central Profile + CF sync"),
    
    # Infrastructure
    Service("gluetun", "Gluetun", "infra", "VPN networking proxy"),
    Service("autobrr", "Autobrr", "infra", "Tracker/IRC automation"),
    Service("dozzle", "Dozzle", "infra", "Real-time container log dashboard"),
]


def services_by_category() -> Dict[str, List[Service]]:
    """Group services by their category."""
    mapping: Dict[str, List[Service]] = {key: [] for key in SERVICE_CATEGORIES}
    for service in SERVICES:
        mapping.setdefault(service.category, []).append(service)
    for bucket in mapping.values():
        bucket.sort(key=lambda s: s.name.lower())
    return mapping


def service_lookup() -> Dict[str, Service]:
    """Create a key-to-service lookup dictionary."""
    return {svc.key: svc for svc in SERVICES}


def expand_dependencies(selected: Iterable[str]) -> List[str]:
    """
    Given a list of selected services, include required dependencies.
    Returns a list with dependencies resolved in proper order.
    """
    lookup = service_lookup()
    resolved: List[str] = []
    pending = list(dict.fromkeys(selected))  # preserve order, drop duplicates
    
    while pending:
        key = pending.pop(0)
        if key in resolved:
            continue
        resolved.append(key)
        requires = lookup.get(key).requires if key in lookup else ()
        for dep in requires:
            if dep not in resolved and dep not in pending:
                pending.append(dep)
    
    return resolved
