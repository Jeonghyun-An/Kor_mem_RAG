# setup-volumes.ps1
# Kor_mem_RAG External 볼륨과 네트워크 생성 스크립트 - 처음에 한번만 실행
# 실행 명령어: .\setup-volumes.ps1
#
# Library_AI_land 기존 리소스 (건드리지 않음):
#   network : library-ragnet
#   volumes : library_etcd_data / library_milvus_data / library_minio_data

Write-Host "=== Kor_mem_RAG Setup ===" -ForegroundColor Green

# 1. 네트워크 생성
Write-Host "`n[1/4] Creating network..." -ForegroundColor Cyan
docker network create kor-mem-net 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  + Network 'kor-mem-net' created" -ForegroundColor Green
} else {
    Write-Host "  . Network 'kor-mem-net' already exists" -ForegroundColor Yellow
}

# 2. etcd 볼륨 생성
Write-Host "`n[2/4] Creating etcd volume..." -ForegroundColor Cyan
docker volume create kormem_etcd_data 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  + Volume 'kormem_etcd_data' created" -ForegroundColor Green
} else {
    Write-Host "  . Volume 'kormem_etcd_data' already exists" -ForegroundColor Yellow
}

# 3. Milvus 볼륨 생성
Write-Host "`n[3/4] Creating Milvus volume..." -ForegroundColor Cyan
docker volume create kormem_milvus_data 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  + Volume 'kormem_milvus_data' created" -ForegroundColor Green
} else {
    Write-Host "  . Volume 'kormem_milvus_data' already exists" -ForegroundColor Yellow
}

# 4. MinIO 볼륨 생성
Write-Host "`n[4/4] Creating MinIO volume..." -ForegroundColor Cyan
docker volume create kormem_minio_data 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  + Volume 'kormem_minio_data' created" -ForegroundColor Green
} else {
    Write-Host "  . Volume 'kormem_minio_data' already exists" -ForegroundColor Yellow
}

# 5. 확인
Write-Host "`n=== Verification ===" -ForegroundColor Green

Write-Host "`nNetworks:" -ForegroundColor Cyan
docker network ls | Select-String -Pattern "kor-mem-net|library-ragnet"

Write-Host "`nVolumes:" -ForegroundColor Cyan
docker volume ls | Select-String -Pattern "kormem_|library_"

Write-Host "`n Setup complete!" -ForegroundColor Green
Write-Host "`n포트 (Library_AI_land 충돌 없음)" -ForegroundColor Yellow
Write-Host "  MinIO   : 20000/20001  (library: 19000/19001)" -ForegroundColor Yellow
Write-Host "  vLLM    : 18082        (library: 18080)" -ForegroundColor Yellow
Write-Host "  FastAPI : 18001        (library: 18000)" -ForegroundColor Yellow
Write-Host "  Nginx   : 91           (library: 90)" -ForegroundColor Yellow
Write-Host "`nNext step: Portainer -> Stacks -> Add stack" -ForegroundColor Yellow