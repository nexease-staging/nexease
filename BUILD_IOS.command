#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/frontend"
command -v node >/dev/null || { echo 'Install Node.js 22 or newer first.'; exit 1; }
npm ci
npm run mobile:build
npx cap sync ios
npx cap open ios
