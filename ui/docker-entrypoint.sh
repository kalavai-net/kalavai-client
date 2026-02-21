#!/bin/sh
# Build in the containe to set env variables
set -e

echo "Building Next.js app with runtime environment..."
npm run build

echo "Starting Next.js server..."
exec npm run start
