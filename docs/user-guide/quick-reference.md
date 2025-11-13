# 🚀 BoxLab Quick Reference

## Single-Command Execution

```bash
./boxlab
```

## What It Does

1. **Shows Beautiful Banner** - Welcome message with styled UI
2. **Service Selection** - Multi-select menu with 28 services
3. **VPN Configuration** - Optional wizard for Mullvad, ProtonVPN, NordVPN, IVPN, Custom
4. **Optional Services** - Wizarr (invitation system), Jellystat (Jellyfin analytics)
5. **Permission Setup** - Creates users, groups, directories with correct ownership
6. **Docker Compose Generation** - Creates docker-compose.yml with selected services
7. **Environment File** - Generates .env with all settings
8. **Ready to Deploy** - Just run `docker compose up -d`

## Directory Structure

```
/opt/media/                    # Default media directory
├── data/
│   ├── media/                # Media files
│   │   ├── movies/
│   │   ├── tv/
│   │   ├── music/
│   │   └── books/
│   ├── torrents/             # Download directory
│   │   ├── movies/
│   │   ├── tv/
│   │   └── music/
│   └── usenet/               # Usenet downloads
│       ├── movies/
│       ├── tv/
│       └── music/
└── config/                   # Service configurations
    ├── plex/
    ├── sonarr/
    ├── radarr/
    └── ...
```

## Service Categories

### 🎬 Media Servers

- **Plex**, **Jellyfin**, **Emby**, **Kodi**

### 📺 PVR / Automation

- **Sonarr**, **Radarr**, **Lidarr**, **Readarr**, **Bazarr**, **Prowlarr**, **Overseerr**

### 📦 Download Clients

- **qBittorrent**, **Deluge**, **Transmission**, **SABnzbd**, **NZBGet**

### 📊 Monitoring & Dashboards

- **Tautulli**, **Organizr**, **Homarr**, **Heimdall**, **Dashy**, **Homepage**

### 🎯 Request Management

- **Overseerr**, **Jellyseerr**, **Wizarr**

### 🔐 VPN & Networking

- **Gluetun**

### 📚 Other Services

- **Komga**, **Kavita**, **FlareSolverr**

## VPN Providers

| Provider  | Type              | Configuration                |
| --------- | ----------------- | ---------------------------- |
| Mullvad   | WireGuard         | Account number + private key |
| ProtonVPN | WireGuard         | Username + private key       |
| NordVPN   | WireGuard         | Private key + address        |
| IVPN      | WireGuard         | Username + private key       |
| Custom    | WireGuard/OpenVPN | Manual configuration         |

## Default Ports

| Service     | Port  | Access                     |
| ----------- | ----- | -------------------------- |
| Plex        | 32400 | http://localhost:32400/web |
| Jellyfin    | 8096  | http://localhost:8096      |
| Sonarr      | 8989  | http://localhost:8989      |
| Radarr      | 7878  | http://localhost:7878      |
| qBittorrent | 8080  | http://localhost:8080      |
| Prowlarr    | 9696  | http://localhost:9696      |
| Overseerr   | 5055  | http://localhost:5055      |
| Tautulli    | 8181  | http://localhost:8181      |

## User IDs & Groups

| User        | UID   | Purpose                |
| ----------- | ----- | ---------------------- |
| mediacenter | 13000 | Group for all services |
| plex        | 13001 | Plex service           |
| sonarr      | 13002 | Sonarr service         |
| radarr      | 13003 | Radarr service         |
| qbittorrent | 13004 | qBittorrent service    |
| ...         | ...   | ...                    |

## Common Commands

### Start Services

```bash
docker compose up -d
```

### Stop Services

```bash
docker compose down
```

### View Logs

```bash
docker compose logs -f [service-name]
```

### Restart Service

```bash
docker compose restart [service-name]
```

### Update Services

```bash
docker compose pull
docker compose up -d
```

### Check Status

```bash
docker compose ps
```

## Troubleshooting

### Gum Not Found

```bash
bash scripts/install_gum.sh
```

### Permission Errors

```bash
sudo bash setup_permissions.sh
```

### Import Errors

```bash
# Make sure you're running from project root
cd /path/to/boxlab-media-server-stack
./boxlab
```

### Service Won't Start

```bash
# Check logs
docker compose logs [service-name]

# Verify permissions
ls -la /opt/media/config/[service-name]

# Check if port is in use
sudo lsof -i :[port-number]
```

### VPN Not Working

```bash
# Check Gluetun logs
docker compose logs gluetun

# Verify VPN credentials in .env
cat .env | grep VPN

# Test connectivity
docker compose exec gluetun sh -c "curl ifconfig.me"
```

## Files Generated

| File                   | Purpose                 |
| ---------------------- | ----------------------- |
| `docker-compose.yml`   | Service definitions     |
| `.env`                 | Environment variables   |
| `setup_permissions.sh` | Permission setup script |

## Environment Variables

| Variable                | Example            | Description    |
| ----------------------- | ------------------ | -------------- |
| `ROOT_DIR`              | `/opt/media`       | Base directory |
| `PUID`                  | `13001`            | User ID        |
| `PGID`                  | `13000`            | Group ID       |
| `TIMEZONE`              | `America/New_York` | Timezone       |
| `VPN_SERVICE_PROVIDER`  | `mullvad`          | VPN provider   |
| `WIREGUARD_PRIVATE_KEY` | `xxx`              | WG private key |

## Best Practices

✅ **DO:**

- Use hardlinks (same filesystem for media & downloads)
- Set up VPN for torrent clients
- Configure Prowlarr for all \*arr services
- Use Overseerr for media requests
- Monitor with Tautulli
- Back up configuration directories

❌ **DON'T:**

- Run services as root
- Use different filesystems for media & downloads
- Expose services directly to internet without reverse proxy
- Share VPN credentials publicly
- Delete torrents immediately (breaks hardlinks)

## Quick Links

- **Documentation:** [README.md](./README.md)
- **Changes:** [CHANGES.md](./CHANGES.md)
- **Comparison:** [COMPARISON.md](./COMPARISON.md)
- **Proposal:** [openspec/changes/refactor-clean-architecture/proposal.md](./openspec/changes/refactor-clean-architecture/proposal.md)

## Getting Help

1. Check [README.md](./README.md) troubleshooting section
2. Review [CHANGES.md](./CHANGES.md) for migration notes
3. Check Docker logs: `docker compose logs [service]`
4. Verify permissions: `ls -la /opt/media`
5. Test Gum: `bin/gum --version`

## Version Info

- **Python:** 3.8+ required
- **Docker:** Compose V2 required
- **Gum:** v0.17.0 bundled
- **Platform:** Linux, macOS (x86_64, ARM64)

---

**Happy Streaming! 🎬🍿**
