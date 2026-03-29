#! /bin/bash

# Dev
sudo dnf install -y cmake ninja-build gcc g++ mesa-libgbm-devel libappindicator-gtk3-devel openssl-devel libcurl-devel miniupnpc-devel libdrm-devel libva-devel libnotify-devel nodejs npm libevdev-devel opus-devel pulseaudio-libs-devel numactl-devel libcap-devel pipewire-devel

# External dev
curl -L --fail --retry 5 --retry-delay 2 \
  -o /tmp/micromamba.tar.bz2 \
  https://github.com/mamba-org/micromamba-releases/releases/latest/download/micromamba-linux-64.tar.bz2
tar -xjf /tmp/micromamba.tar.bz2 -C /tmp
install -Dm755 /tmp/bin/micromamba ~/.local/bin/micromamba
micromamba create -y -p .micromamba/cuda-env cuda-nvcc

# Runtime
sudo dnf install -y libappindicator-gtk3
