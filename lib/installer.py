"""
System installer and permission setup for BoxLab services.
Creates users, groups, and directory structures with proper permissions.
"""
import os


class PermissionSetup:
    """Handles filesystem permissions and user/group management."""
    
    def __init__(self, root_dir='/'):
        self.root_dir = root_dir
        self.local_user = os.popen('id -un').read().rstrip('\n')
        # Create base mediacenter group and directories
        os.system('sudo groupadd mediacenter -g 13000 2>/dev/null || true')
        os.system('sudo usermod -a -G mediacenter $USER')
        os.system(
            f'/bin/bash -c "sudo mkdir -pv {self.root_dir}/data/{{media,usenet,torrents}} -m 775'
            f' ; sudo chown $(id -u):mediacenter {self.root_dir}/data'
            f' ; sudo chown $(id -u):mediacenter {self.root_dir}/data/{{media,usenet,torrents}}"'
        )

    def create_config_dir(self, service_name, owner=None):
        """Create a service-specific config directory with proper ownership."""
        owner_name = owner or service_name
        os.system(
            f'/bin/bash -c "sudo mkdir -p {self.root_dir}/config/{service_name}-config -m 775'
            f' ; sudo chown -R {owner_name}:mediacenter {self.root_dir}/config/{service_name}-config'
            f' ; sudo chown $(id -u):mediacenter {self.root_dir}/config"'
        )

    def sonarr(self):
        os.system(
            f'/bin/bash -c "sudo useradd sonarr -u 13001 2>/dev/null || true'
            f' ; sudo mkdir -pv {self.root_dir}/data/{{media,usenet,torrents}}/tv -m 775'
            f' ; sudo chown -R sonarr:mediacenter {self.root_dir}/data/{{media,usenet,torrents}}/tv"'
        )
        self.create_config_dir('sonarr')
        os.system('sudo usermod -a -G mediacenter sonarr')

    def radarr(self):
        os.system(
            f'/bin/bash -c "sudo useradd radarr -u 13002 2>/dev/null || true'
            f' ; sudo mkdir -pv {self.root_dir}/data/{{media,usenet,torrents}}/movies -m 775'
            f' ; sudo chown -R radarr:mediacenter {self.root_dir}/data/{{media,usenet,torrents}}/movies"'
        )
        self.create_config_dir('radarr')
        os.system('sudo usermod -a -G mediacenter radarr')

    def bazarr(self):
        os.system('sudo useradd bazarr -u 13013 2>/dev/null || true')
        self.create_config_dir('bazarr')
        os.system('sudo usermod -a -G mediacenter bazarr')

    def lidarr(self):
        os.system(
            f'/bin/bash -c "sudo useradd lidarr -u 13003 2>/dev/null || true'
            f' ; sudo mkdir -pv {self.root_dir}/data/{{media,usenet,torrents}}/music -m 775'
            f' ; sudo chown -R lidarr:mediacenter {self.root_dir}/data/{{media,usenet,torrents}}/music"'
        )
        self.create_config_dir('lidarr')
        os.system('sudo usermod -a -G mediacenter lidarr')

    def readarr(self):
        os.system(
            f'/bin/bash -c "sudo useradd readarr -u 13004 2>/dev/null || true'
            f' ; sudo mkdir -pv {self.root_dir}/data/{{media,usenet,torrents}}/books -m 775'
            f' ; sudo chown -R readarr:mediacenter {self.root_dir}/data/{{media,usenet,torrents}}/books"'
        )
        self.create_config_dir('readarr')
        os.system('sudo usermod -a -G mediacenter readarr')

    def mylar3(self):
        os.system(
            f'/bin/bash -c "sudo useradd mylar -u 13005 2>/dev/null || true'
            f' ; sudo mkdir -pv {self.root_dir}/data/{{media,usenet,torrents}}/comics -m 775'
            f' ; sudo chown -R mylar:mediacenter {self.root_dir}/data/{{media,usenet,torrents}}/comics"'
        )
        self.create_config_dir('mylar')
        os.system('sudo usermod -a -G mediacenter mylar')

    def audiobookshelf(self):
        os.system(
            f'/bin/bash -c "sudo useradd audiobookshelf -u 13014 2>/dev/null || true'
            f' ; sudo mkdir -pv {self.root_dir}/data/media/{{audiobooks,podcasts,audiobookshelf-metadata}} -m 775'
            f' ; sudo chown -R audiobookshelf:mediacenter {self.root_dir}/data/media/{{audiobooks,podcasts,audiobookshelf-metadata}}"'
        )
        self.create_config_dir('audiobookshelf')
        os.system('sudo usermod -a -G mediacenter audiobookshelf')

    def prowlarr(self):
        os.system('sudo useradd prowlarr -u 13006 2>/dev/null || true')
        self.create_config_dir('prowlarr')
        os.system('sudo usermod -a -G mediacenter prowlarr')

    def qbittorrent(self):
        os.system('sudo useradd qbittorrent -u 13007 2>/dev/null || true')
        os.system('sudo usermod -a -G mediacenter qbittorrent')

    def overseerr(self):
        os.system('sudo useradd overseerr -u 13009 2>/dev/null || true')
        self.create_config_dir('overseerr')
        os.system('sudo usermod -a -G mediacenter overseerr')

    def plex(self):
        os.system('sudo useradd plex -u 13010 2>/dev/null || true')
        self.create_config_dir('plex')
        os.system('sudo usermod -a -G mediacenter plex')

    def sabnzbd(self):
        os.system('sudo useradd sabnzbd -u 13011 2>/dev/null || true')
        self.create_config_dir('sabnzbd')
        os.system('sudo usermod -a -G mediacenter sabnzbd')

    def jellyseerr(self):
        os.system('sudo useradd jellyseerr -u 13012 2>/dev/null || true')
        self.create_config_dir('jellyseerr')
        os.system('sudo usermod -a -G mediacenter jellyseerr')
    
    def jackett(self):
        os.system('sudo useradd jackett -u 13008 2>/dev/null || true')
        self.create_config_dir('jackett')
        os.system('sudo usermod -a -G mediacenter jackett')

    def kapowarr(self):
        os.system(
            f'/bin/bash -c "sudo useradd kapowarr -u 13015 2>/dev/null || true'
            f' ; sudo mkdir -pv {self.root_dir}/data/temp_downloads -m 775'
            f' ; sudo chown -R kapowarr:mediacenter {self.root_dir}/data/temp_downloads"'
        )
        self.create_config_dir('kapowarr')
        os.system('sudo usermod -a -G mediacenter kapowarr')

    def autobrr(self):
        os.system('sudo useradd autobrr -u 13016 2>/dev/null || true')
        self.create_config_dir('autobrr')
        os.system('sudo usermod -a -G mediacenter autobrr')

    def tdarr(self):
        os.system(
            f'/bin/bash -c "sudo useradd tdarr -u 13017 2>/dev/null || true'
            f' ; sudo mkdir -pv {self.root_dir}/config/tdarr/{{server,configs,logs}} -m 775'
            f' ; sudo mkdir -pv {self.root_dir}/data/transcode -m 775'
            f' ; sudo chown -R tdarr:mediacenter {self.root_dir}/config/tdarr'
            f' ; sudo chown -R tdarr:mediacenter {self.root_dir}/data/transcode'
            f' ; sudo chown $(id -u):mediacenter {self.root_dir}/config"'
        )
        os.system('sudo usermod -a -G mediacenter tdarr')

    def wizarr(self):
        os.system(
            f'/bin/bash -c "sudo useradd wizarr -u 13018 2>/dev/null || true'
            f' ; sudo mkdir -pv {self.root_dir}/data/wizarr-cache -m 775'
            f' ; sudo chown -R wizarr:mediacenter {self.root_dir}/data/wizarr-cache"'
        )
        self.create_config_dir('wizarr')
        os.system('sudo usermod -a -G mediacenter wizarr')

    def decluttarr(self):
        os.system('sudo useradd decluttarr -u 13019 2>/dev/null || true')
        self.create_config_dir('decluttarr')
        os.system('sudo usermod -a -G mediacenter decluttarr')

    def janitorr(self):
        os.system(
            f'/bin/bash -c "sudo useradd janitorr -u 13020 2>/dev/null || true'
            f' ; sudo mkdir -pv {self.root_dir}/data/janitorr/logs -m 775'
            f' ; sudo chown -R janitorr:mediacenter {self.root_dir}/data/janitorr"'
        )
        self.create_config_dir('janitorr')
        os.system('sudo usermod -a -G mediacenter janitorr')

    def profilarr(self):
        os.system(
            f'/bin/bash -c "sudo mkdir -pv {self.root_dir}/config/profilarr-config -m 775'
            f' ; sudo chown -R {self.local_user}:mediacenter {self.root_dir}/config/profilarr-config'
            f' ; sudo chown $(id -u):mediacenter {self.root_dir}/config"'
        )

    def jellystat(self):
        os.system(
            f'/bin/bash -c "sudo mkdir -pv {self.root_dir}/data/jellystat/{{postgres-data,postgres-backup}} -m 775'
            f' ; sudo chown -R {self.local_user}:mediacenter {self.root_dir}/data/jellystat"'
        )

    # Services that don't require specific setup
    def jellyfin(self):
        pass
    
    def tautulli(self):
        pass
    
    def homarr(self):
        pass
    
    def flaresolverr(self):
        pass
    
    def gluetun(self):
        pass
    
    def dozzle(self):
        pass
