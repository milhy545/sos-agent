#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${HOME}/.local/bin/sos"
BACKUP_SUFFIX="$(date +%Y%m%d-%H%M%S)"

mkdir -p "$(dirname "${TARGET}")"

if [ -e "${TARGET}" ] && [ ! -L "${TARGET}" ]; then
  cp "${TARGET}" "${TARGET}.bak-${BACKUP_SUFFIX}"
  echo "Backed up existing ${TARGET} -> ${TARGET}.bak-${BACKUP_SUFFIX}"
fi

ln -sf "${REPO_DIR}/sos-launcher.sh" "${TARGET}"
chmod +x "${REPO_DIR}/sos-launcher.sh"

echo "Linked ${TARGET} -> ${REPO_DIR}/sos-launcher.sh"
echo "Now `sos ...` runs from this repo (no install.sh needed)."
