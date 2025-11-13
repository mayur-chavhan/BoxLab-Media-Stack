# 🎬 BoxLab Media Server Stack# BoxLab Media Server Stack

> **Your Ultimate Self-Hosted Media Automation Stack**BoxLab Media Server Stack is a curated fork of the excellent Ezarr project with the additional

> applications that power the "Ultimate Jellyfin Stack". You still get the battle-tested Ezarr CLI,

> A beautiful, interactive installer for deploying a complete media automation ecosystem with Sonarr, Radarr, Jellyfin, Plex, and 20+ other services.folder layout, and hardlink-friendly defaults, but now with optional access to all of the extra

arr/automation/monitoring tools many of us rely on.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)It's set up to follow the [TRaSH guidelines](https://trash-guides.info/Hardlinks/How-to-setup-for/Docker/) so it should at least perform optimally. It features:

- [Sonarr](https://sonarr.tv/) is an application to manage TV shows. It is capable of keeping track

--- of what you'd like to watch, at what quality, in which language and more, and can find a place to

download this if connected to Prowlarr and qBittorrent. It can also reorganize the media you

## ✨ Features already own in order to create a more uniformly formatted collection.

- [Radarr](https://radarr.video/) is like Sonarr, but for movies.

- 🎨 **Beautiful TUI** - Elegant terminal interface powered by [Charm's Gum](https://github.com/charmbracelet/gum)- [Bazarr](https://www.bazarr.media/) is a companion application to Sonarr and Radarr that manages

- 🚀 **One-Command Setup** - Interactive wizard guides you through the entire installation and downloads subtitles based on your requirements.

- 🔒 **Built-in VPN Support** - Optional Gluetun configuration with multiple provider support- [Lidarr](https://lidarr.audio/) is like Sonarr, but for music.

- 📦 **28 Self-Hosted Apps** - From media servers to automation tools- [Readarr](https://readarr.com/) is like Sonarr, but for books.

- ⚡ **Smart Dependencies** - Automatically includes required services- [Mylar3](https://github.com/mylar3/mylar3) is like Sonarr, but for comic books. This one is a bit

- 🛡️ **TRaSH Guidelines** - Follows best practices for hardlink-friendly setups tricky to set up, so do so at your own risk. In order to connect this to your Prowlarr container,

- 🔧 **Automatic Permissions** - Creates users, groups, and folder structures the process within Prowlarr is the same as for the other containers (add app). You'll have to add

- 🐳 **Docker Compose** - Generates clean, production-ready compose files an API key within Mylar3, yourself.

- [Audiobookshelf](https://www.audiobookshelf.org/) is a self-hosted audiobook and podcast server.

---- [Homarr](https://homarr.dev/) is _a sleek, modern dashboard that puts all of your apps and services at your fingertips._

- [Prowlarr](https://wiki.servarr.com/prowlarr) can keep track of indexers, which are services that

## 🎯 Quick Start keep track of Torrent or UseNet links. One can search an indexer for certain content and find a

where to download this. **Note**: when adding an indexer, please do not set the "seed ratio" to

### Prerequisites less than 1. Less than 1 means that you upload less than you download. Not only is this

unfriendly towards your fellow users, but it can also get you banned from certain indexers.

- **Linux** (Ubuntu, Debian, Arch, etc.)- [Jackett](https://github.com/Jackett/Jackett) is an alternative to Prowlarr.

- **Python 3.8+**- [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) is a proxy server to bypass Cloudflare and DDoS-GUARD protection.

- **Docker** with **Docker Compose v2**- [qBittorrent](https://www.qbittorrent.org/) can download torrents and provides a bunch more

- **Charm Gum** (included for Linux x86_64, see [Installation](#-installation) for other platforms) features for management.

- [SABnzbd](https://sabnzbd.org/) can download nzb's

### One-Line Install features for management.

- [PleX](https://www.plex.tv/) is a mediaserver. Using this, you get access to a Netflix-like

````bash interface across many devices like your laptop or computer, your phone, your TV and more. For

git clone https://github.com/mayur-chavhan/boxlab-media-server-stack.git  some features, you need a [PleX pass](https://www.plex.tv/nl/plex-pass/).

cd boxlab-media-server-stack- [Tautulli](https://tautulli.com/) is a monitoring application for PleX  which can keep track of

./boxlab  what has been watched, who watched it, when and where they watched it, and how it was watched.

```- [Jellyfin](https://jellyfin.org/) is an alternative for PleX. Which you'd like to use is a matter

  of preference, and you *could* even use both, although this is probably a waste of resources.

That's it! The interactive installer will guide you through:- [Overseerr](https://overseerr.dev/) is a show and movie request management and media discovery

1. 📱 **Select Applications** - Choose from 28+ self-hosted apps   tool.

2. 🔐 **Configure VPN** - Optional Gluetun setup with provider wizard- [Jellyseerr](https://github.com/Fallenbagel/jellyseerr) is like Overseerr, but for Jellyfin.

3. ⚙️  **Basic Settings** - Timezone, storage path, service-specific configs- [Kapowarr](https://github.com/mRcS-IT/kapowarr) keeps up with your comic libraries and can feed the same download clients.

4. ✅ **Review & Confirm** - Summary of your selections- [Tdarr](https://github.com/haveagitgat/Tdarr) automates media transcoding and pruning.

5. 🚀 **Deploy** - Generates docker-compose.yml and sets up permissions- [Autobrr](https://autobrr.com/) joins tracker IRC channels so you can grab torrents immediately.

- [Gluetun](https://github.com/qdm12/gluetun) provides a hardened WireGuard/OpenVPN tunnel for the containers you want to run behind a VPN.

---- [Wizarr](https://wizarrrr.com/) generates one-click invites to your media server.

- [Dozzle](https://github.com/amir20/dozzle) gives you a simple, searchable Docker log dashboard.

## 📦 Available Applications- [Decluttarr](https://github.com/manimatter/decluttarr) keeps your Sonarr/Radarr/Lidarr queues clean and removes stale downloads.

- [Jellystat](https://github.com/CyferShepard/jellystat) collects Jellyfin playback analytics (with an optional Postgres backing store).

### 📺 Media Management (Servarr)- [Janitorr](https://github.com/schaka/janitorr) cleans up untagged media and stale library entries.

- **Sonarr** - TV series automation- [Profilarr](https://github.com/Dictionarry-Hub/profilarr) manages per-instance quality profiles and custom formats from a single UI.

- **Radarr** - Movie automation

- **Lidarr** - Music automation> **Heads-up:** Gluetun is shipped as a standalone VPN container. If you want to tunnel qBittorrent, Prowlarr, Autobrr, etc. you still need to edit the generated compose file and attach those services via `network_mode: "service:gluetun"`.

- **Readarr** - Book automation

- **Mylar3** - Comic book management## Requirements

- **Kapowarr** - Another comic downloaderCurrently, this script only works on Linux. There is a chance that the sample docker compose file will work on Windows,

- **Bazarr** - Subtitle automationalthough untested. The only requirements other than that are **Python 3**, the **Charm Gum** binary, and **docker** with **docker-compose-v2**.

While this script _may_ work on docker-compose-v1 it's made to be and highly recommended to be run using v2.

### 🎬 Media Servers & PortalsA prebuilt Gum binary for Linux x86_64 ships inside `bin/gum`, and `main.py` automatically prepends that directory to `PATH` so you can run the CLI without installing anything extra.

- **Plex** - Commercial media serverInstall Gum by following the instructions on [Charm’s releases page](https://github.com/charmbracelet/gum) or via `brew install gum`/`sudo pacman -S gum` if you need a different architecture or want a system-wide install.

- **Tautulli** - Plex monitoringThe easiest way to install these dependencies on Ubuntu and other Debian-based distors is by running:

- **Jellyfin** - Open-source media server```

- **Overseerr** - Request management for Plexsudo apt-get install python3 docker.io docker-compose-v2

- **Jellyseerr** - Request management for Jellyfin```

- **Jellystat** - Jellyfin analyticsFor other Linux distros you may have to use a different package manager or download directly from docker's website.

- **Wizarr** - One-click invitations

- **Audiobookshelf** - Audiobooks & podcasts### Updating Gum or using another OS

- **Homarr** - Dashboard for your stackIf you’re on Apple Silicon/macOS, ARM SBCs, or simply want to grab the latest Gum release, run the helper script to download the right binary and place it in `bin/gum` inside this repo:



### 🔍 Indexers & Bypass```bash

- **Prowlarr** - Indexer aggregatorscripts/install_gum.sh

- **Jackett** - Alternative indexer proxy```

- **Flaresolverr** - Cloudflare bypass

After it finishes, either add `bin/` to your PATH or launch the CLI with `PATH="bin:$PATH" python3 main.py`. Windows users can install Gum via winget/scoop or by unzipping the appropriate asset from the [releases](https://github.com/charmbracelet/gum/releases).

### ⬇️ Download Clients

- **qBittorrent** - Torrent client## Using

- **SABnzbd** - Usenet downloader### Using the CLI

To make things easier, a Gum-powered TUI has been developed. First, clone the repository in a directory of your

### 🤖 Automation & Optimizationchoosing. You can run it by entering `python3 main.py` and the CLI will guide you through a colorful

- **Tdarr** - Media transcodingquestion-and-answer flow:

- **Decluttarr** - Queue cleanup

- **Janitorr** - Library hygiene1. Select all the self-hosted apps you would like to deploy using arrow keys + space.

- **Profilarr** - Profile management2. Decide if you want Gluetun VPN support, pick a provider, and enter any keys.

3. Answer a few prompts about timezone, storage path, Plex claim tokens, Wizarr URLs, or Jellystat secrets.

### 🔧 Infrastructure & Utilities4. Confirm the summary screen and let the tool write `docker-compose.yml`.

- **Gluetun** - VPN container5. Optionally run the permissions/folder bootstrap (requires sudo).

- **Autobrr** - IRC/Tracker automation

- **Dozzle** - Docker log dashboardThis is the recommended method if you're setting this up for the first time on a new system.

Please take a look at [important notes](#important-notes) before you continue.

---**NOTE: This script will create users for each container with IDs ranging from 13001 to 13020.

If you want to choose your own IDs (or some of them are occupied) you have to go through the manual install.**

## 🏗️ Architecture

### Manually

```If you're installing this for the first time simply follow these steps.

boxlab-media-server-stack/If you're coming from an older version or reinstalling with different IDs, run `remove_old_users.sh` to clean up old users and then follow these steps.

├── boxlab              # 🚀 Main launcher (executable)1. To get started, clone the repository in a directory of your choosing. `git clone https://github.com/<your-user>/boxlab-media-server-stack.git`

├── main.py             # 🐍 Python entry point2. Copy `.env.sample` to a real `.env` by running `$ cp .env.sample .env`.

├── lib/                # 📚 Core modules3. Set the environment variables to your liking. Pay special attention `ROOT_DIR` as this is where everything is going to be stored in.

│   ├── catalog.py      #    Service definitions   The path in this value needs to be **absolute**. If you leave it empty it's going to install in the directory the .env file is currently in.

│   ├── cli.py          #    Workflow orchestration   `UID` should be set to the ID of the user that you want to run docker with. You can find this by running `id -u` from that user's shell.

│   ├── composer.py     #    Docker Compose generator4. Run `setup.sh` as superuser. This will set up your users, a system of directories and ensure permissions are set correctly.

│   ├── config.py       #    Configuration models5. Copy `docker-compose.yml.sample` to a real `docker-compose.yml` by running `$ cp docker-compose.yml.sample docker-compose.yml`.

│   ├── installer.py    #    Permission & user setup6. Take a look at the `docker-compose.yml` file. If there are services you would like to ignore

│   └── tui.py          #    Beautiful UI components   (for example, running PleX and Jellyfin at the same time is a bit unusual), you can comment them

├── bin/   out by placing `#` in front of the lines. This ensures they are ignored by Docker compose.

│   └── gum             # 🎨 Gum binary (Linux x86_64 included)   Double check that your .env file is set up properly. Also make sure to add a newly generated encryption key to the

├── scripts/   Homarr section, if you want to use it.

│   └── install_gum.sh  # 📥 Gum installer for other platforms7. Run `docker compose up -d` to start the containers. If it complains about permissions run the following commands to add your current user to the docker group and apply changes:

├── remove_old_users.sh # 🧹 Cleanup utility    ```

└── docker-compose.yml  # 📋 Generated (not in repo)    sudo groupadd docker

```    sudo usermod -aG docker $USER

    newgrp docker

### Generated Structure    ```

    If it still doesn't work reboot your system.

After running the installer:

Once the CLI finishes you can run `docker compose up -d` and continue configuring the web interfaces.

```For contributors who prefer the manual path, the classic instructions still work.

$ROOT_DIR/              # Your chosen installation directoryTake a look at [important notes](#important-notes) before you continue.

├── config/             # Service configurations

│   ├── sonarr-config/### Adding new applications to the TUI

│   ├── radarr-config/Applications are defined in `src/boxlab/catalog.py`. Add a new `Service` entry (with `key`, `name`, `category`, `description`,

│   └── ...and optional dependencies) plus matching compose/permission methods, and the Gum UI will automatically display it in the selection step.

└── data/               # Media and downloads

    ├── media/          # Organized libraries### Project layout

    │   ├── movies/- `main.py` – entrypoint that boots the Gum installer.

    │   ├── tv/- `src/boxlab/catalog.py` – declarative service catalog grouped by category.

    │   └── ...- `src/boxlab/ui.py` – Charm Gum helpers (select/input/confirm styling).

    └── torrents/       # Download directory- `src/boxlab/workflow.py` – orchestrated wizard logic.

```- `src/boxlab/compose.py` – docker-compose fragment builders per service.

- `src/boxlab/permissions.py` – optional filesystem/user bootstrap utilities.

---

### Gum compatibility & alternatives

## 💻 Installation- **Compatibility:** Gum is a standalone CLI written in Go; we execute it from Python via `subprocess.run`, so it works anywhere Gum’s binary works (Linux/macOS today, Windows via WSL/PowerShell). Because it’s not a Python package, it can also be scripted from Bash or any other runtime.

- **Binary layout:** For reproducibility we keep downloaded binaries under `bin/gum` (ignored by git). The CLI checks for `gum` on `PATH` first, so system-wide installs take precedence.

### For Linux x86_64- **Alternatives:** If you prefer a pure-Python solution, [Textual](https://github.com/Textualize/textual) or [prompt_toolkit/InquirerPy](https://github.com/kazhala/InquirerPy) can deliver rich TUIs without external binaries, while Bash-focused stacks sometimes rely on [whiptail/dialog] or [gum alternatives like Bubble Tea apps]. We chose Gum because it is trivial to script from both Bash and Python, ships with beautiful defaults, and keeps the installer logic language-agnostic.



The installer includes Gum automatically:## Important notes

- You probably shouldn't run the python script as root. Ideally you should create a brand new user that's just for these services, but any regular user will do.

```bash  It will need your password for `sudo` to set up the permissions and folder structures, but you shouldn't run it *as* root.

git clone https://github.com/mayur-chavhan/boxlab-media-server-stack.git- If you already used this script previously and want to clean up old users, run `remove_old_users.sh`.

cd boxlab-media-server-stack  This is also recommended if you are updating from an earlier version of this script, since there were previously some conflicts in user IDs.

./boxlab- It is recommended to restart your system after script completion, so that newly created users and groups can be loaded properly.

```- When linking one service to another, remember to use the container name instead of `localhost`.

- Please set the settings of the -arr containers as soon as possible to the following (use

### For macOS / ARM / Other Architectures  advanced):

  - Media management:

Install Gum first:    - Use hardlinks instead of Copy: `true`

    - Root folder: `/data/media/` and then tv, movies or music depending on service

```bash  - qBittorrent ships with a default username `admin` and a one-time password that can be viewed by running `docker logs qbittorrent`.

# macOS  - Make sure to set a username and password for all servarr services and qBittorrent!

brew install gum- In qBittorrent, after connecting it to the -arr services, you can indicate it should move

  torrents in certain categories to certain directories, like torrents in the `radarr` category

# Arch Linux  to `/data/torrents/movies`. You should do this. Also set the `Default Save Path` to

sudo pacman -S gum  `/data/torrents`. Set "Run external program on torrent completion" to true and enter this in the

  field: `chmod -R 775 "%F/"`.

# Or use the included installer- You'll have to add indexers in Prowlarr by hand. Use Prowlarrs settings to connect it to the

scripts/install_gum.sh  other -arr apps.

````

### IMPORTANT IF USING NFS SHARES

Then run the installer:- NFS shares' permissions are mapped by user IDs. If you want to access a file as a client, your user ID needs to match the user ID of the owner (or group) of that file on the NFS server.

Note that if you are a group member (and not the owner), having matching group IDs won't be enough, there also needs to be a corresponding user on the NFS server. The easiest way to make sure

```bashthe users and groups are set up on both sides correctly is to run `setup.sh` on both your NFS server and your client.

python3 main.pyOn your server:

```- Copy `.env`and`setup.sh` to your NFS server.

- You may have to adjust `.env` so that `ROOT_DIR` reflects where it will be stored on your server, which is most likely different from the mapped location on the client.

### Install Docker (if needed)- Make sure that the `.env` file is not a .sample. Run `setup.sh`.

- Now follow all the same steps but on your client machine. Always double-check that `.env` is set correctly, especially `ROOT_DIR`.

**Ubuntu/Debian:**You don't have to do this on your server first but it's recommended. If you are running this script on the client **make sure that you temporarily enable -no-root-squash on your NFS server**,

````bashas the script needs superuser privileges to run and by default on NFS the root user is mapped to nowhere to prevent abuse.

sudo apt-get update

sudo apt-get install docker.io docker-compose-v2### SABnzbd External internet access denied message

sudo usermod -aG docker $USERWhen you're trying to access SABnzbd the first time you'll come across the message `External

```internet access denied`. To fix this simple modify the `sabnzbd.ini` and change `inet_exposure` to

`4`, restart the docker container for sabnzbd (`docker restart sabnzbd`) and now you can access the

**Other distros:** See [Docker's official docs](https://docs.docker.com/engine/install/)UI of SABnzbd (note: you may get a `Access denied - Hostname verification failed`, to fix this,

simply go to the IP of your server directly instead of the hostname). After accessing the UI don't

---forget to set a username and password (https://sabnzbd.org/wiki/configuration/3.7/general,

section Security).

## 🚀 Usage

For more instructions or help see also https://sabnzbd.org/wiki/extra/access-denied.html on the

### Interactive Installerofficial SABnzbd website.



Launch the beautiful TUI:## FAQ



```bash### How to update containers

./boxlabThere is an `update_containers.sh` script that takes care of this. Simply run it and it updates

# orall containers and removes old images. If you want to keep them, simply comment out the last line of the script.

python3 main.pyIt's essentially the following steps but automated:

```If you'd like to it manually, go to the directory of your `docker-compose.yml` file

and run `(sudo) docker compose pull`. This pulls the newest versions of all images (blueprints for

Follow the prompts to:containers) listed in the `docker-compose.yml` file. Then, you can run `(sudo) docker compose up

1. Select applications-d`. This will deploy the new versions without losing uptime. Afterwards, you can run `(sudo)

2. Configure VPN (optional)docker image prune` to remove the old images, freeing up space.

3. Set timezone and storage path

4. Configure service-specific settings### Why do I need to set some settings myself, can that be added?

5. Generate docker-compose.ymlSome settings, particularly for the Servarr suite, are set in databases. While it *might* be

6. Set up permissions (requires sudo)possible to interact with this database after creation, I'd rather not touch these. It's not

that difficult to set them yourself, and quite difficult to do it automatically. For other

### Deploy Your Stackcontainers, configuration files are automatically generated, so these are more easily edited,

but I currently don't believe this is worth the effort.

After generation:

On top of the above, connecting the containers above would mean setting a password and creating an

```bashAPI key for all of them. This would lead to everyone using BoxLab (or upstream Ezarr) having the same API key

# Review the generated compose fileand user/password combination. Personally, I'd rather trust users to figure this out on their own rather

cat docker-compose.ymlthan trusting them to change these passwords and keys.


# Start all services
docker compose up -d

# Check logs
docker compose logs -f

# Stop all services
docker compose down
````

### Update Services

```bash
# Pull latest images
docker compose pull

# Restart with updates
docker compose up -d

# Clean up old images
docker image prune -f
```

---

## 🔧 Advanced Configuration

### VPN Configuration

The installer supports multiple VPN providers:

- **Mullvad** (recommended for privacy)
- **Proton VPN**
- **NordVPN**
- **IVPN**
- **Custom/Other**

During setup, you'll configure:

- WireGuard private key
- IP addresses
- Server locations
- MTU settings

> **Note:** To route specific services through VPN, you'll need to manually edit `docker-compose.yml` and add `network_mode: "service:gluetun"` to those services.

### User IDs

The installer creates system users with fixed UIDs:

- `mediacenter` group: GID 13000
- Service users: UIDs 13001-13020

If these IDs conflict with existing users, run `./remove_old_users.sh` first.

### Custom Root Directory

Default: `~/boxlab`

You can specify any absolute path during installation. For best performance, use a filesystem that supports hardlinks (ext4, xfs, etc.).

---

## 📚 Documentation

- **TRaSH Guides:** https://trash-guides.info/
- **Docker Compose:** https://docs.docker.com/compose/
- **Gluetun VPN:** https://github.com/qdm12/gluetun
- **Servarr Wiki:** https://wiki.servarr.com/

---

## 🤝 Contributing

Want to add a new service? It's easy!

1. **Add to catalog** (`lib/catalog.py`):

   ```python
   Service("newapp", "NewApp", "category", "Description")
   ```

2. **Add compose method** (`lib/composer.py`):

   ```python
   def newapp(self):
       return '''
         newapp:
           image: lscr.io/linuxserver/newapp:latest
           ...
       '''
   ```

3. **Add permissions** (`lib/installer.py`):

   ```python
   def newapp(self):
       os.system('sudo useradd newapp -u 13021')
       self.create_config_dir('newapp')
   ```

4. Test and submit a PR!

---

## ⚠️ Important Notes

### Linux Only

This tool requires Linux for user/group management. While the generated `docker-compose.yml` may work on other platforms, the installer itself needs Linux.

### Hardlinks

Keep all media and downloads on the **same filesystem** to preserve hardlinks. This is crucial for:

- Saving disk space
- Instant "moves" from downloads to media folders
- Seeding torrents without duplicating files

### NFS Shares

If using NFS:

- Match UID/GID on all hosts
- Use `no_root_squash` option
- Test permissions before deploying

### Security

- Never commit API keys or secrets
- Use strong passwords for Jellystat
- Configure reverse proxy for external access
- Keep Docker and images updated

---

## 🐛 Troubleshooting

### "Gum not installed"

```bash
# Run the installer
scripts/install_gum.sh

# Or install manually
brew install gum  # macOS
sudo pacman -S gum  # Arch
```

### "Permission denied"

```bash
# Ensure user is in docker group
sudo usermod -aG docker $USER

# Log out and back in, or:
newgrp docker
```

### "Port already in use"

```bash
# Find conflicting service
sudo lsof -i :8989  # Example for Sonarr

# Stop conflicting service or edit docker-compose.yml ports
```

### User/Group Conflicts

```bash
# Clean up old users
./remove_old_users.sh

# Re-run installer
./boxlab
```

---

## 📄 License

MIT License - see [LICENSE.md](LICENSE.md)

---

## 🙏 Acknowledgments

- Forked from the excellent [Ezarr](https://github.com/Luctia/ezarr) project
- Built with [Charm's Gum](https://github.com/charmbracelet/gum)
- Follows [TRaSH Guides](https://trash-guides.info/)
- Uses [LinuxServer.io](https://www.linuxserver.io/) Docker images

---

## 📞 Support

- 🐛 **Issues:** [GitHub Issues](https://github.com/mayur-chavhan/boxlab-media-server-stack/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/mayur-chavhan/boxlab-media-server-stack/discussions)
- 📖 **Wiki:** [Project Wiki](https://github.com/mayur-chavhan/boxlab-media-server-stack/wiki)

---

<div align="center">

**[⭐ Star this repo](https://github.com/mayur-chavhan/boxlab-media-server-stack)** if you find it useful!

Made with ❤️ by the BoxLab community

</div>
