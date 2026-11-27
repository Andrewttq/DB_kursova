# Зупинка всього проєкту. Викликається з stop.bat. Дані в томах зберігаються.
Set-Location (Split-Path $PSScriptRoot -Parent)
Write-Host "Зупиняю сервіси і бази (дані зберігаються)..."
docker compose --profile app stop
docker compose -f docker-compose.sharded.yml stop 2>$null
Write-Host "Готово." -ForegroundColor Green
Read-Host "Enter — закрити"
