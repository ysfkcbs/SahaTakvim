#!/usr/bin/env bash
# One-time setup for the self-hosted GitHub Actions runner on a Mac.
# Run this on a fresh machine after: brew install gh && gh auth login (with
# 'workflow' scope: gh auth refresh -h github.com -s workflow) and after
# cloning this repo to its permanent path.
#
# Usage: ./scripts/setup_github_runner.sh <github-owner/repo> [runner-name]
set -euo pipefail

REPO="${1:?Usage: $0 <owner/repo> [runner-name]}"
RUNNER_NAME="${2:-$(scutil --get ComputerName | tr ' ' '-')}"
RUNNER_DIR="$HOME/actions-runner"
ARCH="$(uname -m)"
OS_ARCH="osx-$([ "$ARCH" = "arm64" ] && echo arm64 || echo x64)"

VERSION="$(gh api repos/actions/runner/releases/latest --jq '.tag_name' | sed 's/^v//')"
echo "==> Installing GitHub Actions runner v${VERSION} for ${OS_ARCH}"

mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"
curl -o "actions-runner-${OS_ARCH}-${VERSION}.tar.gz" -L \
  "https://github.com/actions/runner/releases/download/v${VERSION}/actions-runner-${OS_ARCH}-${VERSION}.tar.gz"
tar xzf "actions-runner-${OS_ARCH}-${VERSION}.tar.gz"

echo "==> Registering runner against ${REPO}"
TOKEN="$(gh api -X POST "repos/${REPO}/actions/runners/registration-token" --jq .token)"
./config.sh --url "https://github.com/${REPO}" --token "$TOKEN" --unattended --name "$RUNNER_NAME" --work _work --replace

echo "==> Working around Docker Desktop's keychain-backed credential store"
# Docker Desktop's default credsStore ("desktop") shells out to a helper that
# queries the macOS login keychain. The runner's LaunchAgent session can't
# unlock that keychain (non-interactive session), so every image pull/build
# fails with "keychain cannot be accessed because the current session does
# not allow user interaction." Fix: point this runner's jobs at a Docker
# config with no credsStore. Safe because this project only pulls public
# images (python, nginx, certbot) — never anything requiring registry auth.
mkdir -p "$RUNNER_DIR/.docker-config"
cat > "$RUNNER_DIR/.docker-config/config.json" <<'EOF'
{
  "auths": {},
  "credsStore": "none"
}
EOF
cat > "$RUNNER_DIR/.docker-config/docker-credential-none" <<'HELPER'
#!/bin/sh
case "$1" in
  get)
    echo "credentials not found in native keychain"
    exit 1
    ;;
  list)
    echo "{}"
    ;;
  *)
    exit 0
    ;;
esac
HELPER
chmod +x "$RUNNER_DIR/.docker-config/docker-credential-none"
ln -sf "$RUNNER_DIR/.docker-config/docker-credential-none" /opt/homebrew/bin/docker-credential-none
echo "DOCKER_CONFIG=$RUNNER_DIR/.docker-config" > "$RUNNER_DIR/.env"

echo "==> Installing as a persistent background service (no sudo needed)"
./svc.sh install
./svc.sh start
./svc.sh status

echo "==> Done. Note: .github/workflows/deploy.yml also sets DOCKER_CONFIG"
echo "    explicitly at the job level, so this is belt-and-suspenders — but"
echo "    keep both, other workflows/jobs on this runner will need it too."
