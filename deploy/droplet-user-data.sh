#!/bin/bash
# DigitalOcean droplet first-boot: Docker + Compose plugin.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y ca-certificates curl git ufw
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
