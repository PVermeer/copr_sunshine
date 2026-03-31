#! /bin/bash

# Dev
sudo dnf install -y cmake ninja-build gcc g++ mesa-libgbm-devel libappindicator-gtk3-devel openssl-devel libcurl-devel miniupnpc-devel libdrm-devel libva-devel libnotify-devel nodejs npm libevdev-devel opus-devel pulseaudio-libs-devel numactl-devel libcap-devel pipewire-devel micromamba vulkan-devel glslc

# External dev
mamba create -y -p .mamba/cuda-env conda-forge::cuda-nvcc
