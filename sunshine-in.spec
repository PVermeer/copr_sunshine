# ONLY MAKE CHANGES TO: sunshine.in.spec!

# Create an option to build locally without fetchting own repo
# for sourcing and patching
%{!?with_local:%global with_local 0}

# Source repo
%global author LizardByte
%global source Sunshine
%global sourcerepo https://github.com/LizardByte/Sunshine
%global tag 0
%global commit 0
%global version 0
%global releasetype 0

# Copr repo
%global coprrepo https://github.com/PVermeer/copr_sunshine
%global coprsource copr_sunshine

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
Release: 5%{?dist}
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
BuildRequires: vulkan-devel
BuildRequires: glslc

%description
Self-hosted game stream host for Moonlight.

%define sourcesdir %{_builddir}/source
%define sourcedir %{sourcesdir}/%{source}
%define cudadir %{_builddir}/cuda-env

%prep
# Install cuda compiler (nvcc) with mamba (Anaconda packages)
micromamba create -y -p %{cudadir} conda-forge::cuda-nvcc

# Local testing
%if 0%{?with_local}
  mkdir -p %{sourcedir}
  cp -r %{_topdir}/SOURCES/. %{sourcesdir}
# Copr
%else
  git clone %{sourcerepo} --depth=1 --no-checkout %{sourcedir}
%endif

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
  "-DSUNSHINE_ENABLE_VULKAN=ON"
  "-DSUNSHINE_ENABLE_KWIN=ON"
)
cmake "${cmake_args[@]}"
make -j$(nproc) -C "%{sourcedir}/build"

%install
cd %{sourcedir}/build
%make_install

# Keep old service with symlink
if [ ! -f %{buildroot}%{_userunitdir}/sunshine.service ] \
  && [ -f %{buildroot}%{_userunitdir}/app-dev.lizardbyte.app.Sunshine.service ]; \
then
  ln -s app-dev.lizardbyte.app.Sunshine.service %{buildroot}%{_userunitdir}/sunshine.service
fi

# Add service override to start properly on Gnome
mkdir -p %{buildroot}%{_userunitdir}/sunshine.service.d
echo "\
[Install]
WantedBy=gnome-session.target
WantedBy=xdg-desktop-autostart.target
" > %{buildroot}%{_userunitdir}/sunshine.service.d/override.conf

# Only have one binary (sunshine)
if [ -L %{buildroot}%{_bindir}/sunshine ] \
  && [ -f %{buildroot}%{_bindir}/sunshine-%{version} ]; \
then
  rm %{buildroot}%{_bindir}/sunshine
  mv %{buildroot}%{_bindir}/sunshine-%{version} %{buildroot}%{_bindir}/sunshine
fi

%check
if [ ! -f %{buildroot}%{_userunitdir}/sunshine.service ]; then
  echo "Error: missing sunshine.service" >&2
  exit 1
fi
if [ -L %{buildroot}%{_bindir}/sunshine ]; then
  echo "Error: sunshine is a symlink" >&2
  exit 1
fi

%post
if ! command -v rpm-ostree >/dev/null 2>&1; then
  modprobe uhid || :
  udevadm control --reload-rules || :
  udevadm trigger || :
fi
%systemd_user_post sunshine.service

%preun
%systemd_user_preun sunshine.service

%postun
if ! command -v rpm-ostree >/dev/null 2>&1; then
  udevadm control --reload-rules || :
fi
%systemd_user_postun_with_restart sunshine.service

%files
%caps(cap_sys_admin+p) %{_bindir}/sunshine
%{_userunitdir}/*.service
%{_userunitdir}/sunshine.service.d/override.conf
%{_udevrulesdir}/*-sunshine.rules
%{_modulesloaddir}/*-sunshine.conf
%{_datadir}/applications/*.desktop
%{_datadir}/icons/hicolor/scalable/apps/*.svg
%{_datadir}/icons/hicolor/scalable/status/*.svg
%{_datadir}/metainfo/*.metainfo.xml
%{_datadir}/sunshine/**
