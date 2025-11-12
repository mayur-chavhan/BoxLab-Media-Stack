import os
import secrets
from container_configs import ContainerConfig
from users_groups_setup import UserGroupSetup

services_classed = dict()


def take_boolean_input(default=True):
    while True:
        ans = input()
        if ans == '':
            return default
        if ans == 'y' or ans == 'Y':
            return True
        if ans == 'n' or ans == 'N':
            return False
        print('Please answer with y or n.', end=' ')

def take_input(service_name, service_type, default=True):
    choice = take_boolean_input(default=default)
    if choice:
        services_classed[service_type].append(service_name)
    else:
        print('Not adding ' + service_name + ".")

def take_directory_input():
    while True:
        ans = input()
        if ans[0] == '/':
            if ans[-1] == '/':
                return ans[:-1]
            return ans
        print('Please make sure the path is absolute, meaning it starts at the root of your filesystem and starts with "/":', end=' ')

def get_system_timezone():
    tz_path = "/etc/localtime"

    if os.path.exists(tz_path):
        if os.path.islink(tz_path):
            tz = os.readlink(tz_path)
            return tz.split('zoneinfo/')[-1]
    return None

print('Welcome to the BoxLab Media Server Stack CLI.')
print('This CLI will ask you which services you\'d like to use and more. If you\'d like more information about a '
      'certain service, look in the README.')

print('\n===SERVARR===')
services_classed['servarr'] = []
print('Use Sonarr? [Y/n]', end=" ")
take_input('sonarr', 'servarr')
print('Use Radarr? [Y/n]', end=" ")
take_input('radarr', 'servarr')
print('Use Lidarr? [Y/n]', end=" ")
take_input('lidarr', 'servarr')
print('Use Readarr? [Y/n]', end=" ")
take_input('readarr', 'servarr')
print('Use Mylar3? [Y/n]', end=" ")
take_input('mylar3', 'servarr')
print('Use Kapowarr? [Y/n]', end=" ")
take_input('kapowarr', 'servarr')
print('Use Audiobookshelf? [Y/n]', end=" ")
take_input('audiobookshelf', 'servarr')
print('Use Homarr? [Y/n]', end=" ")
take_input('homarr', 'servarr')
if len(services_classed['servarr']) == 0:
    print('Warning: no media management services selected.')
if services_classed['servarr'].__contains__('sonarr') or services_classed['servarr'].__contains__('radarr'):
    print('Use Bazarr? [Y/n]', end=" ")
    take_input('bazarr', 'servarr')

print('\n===INDEXERS===')
services_classed['indexer'] = []
print('Use Prowlarr? [Y/n]', end=" ")
take_input('prowlarr', 'indexer')
print('Use Jackett? [Y/n]', end=" ")
take_input('jackett', 'indexer')
if len(services_classed['indexer']) == 0:
    print('Warning: no indexing service selected.')

print('\n===CLOUDFLARE BYPASS===')
services_classed['bypass'] = []
print('Use Flaresolverr? [Y/n]', end=" ")
take_input('flaresolverr', 'bypass')

print('\n===MEDIA SERVERS===')
services_classed['ms'] = []
print('Use PleX? [Y/n]', end=" ")
take_input('plex', 'ms')
if services_classed['ms'].__contains__('plex'):
    print('Use Tautulli? [Y/n]', end=" ")
    take_input('tautulli', 'ms')
    if services_classed['servarr'].__contains__('sonarr') or services_classed['servarr'].__contains__('radarr'):
        print('Use Overseerr? [Y/n]', end=" ")
        take_input('overseerr', 'servarr')
print('Use Jellyfin? [Y/n]', end=" ")
take_input('jellyfin', 'ms')
if (services_classed['ms'].__contains__('jellyfin')
        and (services_classed['servarr'].__contains__('sonarr') or services_classed['servarr'].__contains__('radarr'))):
    print('Use Jellyseerr? [Y/n]', end=" ")
    take_input('jellyseerr', 'servarr')
if len(services_classed['ms']) == 0:
    print('Warning: no media servers selected.')

print('\n===BITTORRENT===')
services_classed['torrent'] = []
print('Use qBittorrent? [Y/n]', end=" ")
take_input('qbittorrent', 'torrent')

print('\n===USENET===')
services_classed['usenet'] = []
print('Use SABnzbd? [Y/n]', end=" ")
take_input('sabnzbd', 'usenet')

if len(services_classed['torrent']) == 0 and len(services_classed['usenet']) == 0:
    print('Warning: no usenet or BitTorrent clients selected.')

print('\n===AUTOMATION & OPTIMIZATION===')
services_classed['automation'] = []
print('Use Tdarr? [Y/n]', end=" ")
take_input('tdarr', 'automation')
print('Use Decluttarr? [Y/n]', end=" ")
take_input('decluttarr', 'automation')
print('Use Janitorr? [Y/n]', end=" ")
take_input('janitorr', 'automation')
print('Use Profilarr? [Y/n]', end=" ")
take_input('profilarr', 'automation')

print('\n===INFRASTRUCTURE & PORTALS===')
services_classed['infra'] = []
print('Use Gluetun? (Provides VPN networking) [y/N]', end=" ")
take_input('gluetun', 'infra', default=False)
print('Use Autobrr? [Y/n]', end=" ")
take_input('autobrr', 'infra')
print('Use Wizarr? [Y/n]', end=" ")
take_input('wizarr', 'infra')
print('Use Dozzle for log viewing? [Y/n]', end=" ")
take_input('dozzle', 'infra')
print('Use Jellystat? [Y/n]', end=" ")
take_input('jellystat', 'infra')

services = []
for service_class in services_classed.keys():
    services.extend(services_classed[service_class])
if len(services) == 0:
    print('No services selected. Terminating.')
    exit(1)

print('\n===CONFIGURATION===')

print('Please enter your timezone (like "Europe/Amsterdam") or press enter to use your system\'s configured timezone:', end=' ')
timezone = input()
if timezone == '':
    timezone = get_system_timezone()

if len(timezone) == 0: # if user pressed enter and reading timezone from /etc/localtime failed then default to Amsterdam
    timezone = 'Europe/Amsterdam'

plex_claim = ''
if services.__contains__('plex'):
    print('If you have a PleX claim token, enter it now. Otherwise, just press enter.', end=' ')
    plex_claim = input()

print('Where would you like to keep your files?', end=' ')
root_dir = take_directory_input()

gluetun_settings = None
if services.__contains__('gluetun'):
    print('\nEnter VPN service provider for Gluetun (default: mullvad):', end=' ')
    provider = input().strip() or 'mullvad'
    print('Enter VPN type (default: wireguard):', end=' ')
    vpn_type = input().strip() or 'wireguard'
    print('Enter Wireguard private key (leave empty to fill in the compose file later):', end=' ')
    wireguard_private_key = input().strip()
    print('Enter Wireguard addresses (default: 10.64.0.2/32,4.0.0.2/32):', end=' ')
    addresses = input().strip() or '10.64.0.2/32,4.0.0.2/32'
    print('Enter preferred server cities (comma separated, optional):', end=' ')
    server_cities = input().strip()
    print('Enter Wireguard MTU (default: 1280):', end=' ')
    mtu = input().strip() or '1280'
    print('Enter Public IP API endpoint (optional):', end=' ')
    public_ip_api = input().strip()
    print('Enter Public IP API token (optional):', end=' ')
    public_ip_token = input().strip()
    gluetun_settings = {
        'VPN_SERVICE_PROVIDER': provider,
        'VPN_TYPE': vpn_type,
        'WIREGUARD_PRIVATE_KEY': wireguard_private_key,
        'WIREGUARD_ADDRESSES': addresses,
        'SERVER_CITIES': server_cities,
        'WIREGUARD_MTU': mtu,
        'PUBLICIP_API': public_ip_api,
        'PUBLICIP_API_TOKEN': public_ip_token
    }

wizarr_settings = None
if services.__contains__('wizarr'):
    print('\nEnter the external URL for Wizarr (e.g. https://wizarr.example.com). Leave empty to fill in later:', end=' ')
    app_url = input().strip()
    print('Disable Wizarr built-in authentication? [y/N]', end=' ')
    disable_auth = take_boolean_input(False)
    wizarr_settings = {
        'APP_URL': app_url,
        'DISABLE_BUILTIN_AUTH': 'true' if disable_auth else 'false'
    }

jellystat_settings = None
if services.__contains__('jellystat'):
    print('\nJellystat database username [jfstat]:', end=' ')
    db_user = input().strip() or 'jfstat'
    print('Jellystat database name [jfstat]:', end=' ')
    db_name = input().strip() or 'jfstat'
    print('Jellystat database password (leave empty to auto-generate):', end=' ')
    db_password = input().strip()
    if db_password == '':
        db_password = secrets.token_hex(16)
        print('Generated password for Jellystat database: ' + db_password)
    print('Jellystat JWT secret (leave empty to auto-generate):', end=' ')
    jwt_secret = input().strip()
    if jwt_secret == '':
        jwt_secret = secrets.token_hex(32)
        print('Generated JWT secret for Jellystat.')
    jellystat_settings = {
        'db_user': db_user,
        'db_name': db_name,
        'db_password': db_password,
        'jwt_secret': jwt_secret
    }

compose = open('docker-compose.yml', 'w')
compose.write(
    '---\n'
    'services:\n'
)

container_config = ContainerConfig(
    root_dir,
    timezone,
    plex_claim=plex_claim,
    gluetun_settings=gluetun_settings,
    wizarr_settings=wizarr_settings,
    jellystat_settings=jellystat_settings
)

for service in services:
    compose.write(getattr(container_config, service)())
compose.close()
print("Docker compose file generated successfully.")

print("Do you want to also generate the required folder structure and permissions? (this is required for first time setup) [Y/n]: ")
generate_permissions = take_boolean_input()
if generate_permissions:
    permission_setup = UserGroupSetup(root_dir=root_dir)
    for service in services:
        try:
            getattr(permission_setup, service)()
        except AttributeError:
            pass
else:
    print("Permission and folder structure generation skipped by user.")


print('Process complete. You can now run "docker compose up -d" to start your containers.')
print('Thank you for using the BoxLab Media Server Stack. If you experience any issues or have feature requests, add them to our issues.')
print('For questions, you can also use the discussions tab.')
exit(0)
