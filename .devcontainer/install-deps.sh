#! /bin/bash

# Dev
sudo dnf install -y cmake ninja-build gcc g++ micromamba mesa-libgbm-devel openssl-devel libcurl-devel miniupnpc-devel libdrm-devel libva-devel nodejs npm libevdev-devel opus-devel pulseaudio-libs-devel numactl-devel libcap-devel pipewire-devel vulkan-devel glslc qt6-qtbase-devel qt6-qtsvg-devel libXfixes-devel libXrandr-devel python3-jinja2 python3-setuptools uv boost-devel

# External dev
mamba create -y -p .mamba/cuda-env conda-forge::cuda-nvcc
