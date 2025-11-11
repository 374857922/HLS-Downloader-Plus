#!/bin/sh
set -e

# 如果环境变量没传，就默认空字符串 → 浏览器自动用当前域名+端口
API_BASE=${API_BASE:-""}
WS_BASE=${WS_BASE:-""}

# 一次性替换
find /app/web -type f \( -name "*.html" -o -name "*.js" \) \
  -exec sed -i "s|__API_BASE__|${API_BASE}|g; s|__WS_BASE__|${WS_BASE}|g" {} +

exec "$@"