param(
    [string]$Image = "landsoftdocker/kormem-nuxt",
    [string]$Cache = "landsoftdocker/kormem-nuxt:buildcache"
)

$ErrorActionPreference = "Stop"

$tag = Get-Date -Format "yyyyMMdd-HHmm"

Write-Host "================================="
Write-Host "Building Nuxt Image"
Write-Host "Image : $Image"
Write-Host "Tag   : $tag"
Write-Host "================================="

docker buildx use kormem-builder 2>$null | Out-Null

docker buildx build `
  -f .\docker\Dockerfile.nuxt `
  -t "$Image`:latest" `
  -t "$Image`:$tag" `
  --push `
  --cache-from "type=registry,ref=$Cache" `
  --cache-to "type=registry,ref=$Cache,mode=max" `
  .\frontend

Write-Host ""
Write-Host "Nuxt build completed"
Write-Host "Tag pushed : $tag"