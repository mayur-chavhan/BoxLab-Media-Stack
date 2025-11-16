"""Service definitions and metadata for all supported *arr services."""

from typing import TypedDict


class ServiceMetadata(TypedDict):
    """Metadata for a supported service."""

    name: str
    description: str
    image: str
    default_port: int
    category: str
    required_volumes: list[str]
    trash_guides_url: str | None


SUPPORTED_SERVICES: dict[str, ServiceMetadata] = {
    "sonarr": {
        "name": "Sonarr",
        "description": "TV show automation and management",
        "image": "lscr.io/linuxserver/sonarr:latest",
        "default_port": 8989,
        "category": "media_management",
        "required_volumes": ["/config", "/data"],
        "trash_guides_url": "https://trash-guides.info/Sonarr/",
    },
    "radarr": {
        "name": "Radarr",
        "description": "Movie automation and management",
        "image": "lscr.io/linuxserver/radarr:latest",
        "default_port": 7878,
        "category": "media_management",
        "required_volumes": ["/config", "/data"],
        "trash_guides_url": "https://trash-guides.info/Radarr/",
    },
    "prowlarr": {
        "name": "Prowlarr",
        "description": "Indexer manager for *arr apps",
        "image": "lscr.io/linuxserver/prowlarr:latest",
        "default_port": 9696,
        "category": "media_management",
        "required_volumes": ["/config"],
        "trash_guides_url": "https://trash-guides.info/Prowlarr/",
    },
    "bazarr": {
        "name": "Bazarr",
        "description": "Subtitle management",
        "image": "lscr.io/linuxserver/bazarr:latest",
        "default_port": 6767,
        "category": "media_management",
        "required_volumes": ["/config", "/data"],
        "trash_guides_url": "https://trash-guides.info/Bazarr/",
    },
    "recyclarr": {
        "name": "Recyclarr",
        "description": "TRaSH-Guides sync automation",
        "image": "ghcr.io/recyclarr/recyclarr:latest",
        "default_port": 0,  # No web UI
        "category": "media_management",
        "required_volumes": ["/config"],
        "trash_guides_url": "https://trash-guides.info/Recyclarr/",
    },
    "jellyfin": {
        "name": "Jellyfin",
        "description": "Open-source media server",
        "image": "lscr.io/linuxserver/jellyfin:latest",
        "default_port": 8096,
        "category": "media_server",
        "required_volumes": ["/config", "/data/media"],
        "trash_guides_url": None,
    },
    "emby": {
        "name": "Emby",
        "description": "Media server (proprietary)",
        "image": "lscr.io/linuxserver/emby:latest",
        "default_port": 8096,
        "category": "media_server",
        "required_volumes": ["/config", "/data/media"],
        "trash_guides_url": None,
    },
    "plex": {
        "name": "Plex",
        "description": "Media server (requires account)",
        "image": "lscr.io/linuxserver/plex:latest",
        "default_port": 32400,
        "category": "media_server",
        "required_volumes": ["/config", "/data/media"],
        "trash_guides_url": None,
    },
    "jellyseerr": {
        "name": "Jellyseerr",
        "description": "Request management for Jellyfin",
        "image": "fallenbagel/jellyseerr:latest",
        "default_port": 5055,
        "category": "request_management",
        "required_volumes": ["/app/config"],
        "trash_guides_url": None,
    },
    "overseerr": {
        "name": "Overseerr",
        "description": "Request management for Plex",
        "image": "lscr.io/linuxserver/overseerr:latest",
        "default_port": 5055,
        "category": "request_management",
        "required_volumes": ["/config"],
        "trash_guides_url": None,
    },
    "jackett": {
        "name": "Jackett",
        "description": "Indexer proxy (legacy)",
        "image": "lscr.io/linuxserver/jackett:latest",
        "default_port": 9117,
        "category": "download_indexer",
        "required_volumes": ["/config", "/downloads"],
        "trash_guides_url": None,
    },
    "autobrr": {
        "name": "Autobrr",
        "description": "Torrent automation",
        "image": "ghcr.io/autobrr/autobrr:latest",
        "default_port": 7474,
        "category": "download_indexer",
        "required_volumes": ["/config"],
        "trash_guides_url": None,
    },
    "tdarr": {
        "name": "Tdarr",
        "description": "Transcoding automation",
        "image": "ghcr.io/haveagitgat/tdarr:latest",
        "default_port": 8265,
        "category": "media_processing",
        "required_volumes": ["/app/server", "/app/configs", "/data"],
        "trash_guides_url": None,
    },
    "unpackerr": {
        "name": "Unpackerr",
        "description": "Archive extraction",
        "image": "golift/unpackerr:latest",
        "default_port": 0,  # No web UI
        "category": "media_processing",
        "required_volumes": ["/config", "/data"],
        "trash_guides_url": None,
    },
}


def get_services_by_category() -> dict[str, list[str]]:
    """Group services by category."""
    categories: dict[str, list[str]] = {}
    for service_id, metadata in SUPPORTED_SERVICES.items():
        category = metadata["category"]
        if category not in categories:
            categories[category] = []
        categories[category].append(service_id)
    return categories


def get_service_metadata(service_id: str) -> ServiceMetadata | None:
    """Get metadata for a specific service."""
    return SUPPORTED_SERVICES.get(service_id)
