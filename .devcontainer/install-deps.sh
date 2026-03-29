#! /bin/bash

# Dev
sudo dnf install -y cmake ninja-build gcc g++ mesa-libgbm-devel libappindicator-gtk3-devel openssl-devel libcurl-devel miniupnpc-devel libdrm-devel libva-devel libnotify-devel nodejs npm libevdev-devel opus-devel pulseaudio-libs-devel numactl-devel libcap-devel pipewire-devel mamba

# External dev
mamba create -y -p .mamba/cuda-env cuda-nvcc

# Runtime
sudo dnf install -y libappindicator-gtk3
