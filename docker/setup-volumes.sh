#!/bin/bash
# setup-volumes.sh
# Kor_mem_RAG 최초 1회 실행
# Library_AI_land 리소스 (건드리지 않음):
#   network: library-ragnet  |  volumes: library_*  |  nginx: /data/library-rag/runtime/nginx/
# Kor_mem_RAG 신규:
#   network: kor-mem-net     |  volumes: kormem_*   |  nginx: /data/kormem/runtime/nginx/
set -e

echo "========================================"
echo " Kor_mem_RAG  -  Initial Setup"
echo "========================================"

echo "[1/4] Docker network..."
docker network create kor-mem-net 2>/dev/null && echo "  + kor-mem-net created" || echo "  . kor-mem-net already exists"

echo "[2/4] Docker volumes..."
for VOL in kormem_etcd_data kormem_milvus_data kormem_minio_data; do
  docker volume create "$VOL" 2>/dev/null && echo "  + $VOL" || echo "  . $VOL already exists"
done

echo "[3/4] Nginx runtime directories..."
NGINX_DIR="/data/kormem/runtime/nginx/conf.d"
mkdir -p "$NGINX_DIR"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

[ ! -f "/data/kormem/runtime/nginx/nginx.conf" ] \
  && cp "$SCRIPT_DIR/nginx/nginx.conf" "/data/kormem/runtime/nginx/nginx.conf" \
  && echo "  + nginx.conf copied" || echo "  . nginx.conf already exists"

[ ! -f "/data/kormem/runtime/nginx/conf.d/app.conf" ] \
  && cp "$SCRIPT_DIR/nginx/conf.d/app.conf" "/data/kormem/runtime/nginx/conf.d/app.conf" \
  && echo "  + app.conf copied" || echo "  . app.conf already exists"

echo "[4/4] Verification..."
docker network ls | grep -E "kor-mem-net|library-ragnet"
docker volume ls | grep -E "kormem_|library_"

echo ""
echo "========================================"
echo " Setup complete!"
echo ""
echo " 포트 (Library_AI_land 충돌 없음)"
echo "   MinIO   : 20000/20001  (library: 19000/19001)"
echo "   vLLM    : 18082        (library: 18080)"
echo "   FastAPI : 18001        (library: 18000)"
echo "   Nginx   : 91           (library: 90)"
echo ""
echo " Next: cd docker && docker compose up -d"
echo "========================================"
