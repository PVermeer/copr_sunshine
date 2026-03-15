#! /bin/bash

# Dev
sudo dnf install -y cmake ninja-build gcc g++ conda mesa-libgbm-devel libappindicator-gtk3-devel openssl-devel libcurl-devel miniupnpc-devel libdrm-devel libva-devel libnotify-devel nodejs npm libevdev-devel opus-devel pulseaudio-libs-devel numactl-devel libcap-devel

# Cuda via conda
(
    echo -e "\n==== Init"
    conda init || true
    # shellcheck disable=SC1090
    source ~/.bashrc
    echo -e "\n==== Create env"
    conda create -y --name cuda
    echo -e "\n==== Activate"
    conda activate cuda
    echo -e "\n==== Install nvcc"
    conda install -y cuda-nvcc
    echo -e "\n==== Deactivate"
    conda deactivate
    conda init --reverse || true
)

# Runtime
sudo dnf install -y libappindicator-gtk3
