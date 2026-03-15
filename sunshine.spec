# Create an option to build locally without fetchting own repo
# for sourcing and patching
%bcond local 0
 # Cannot compile CUDA with rpm hardening
%undefine _hardened_build

# Source repo
%global author LizardByte
%global source Sunshine
%global sourcerepo https://github.com/LizardByte/Sunshine
%global branch master
%global commit 86188d47a7463b0f73b35de18a628353adeaa20e
%global versioncommit %(echo -n %{commit} | head -c 8)

# Own copr repo
%global coprrepo https://github.com/PVermeer/copr_sunshine
%global coprsource copr_sunshine

Name: sunshine
Version: 2025.924.154138
Release: 1.%{versioncommit}%{?dist}
License: GPL-3.0 license
Summary: Stable build of sunshine.
Url: %{coprrepo}

BuildRequires: git
BuildRequires: cmake
BuildRequires: ninja-build
BuildRequires: conda
BuildRequires: gcc
BuildRequires: g++
BuildRequires: mesa-libgbm-devel
BuildRequires: libappindicator-gtk3-devel
BuildRequires: openssl-devel
BuildRequires: libcurl-devel
BuildRequires: miniupnpc-devel
BuildRequires: libdrm-devel
BuildRequires: libva-devel
BuildRequires: libnotify-devel
BuildRequires: nodejs
BuildRequires: npm
BuildRequires: libevdev-devel
BuildRequires: opus-devel
BuildRequires: pulseaudio-libs-devel
BuildRequires: numactl-devel
BuildRequires: libcap-devel

Requires: libappindicator-gtk3
Requires: openssl
Requires: libcurl
Requires: miniupnpc
Requires: libdrm
Requires: libva
Requires: libnotify
Requires: libevdev
Requires: opus
Requires: numactl

%description
Stable build of sunshine.

%define workdir %{_builddir}/%{name}
%define coprdir %{workdir}/%{coprsource}
%define sourcedir %{workdir}/%{source}

%prep
# To apply working changes handle sources / patches locally
# COPR should clone the commited changes
%if %{with local}
  # Get sources / patches - local build
  mkdir -p %{coprdir}
  cp -r %{_topdir}/SOURCES/* %{coprdir}

  # Get source repo - local build
  mkdir -p %{sourcedir}
  cp -r %{_topdir}/SOURCES/Sunshine/. %{sourcedir}
  cd %{sourcedir}
  rm -rf .git
  cd %{workdir}
%else
  # Get sources / patches - COPR build
  git clone --depth 1 %{coprrepo} %{coprdir}
  cd %{coprdir}
  rm -rf .git
  cd %{workdir}

  # Get source repo
  git clone %{sourcerepo} %{sourcedir}
  cd %{sourcedir}
  git reset --hard %{commit}
  git submodule update --recursive --init --depth 1
  rm -rf .git
  cd %{workdir}
%endif

# Install cuda compiler (nvcc)
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

%build
cd %{sourcedir}

export RPM_ARCH=%{_arch}

export CUDA_HOME=/usr/local/cuda
export LIBRARY_PATH=$CUDA_HOME/lib64:$LIBRARY_PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH

export BRANCH=stable
export BUILD_VERSION=%{version}
export COMMIT=%{commit}

cmake_args=(
  "-B=build"
  "-G=Ninja"
  "-S=."
  "-DBUILD_DOCS=OFF"
  "-DBUILD_WERROR=OFF"
  "-DCMAKE_BUILD_TYPE=Release"
  "-DSUNSHINE_ENABLE_DRM=ON"
  "-DSUNSHINE_ENABLE_PORTAL=ON"
  "-DSUNSHINE_ENABLE_WAYLAND=ON"
  "-DSUNSHINE_ENABLE_X11=ON"
  "-DSUNSHINE_PUBLISHER_NAME=LizardByte"
  "-DSUNSHINE_PUBLISHER_WEBSITE=https://app.lizardbyte.dev"
  "-DSUNSHINE_PUBLISHER_ISSUE_URL=https://app.lizardbyte.dev/support"
  "-DSUNSHINE_ENABLE_CUDA=ON"
  "-DCMAKE_CUDA_COMPILER:PATH=~/.conda/envs/cuda/bin/nvcc"
)
cmake "${cmake_args[@]}"
ninja -C "build"

cd %{workdir}

%check

%install
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_userunitdir}
mkdir -p %{buildroot}%{_udevrulesdir}
mkdir -p %{buildroot}%{_modulesloaddir}
mkdir -p %{buildroot}%{_datadir}/applications
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/scalable/apps
mkdir -p %{buildroot}%{_datadir}/metainfo
mkdir -p %{buildroot}%{_datadir}/sunshine

install -m 0755 $(readlink -f %{sourcedir}/build/sunshine) %{buildroot}%{_bindir}/sunshine
install -m 0644 %{sourcedir}/build/sunshine.service %{buildroot}%{_userunitdir}
install -m 0644 %{sourcedir}/src_assets/linux/misc/*-sunshine.rules %{buildroot}%{_udevrulesdir}
install -m 0644 %{sourcedir}/src_assets/linux/misc/*-sunshine.conf %{buildroot}%{_modulesloaddir}
install -m 0644 %{sourcedir}/build/*.desktop %{buildroot}%{_datadir}/applications
install -m 0644 %{sourcedir}/sunshine.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/sunshine.svg
install -m 0644 %{sourcedir}/build/*.metainfo.xml %{buildroot}%{_datadir}/metainfo
cp -aL %{sourcedir}/build/assets/* %{buildroot}%{_datadir}/sunshine

%post
modprobe uhid
%udev_reload_rules
udevadm trigger
%systemd_post %{service}

%postun
%udev_reload_rules

%files
%caps(cap_sys_admin+p) %{_bindir}/sunshine
%{_userunitdir}/sunshine.service
%{_udevrulesdir}/*-sunshine.rules
%{_modulesloaddir}/*-sunshine.conf
%{_datadir}/applications/*.desktop
%{_datadir}/icons/hicolor/scalable/apps/sunshine.svg
%{_datadir}/metainfo/*.metainfo.xml
%{_datadir}/sunshine/**
