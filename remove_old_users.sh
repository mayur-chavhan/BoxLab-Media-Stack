#!/bin/bash

# shut down all BoxLab Media Server Stack containers referenced by docker-compose.yml 
# If you previously had the stack installed somewhere else you have to do this manually in the directory where the docker-compose file is.
sudo docker compose down

# Remove old users and group
sudo userdel sonarr
sudo userdel radarr
sudo userdel lidarr
sudo userdel readarr
sudo userdel mylar
sudo userdel audiobookshelf
sudo userdel bazarr
sudo userdel prowlarr
sudo userdel jackett
sudo userdel plex
sudo userdel overseerr
sudo userdel jellyseerr
sudo userdel qbittorrent
sudo userdel sabnzbd
sudo userdel kapowarr
sudo userdel autobrr
sudo userdel tdarr
sudo userdel wizarr
sudo userdel decluttarr
sudo userdel janitorr
sudo groupdel mediacenter
