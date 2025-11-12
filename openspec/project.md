# Project Context

## Purpose
BoxLab Media Server Stack is a curated fork of Ezarr that generates a docker compose based “ultimate Jellyfin stack.” The Python CLI lets operators pick which Servarr, download, automation, dashboard, and monitoring apps to run, then emits a TRaSH-guideline-compliant compose file plus optional filesystem/user bootstrap so the apps interoperate out of the box.

## Tech Stack
- Python 3 modules (`main.py`, `container_configs.py`, `users_groups_setup.py`) for interactive prompts, compose templating, and permission scaffolding using only the standard library.
- Bash scripts (`setup.sh`, `update_containers.sh`, `remove_old_users.sh`) for `.env` driven provisioning, upgrades, and cleanup when not using the CLI.
- Docker Engine with docker compose v2 orchestrates linuxserver.io and other upstream containers (Sonarr, Radarr, qBittorrent, Jellyfin, Plex, SABnzbd, Tdarr, etc.).
- Configuration lives under `$ROOT_DIR` following TRaSH hardlink-friendly layouts (`config/*-config`, `data/{media,torrents,usenet,...}`) so downloads and media share the same filesystem.
- OpenSpec spec-driven workflow gates major feature, architecture, or security changes before implementation.

## Project Conventions

### Code Style
- Python code generally follows PEP 8: snake_case names, short helper functions, and no external dependencies; service-specific compose fragments stay in dedicated `ContainerConfig` methods for readability.
- Compose YAML is emitted as deterministic 2-space-indented strings so diffs remain stable and amenable to manual edits.
- Shell scripts target `/bin/bash`, export `.env` values with `set -a`, and prefer explicit `sudo` invocations instead of running the entire script as root.

### Architecture Patterns
- Interactive workflow: `main.py` categorizes services (Servarr, indexers, servers, automation, infra), prompts for required settings (timezone, root paths, optional VPN/Jellystat secrets), and writes `docker-compose.yml`.
- `ContainerConfig` encapsulates every service definition; enabling a service simply calls the matching method, keeping compose generation additive and predictable.
- `UserGroupSetup` (or `setup.sh`) creates the `mediacenter` group, per-service users (UIDs 13001–13020), directories, and permissions so hardlinks and NFS shares behave consistently.
- Manual installations mirror the CLI by populating `.env`, running `setup.sh`, copying `docker-compose.yml.sample`, and editing services in or out as needed.

### Testing Strategy
- No automated tests yet; validate changes by running `python3 main.py`, generating a compose file, and executing `docker compose config && docker compose up -d` on a Linux host.
- Exercise provisioning scripts in a sandbox VM before shipping changes that touch permissions or `.env` parsing, because they rely on `sudo useradd/groupadd` side effects.
- After compose updates, launch only the affected containers to verify environment variables, ports, and volumes resolve as expected.

### Git Workflow
- Treat `main` as the source of truth; develop changes in feature branches or forks and open PRs back to `main`.
- Large features, architecture updates, or behavioral changes require an OpenSpec proposal (`openspec/changes/<change-id>/`) that is validated with `openspec validate --strict` before coding.
- Reference the change ID in commit messages/PRs, keep commits scoped to a specific service or script, and update `tasks.md` checklists when implementation work finishes.

## Domain Context
- Goal is to provide a self-hosted “ultimate Jellyfin stack” that bundles Servarr apps (Sonarr/Radarr/Lidarr/Readarr/Mylar3/Kapowarr), indexers (Prowlarr, Jackett), download clients (qBittorrent, SABnzbd), dashboards (Homarr, Wizarr), monitoring (Dozzle, Jellystat, Tautulli), and automation (Tdarr, Decluttarr, Janitorr, Profilarr).
- Directory layout mirrors TRaSH hardlink guidance: `/data/media/*` holds organized libraries while `/data/{torrents,usenet}` store incoming downloads on the same filesystem to enable hardlink moves.
- Deployments often span NFS shares; matching UID/GID mappings on every host is critical so containers see consistent permissions.
- Security-sensitive items (API keys, VPN credentials, Jellystat secrets, Wizarr URLs) are intentionally collected interactively and never committed.

## Important Constraints
- Linux hosts only—`setup.sh` and `UserGroupSetup` rely on GNU userland tools (`useradd`, `groupadd`, `chown`, `sudo`) and will fail on macOS/Windows.
- Docker Compose v2 is required; the CLI assumes `docker compose` syntax and linuxserver.io images that honor PUID/PGID/TZ environment variables.
- Service users occupy fixed UID slots (13001–13020) inside the `mediacenter` group; check for collisions before provisioning and keep IDs in sync across NFS server/client pairs.
- `$ROOT_DIR` must be an absolute path on a single filesystem to preserve hardlinks; replicate directory/user setup on each machine that mounts the share.
- The generator intentionally avoids configuring API keys, password secrets, or provider logins—operators must finish those steps manually to avoid shared credentials.

## External Dependencies
- Docker Engine, docker compose plugin v2, and standard Linux tools (`bash`, `sudo`, `useradd`, `chown`, `mkdir`, `id`).
- Container images from linuxserver.io and upstream projects: Sonarr, Radarr, Lidarr, Readarr, Mylar3, Bazarr, Kapowarr, Audiobookshelf, Homarr, Jellyfin, Plex, Tautulli, Overseerr, Jellyseerr, qBittorrent, SABnzbd, Prowlarr, Jackett, Tdarr, Wizarr, Decluttarr, Janitorr, Profilarr, Jellystat (+ Postgres), Gluetun, Dozzle, Autobrr.
- Optional infrastructure such as VPN providers supported by Gluetun (Mullvad, etc.) and NFS servers/clients for shared storage.
