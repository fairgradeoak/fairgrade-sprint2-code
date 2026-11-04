#!/bin/sh
set -eu
cd "$(dirname "$0")"
export PORT=3000
node scripts/verify-models.mjs
printf '%s\n' 'Open http://localhost:3000/ (not 127.0.0.1).'
exec node server/server.mjs
