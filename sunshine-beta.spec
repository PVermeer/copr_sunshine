# ONLY MAKE CHANGES TO: sunshine.in.spec!

# Create an option to build locally without fetchting own repo
# for sourcing and patching
%{!?with_local:%global with_local 0}

# Source repo 1
%global author LizardByte
%global source Sunshine
%global sourcerepo https://github.com/LizardByte/Sunshine
%global tag v2026.329.165800
%global commit d03334693c5cbdfba51d7835d7b389b28e4c79d4
%global version 2026.329.165800
%global releasetype beta

# Own copr repo
%global coprrepo https://github.com/pvermeer/rpm-tools
%global coprsource rpm-tools

# Issues ⤵
%undefine _hardened_build

%if "%{releasetype}" == "stable"
Name: sunshine
Conflicts: sunshine-beta
%endif
%if "%{releasetype}" == "beta"
Name: sunshine-beta
Conflicts: sunshine
%endif
Version: %{version}
Release: 1%{?dist}
Summary: Self-hosted game stream host for Moonlight.
License: GPLv3-only
URL: %{coprrepo}

BuildRequires: cmake
BuildRequires: curl
BuildRequires: gcc
BuildRequires: gcc-c++
BuildRequires: git
BuildRequires: libappindicator-gtk3-devel
BuildRequires: libcap-devel
BuildRequires: libcurl-devel
BuildRequires: libdrm-devel
BuildRequires: libevdev-devel
BuildRequires: libnotify-devel
BuildRequires: libva-devel
BuildRequires: mesa-libgbm-devel
BuildRequires: micromamba
BuildRequires: miniupnpc-devel
BuildRequires: nodejs
BuildRequires: npm
BuildRequires: numactl-devel
BuildRequires: openssl-devel
BuildRequires: opus-devel
BuildRequires: pipewire-devel
BuildRequires: pulseaudio-libs-devel
BuildRequires: systemd-rpm-macros
BuildRequires: systemd-udev

%description
Self-hosted game stream host for Moonlight.

%define sourcesdir %{_builddir}/source
%define coprdir %{sourcesdir}/%{coprsource}
%define sourcedir %{sourcesdir}/%{source}
%define bindir %{_builddir}/bin
%define cudadir %{_builddir}/cuda-env

%prep
mkdir -p %{bindir}
export PATH=%{bindir}:$PATH

# Install cuda compiler (nvcc) with mamba (Anaconda packages)
micromamba create -y -p %{cudadir} conda-forge::cuda-nvcc

# To apply working changes handle sources / patches with local changes.
# COPR should clone the commited changes.
%if 0%{?with_local}
  mkdir -p %{coprdir}
  cp -r %{_topdir}/SOURCES/. %{coprdir}
%else
  git clone %{coprrepo} --depth=1 --no-checkout %{coprdir}
  cd %{coprdir}
  git fetch --depth=1 origin
  git reset --hard origin
  cd %{_builddir}
%endif

git clone %{sourcerepo} --depth=1 --no-checkout %{sourcedir}

cd %{sourcedir}
git fetch --depth=1 origin %{commit}
git reset --hard %{commit}
git submodule update --init --depth 1 --recursive
cd %{_builddir}

%build
cd %{sourcedir}
source /etc/os-release

export BRANCH=master
export BUILD_VERSION=v%{version}
export COMMIT=%{commit}

cmake_args=(
  "-B=build"
  "-G=Unix Makefiles"
  "-S=."
  "-DBUILD_DOCS=OFF"
  "-DBUILD_TESTS=OFF"
  "-DBUILD_WERROR=OFF"
  "-DCMAKE_BUILD_TYPE=Release"
  "-DCMAKE_INSTALL_PREFIX=%{_prefix}"
  "-DSUNSHINE_ASSETS_DIR=%{_datadir}/sunshine"
  "-DSUNSHINE_EXECUTABLE_PATH=%{_bindir}/sunshine"
  "-DSUNSHINE_ENABLE_DRM=ON"
  "-DSUNSHINE_ENABLE_PORTAL=ON"
  "-DSUNSHINE_ENABLE_WAYLAND=ON"
  "-DSUNSHINE_ENABLE_X11=ON"
  "-DSUNSHINE_PUBLISHER_NAME=LizardByte"
  "-DSUNSHINE_PUBLISHER_WEBSITE=https://app.lizardbyte.dev"
  "-DSUNSHINE_PUBLISHER_ISSUE_URL=https://app.lizardbyte.dev/support"
  "-DSUNSHINE_ENABLE_CUDA=ON"
  "-DCMAKE_CUDA_COMPILER=%{cudadir}/bin/nvcc"
  "-DCMAKE_CUDA_HOST_COMPILER=%{cudadir}/bin/%{_arch}-conda-linux-gnu-g++"
)
cmake "${cmake_args[@]}"
make -j$(nproc) -C "%{sourcedir}/build"

%install
cd %{sourcedir}/build
%make_install

%check

%post
modprobe uhid || true
udevadm control --reload-rules || true
udevadm trigger || true

%postun
udevadm control --reload-rules || true

%files
%caps(cap_sys_admin+p) %{_bindir}/sunshine
%caps(cap_sys_admin+p) %{_bindir}/sunshine-*
%{_userunitdir}/*.service
%{_udevrulesdir}/*-sunshine.rules
%{_modulesloaddir}/*-sunshine.conf
%{_datadir}/applications/*.desktop
%{_datadir}/icons/hicolor/scalable/apps/*.svg
%{_datadir}/icons/hicolor/scalable/status/*.svg
%{_datadir}/metainfo/*.metainfo.xml
%{_datadir}/sunshine/**
