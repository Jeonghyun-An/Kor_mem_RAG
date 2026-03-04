param(
  [string]$Image = "landsoftdocker/kormem-fastapi",
  [string]$Cache = "landsoftdocker/kormem-fastapi:buildcache"
)

$tag = Get-Date -Format "yyyyMMdd-HHmm"

docker buildx use kormem-builder 2>$null | Out-Null

docker buildx build `
  -f .\docker\Dockerfile `
  -t "$Image`:latest" `
  -t "$Image`:$tag" `
  --push `
  --cache-from "type=registry,ref=$Cache" `
  --cache-to "type=registry,ref=$Cache,mode=max" `
  .