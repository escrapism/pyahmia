#!/usr/bin/env bash
set -euo pipefail

trap 'echo "Error at line $LINENO. Exit code: $?"; exit 1' ERR

echo "Detecting Linux distribution..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=${ID:-unknown}
    PRETTY=${PRETTY_NAME:-$DISTRO}
else
    echo "Could not detect distro."
    DISTRO="unknown"
    PRETTY="Unknown"
fi

PKG_UPDATE=""
PKG_INSTALL=""

case "$DISTRO" in
    ubuntu|debian)
        PKG_UPDATE="sudo apt update"
        PKG_INSTALL="sudo apt install -y"
        ;;
    fedora|rhel|centos)
        PKG_UPDATE="sudo dnf makecache"
        PKG_INSTALL="sudo dnf install -y"
        ;;
    arch)
        PKG_UPDATE="sudo pacman -Sy"
        PKG_INSTALL="sudo pacman -S --noconfirm"
        ;;
    opensuse*|suse)
        PKG_UPDATE="sudo zypper refresh"
        PKG_INSTALL="sudo zypper install -y"
        ;;
    *)
        echo "Unknown distro: $DISTRO"
        ;;
esac

if [[ -n "$PKG_INSTALL" ]]; then
    echo "Installing Tor on: $PRETTY"
    $PKG_UPDATE
    $PKG_INSTALL tor
else
    echo "Falling back to building Tor from source..."

    # Try to install build dependencies if apt is present
    if command -v apt >/dev/null 2>&1; then
        sudo apt update
        sudo apt install -y build-essential git automake autoconf libtool make pkg-config \
            libevent-dev libssl-dev zlib1g-dev
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y gcc make git automake autoconf libtool pkg-config \
            libevent-devel openssl-devel zlib-devel
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -S --noconfirm base-devel git automake autoconf libtool pkgconf \
            libevent openssl zlib
    elif command -v zypper >/dev/null 2>&1; then
        sudo zypper install -y gcc make git automake autoconf libtool pkg-config \
            libevent-devel libopenssl-devel zlib-devel
    else
        echo "Could not detect a package manager to install build deps."
        exit 1
    fi

    # Clean up any old source
    rm -rf tor || true

    # Clone Tor source
    git clone https://git.torproject.org/tor.git
    cd tor

    # Build and install
    ./autogen.sh
    ./configure
    make -j"$(nproc)"
    sudo make install

    cd ..
    echo "Tor built and installed from source"
    exit 0
fi

echo "Tor installation complete"
