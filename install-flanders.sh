#!/usr/bin/env bash
# Install FLANDERS: pull the image, put the `flanders` command on PATH, set up the workspace.
set -euo pipefail
IMAGE="${FLANDERS_IMAGE:-ghcr.io/kklicki350/flanders:latest}"
BIN="${FLANDERS_BIN:-$HOME/.local/bin}"
WS="${FLANDERS_WORKSPACE:-$HOME/flanders}"
SHIM_URL="${FLANDERS_SHIM_URL:-https://raw.githubusercontent.com/kklicki350/flanders/main/docker/flanders-shim}"

say() { printf '\n== %s\n' "$*"; }
ask() { local r; read -r -p "$1 [Y/n] " r </dev/tty || r=n; [[ -z "$r" || "$r" =~ ^[Yy] ]]; }

if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
  cat <<MSG
Docker is required and is not available.
  Linux:        https://docs.docker.com/engine/install/
  macOS:        install Docker Desktop (https://docs.docker.com/desktop/setup/install/mac-install/)
  Windows/WSL:  install Docker Desktop and enable WSL integration for this distro
                (Settings > Resources > WSL integration).
Re-run this installer once 'docker info' works.
MSG
  exit 1
fi

say "Pulling $IMAGE"
docker pull --platform linux/amd64 "$IMAGE"

say "Installing the flanders command into $BIN"
mkdir -p "$BIN"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$here/docker/flanders-shim" ]]; then
  install -m 0755 "$here/docker/flanders-shim" "$BIN/flanders"
else
  curl -fsSL "$SHIM_URL" -o "$BIN/flanders" && chmod 0755 "$BIN/flanders"
fi
case ":$PATH:" in *":$BIN:"*) ;; *) echo "Add $BIN to your PATH (e.g. in ~/.bashrc)";; esac

say "Creating the workspace at $WS"
FLANDERS_WORKSPACE="$WS" FLANDERS_IMAGE="$IMAGE" "$BIN/flanders" workspace init

if ask "Download reference data now (Pfam-A and antiSMASH databases, several GB)?"; then
  FLANDERS_WORKSPACE="$WS" FLANDERS_IMAGE="$IMAGE" "$BIN/flanders" reference fetch
else
  echo "Later: flanders reference fetch"
fi

say "Predictors"
FLANDERS_WORKSPACE="$WS" FLANDERS_IMAGE="$IMAGE" "$BIN/flanders" tools status
cat <<MSG

DeepSig is included. SignalP 6, SignalP 5 and TMHMM 2.0c (DTU, academic licence:
https://services.healthtech.dtu.dk/) and Phobius (https://phobius.sbc.su.se/) cannot be
redistributed. To use them, request and download them yourself, then unpack each into
  $WS/tools/<signalp6|signalp5|tmhmm|phobius>/
so that its program sits in a bin/ folder there. Check with: flanders tools status
MSG
say "Done. Try: flanders --help"
