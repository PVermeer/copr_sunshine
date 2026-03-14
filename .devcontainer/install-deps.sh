#! /bin/bash

# shellcheck disable=SC1091
source /etc/os-release
fedora_version=$VERSION_ID

sudo dnf config-manager addrepo --overwrite -y --from-repofile=https://developer.download.nvidia.com/compute/cuda/repos/fedora"${fedora_version}"/"$(uname -m)"/cuda-fedora"${fedora_version}".repo

# Dev
sudo dnf install -y cmake ninja-build mesa-libgbm-devel cuda-toolkit libappindicator-gtk3-devel openssl-devel libcurl-devel miniupnpc-devel libdrm-devel libva-devel libnotify-devel nodejs npm libevdev-devel opus-devel pulseaudio-libs-devel numactl-devel

# Runtime
sudo dnf install -y libappindicator-gtk3
