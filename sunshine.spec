# Create an option to build locally without fetchting own repo
# for sourcing and patching
%{!?with_local:%global with_local 0}

# Cross build causes issues
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
BuildRequires: gcc
BuildRequires: gcc-c++
BuildRequires: curl
BuildRequires: openssl-devel
BuildRequires: libcurl-devel
BuildRequires: libdrm-devel
BuildRequires: libva-devel
BuildRequires: libnotify-devel
BuildRequires: nodejs
BuildRequires: npm
BuildRequires: libevdev-devel
BuildRequires: libcap-devel
%if 0%{?fedora}
BuildRequires: ninja-build
BuildRequires: libappindicator-gtk3-devel
BuildRequires: mesa-libgbm-devel
BuildRequires: miniupnpc-devel
BuildRequires: numactl-devel
BuildRequires: opus-devel
BuildRequires: pulseaudio-libs-devel
%endif
%if 0%{?suse_version}
BuildRequires: gcc15
BuildRequires: gcc15-c++
BuildRequires: ninja
BuildRequires: libappindicator3-devel
BuildRequires: libgbm-devel
BuildRequires: Mesa-libGL-devel
BuildRequires: libminiupnpc-devel
BuildRequires: libnuma-devel
BuildRequires: libopus-devel
BuildRequires: libpulse-devel
%endif

%description
Stable build of sunshine.

%define workdir %{_builddir}/%{name}
%define coprdir %{workdir}/%{coprsource}
%define sourcedir %{workdir}/%{source}
%define bindir %{_builddir}/bin
%define cudadir %{_builddir}/cuda-env

%prep
mkdir -p %{bindir}
export PATH=%{bindir}:$PATH

# Install cuda compiler (nvcc) with micromamba (conda)
RPM_ARCH=%{_arch}

if [ "$RPM_ARCH" = "x86_64" ]; then
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

micromamba create -y -p %{cudadir} cuda-nvcc

# To apply working changes, handle sources / patches locally
# COPR should clone the commited changes
%if 0%{?with_local}
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

%build
source /etc/os-release
cd %{sourcedir}

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
if [ "$ID" = "opensuse-leap" ]; then
  GCC_MAJOR=$(gcc -dumpfullversion | cut -d. -f1)
  if [ "$GCC_MAJOR" -lt 15 ]; then
      cmake_args+=(
        "-DCMAKE_C_COMPILER=gcc-15"
        "-DCMAKE_CXX_COMPILER=g++-15"
      )
  fi
fi

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
