#!/usr/bin/env bash
set -euo pipefail

#
# Simple helper to download the Charm Gum binary that matches the current
# machine and store it inside repo-local bin/ so the installer can run even
# when Gum is not already installed on the host.
#

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="${PROJECT_ROOT}/bin"
mkdir -p "${BIN_DIR}"

OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

asset_name=""
case "${OS}" in
  linux)
    case "${ARCH}" in
      x86_64|amd64) asset_name="gum_Linux_x86_64.tar.gz" ;;
      arm64|aarch64) asset_name="gum_Linux_arm64.tar.gz" ;;
      armv7l|armv7) asset_name="gum_Linux_armv7.tar.gz" ;;
      armv6l|armv6) asset_name="gum_Linux_armv6.tar.gz" ;;
      i386|i686) asset_name="gum_Linux_i386.tar.gz" ;;
      *)
        echo "Unsupported Linux architecture: ${ARCH}" >&2
        exit 1
        ;;
    esac
    ;;
  darwin)
    case "${ARCH}" in
      x86_64) asset_name="gum_Darwin_x86_64.tar.gz" ;;
      arm64) asset_name="gum_Darwin_arm64.tar.gz" ;;
      *)
        echo "Unsupported macOS architecture: ${ARCH}" >&2
        exit 1
        ;;
    esac
    ;;
  *)
    cat >&2 <<'EOF'
This helper currently supports Linux and macOS hosts. For Windows, install Gum
via the official instructions (winget, scoop, or downloading the .zip) and make
sure it is available on your PATH before running the BoxLab CLI.
EOF
    exit 1
    ;;
esac

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

# Get the latest version from GitHub API
echo "Fetching latest Gum version..."
VERSION=$(curl -s "https://api.github.com/repos/charmbracelet/gum/releases/latest" | grep '"tag_name":' | sed -E 's/.*"v([^"]+)".*/\1/')
if [[ -z "${VERSION}" ]]; then
  echo "Failed to fetch latest version, using v0.17.0 as fallback" >&2
  VERSION="0.17.0"
fi

# Construct the versioned asset name
versioned_asset=$(echo "${asset_name}" | sed "s/gum_/gum_${VERSION}_/")
ARCHIVE="${TMP_DIR}/gum.tar.gz"
echo "Downloading ${versioned_asset} ..."
curl -L "https://github.com/charmbracelet/gum/releases/download/v${VERSION}/${versioned_asset}" -o "${ARCHIVE}"

# Extract from versioned directory structure
tar -xf "${ARCHIVE}" -C "${TMP_DIR}"
extracted_dir="${TMP_DIR}/gum_${VERSION}_${OS^}_${ARCH}"
if [[ ! -f "${extracted_dir}/gum" ]]; then
  echo "Failed to find gum binary inside the archive at ${extracted_dir}" >&2
  exit 1
fi

install_path="${BIN_DIR}/gum"
mv "${extracted_dir}/gum" "${install_path}"
chmod +x "${install_path}"

cat <<EOF
✓ Gum installed to ${install_path}
Add ${BIN_DIR} to your PATH or run the CLI with PATH="${BIN_DIR}:\$PATH" python3 main.py
EOF
