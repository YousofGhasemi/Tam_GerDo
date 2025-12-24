#!/bin/sh
set -e

echo "Generating nginx config..."
envsubst < /etc/nginx/default.conf.tpl > /etc/nginx/conf.d/default.conf

echo "Validating nginx config..."
nginx -t

echo "Starting nginx..."
nginx -g 'daemon off;'
