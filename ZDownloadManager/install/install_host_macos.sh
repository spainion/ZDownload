#!/usr/bin/env bash
set -euo pipefail
# Script to install the ZDownloadManager native messaging host on macOS.

if [[ -z "${ZDM_EXT_ID:-}" ]]; then
  echo "Please set ZDM_EXT_ID environment variable to the extension ID" >&2
  exit 1
fi
MANIFEST_DIR="${HOME}/Library/Application Support/Google/Chrome/NativeMessagingHosts"
mkdir -p "$MANIFEST_DIR"
MANIFEST_PATH="${MANIFEST_DIR}/com.zdownloadmanager.host.json"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE="${SCRIPT_DIR}/host.json.template"
HOST_PATH="${SCRIPT_DIR}/../zdownloadmanager/integration/native_messaging_host.py"
sed -e "s/__EXT_ID__/${ZDM_EXT_ID}/" -e "s#__HOST_PATH__#${HOST_PATH}#" "$TEMPLATE" > "$MANIFEST_PATH"
echo "Installed host manifest at $MANIFEST_PATH"
