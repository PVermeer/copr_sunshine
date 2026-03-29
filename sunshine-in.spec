# ONLY MAKE CHANGES TO: sunshine.in.spec!

# Create an option to build locally without fetchting own repo
# for sourcing and patching
%{!?with_local:%global with_local 0}

%global build_version 0
%global branch 0
%global commit 0
%global release_type 0

# Issues ⤵
%undefine _hardened_build

%if "%{release_type}" == "stable"
Name: sunshine
Conflicts: sunshine-beta
%endif
%if "%{release_type}" == "beta"
Name: sunshine-beta
Conflicts: sunshine
%endif
Version: %{build_version}
Release: 2%{?dist}
Summary: Self-hosted game stream host for Moonlight.
License: GPLv3-only
URL: https://github.com/LizardByte/Sunshine

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

%define workdir %{_builddir}/source
%define sourcedir %{workdir}/Sunshine
%define bindir %{_builddir}/bin
%define cudadir %{_builddir}/cuda-env

%prep
mkdir -p %{bindir}
mkdir -p %{workdir}
mkdir -p %{sourcedir}
export PATH=%{bindir}:$PATH

# Install cuda compiler (nvcc) with micromamba (conda)
if [ "%{_arch}" = "x86_64" ]; then
  curl -L --fail --retry 5 --retry-delay 2 \
  -o /tmp/micromamba.tar.bz2 \
    https://github.com/mamba-org/micromamba-releases/releases/latest/download/micromamba-linux-64.tar.bz2
else
  curl -L --fail --retry 5 --retry-delay 2 \
  -o /tmp/micromamba.tar.bz2 \
    https://github.com/mamba-org/micromamba-releases/releases/latest/download/micromamba-linux-%{_arch}.tar.bz2
fi
tar -xjf /tmp/micromamba.tar.bz2 -C /tmp
install -Dm755 /tmp/bin/micromamba %{bindir}/micromamba
micromamba create -y -p %{cudadir} nvidia::cuda-nvcc

# Source
cd %{workdir}
%if 0%{?with_local}
  mkdir -p %{workdir}
  cp -r %{_topdir}/SOURCES/. %{workdir}
%else
  git clone %{url} %{sourcedir}
%endif
cd %{sourcedir}
git reset --hard %{commit}
git submodule update --recursive --init --depth 1
cd %{workdir}

%build
cd %{sourcedir}
source /etc/os-release

export BRANCH=%{branch}
export BUILD_VERSION=v%{build_version}
export COMMIT=%{commit}

cmake_args=(
  "-B=build"
  "-G=Unix Makefiles"
  "-S=."
  "-DBUILD_DOCS=OFF"
  "-DBUILD_TESTS=ON"
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
