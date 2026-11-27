# Запуск усього проєкту: бази, дані, сервіси. Викликається з start.bat.
$ErrorActionPreference = "Continue"
Set-Location (Split-Path $PSScriptRoot -Parent)
$Host.UI.RawUI.WindowTitle = "DB_kursova — запуск"

function Fail($msg) {
    Write-Host " ! $msg" -ForegroundColor Red
    Read-Host "Enter — закрити"
    exit 1
}

function Wait-Until($seconds, [scriptblock]$check) {
    $deadline = (Get-Date).AddSeconds($seconds)
    while ((Get-Date) -lt $deadline) {
        if (& $check) { return $true }
        Start-Sleep -Seconds 2
    }
    return $false
}

function Get-EsCount {
    try { (Invoke-RestMethod "http://127.0.0.1:9200/recipes/_count" -TimeoutSec 5).count }
    catch { 0 }
}

Write-Host ""
Write-Host " ==== Кулінарні рецепти та шеф-кухарі ====" -ForegroundColor Cyan
Write-Host ""

# ---------- 1. Docker
Write-Host "[1/5] Перевіряю Docker..."
docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "      Docker не запущений, стартую Docker Desktop..."
    Start-Process "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
    $ok = Wait-Until 180 { docker info *> $null; $LASTEXITCODE -eq 0 }
    if (-not $ok) { Fail "Docker так і не запустився. Запусти Docker Desktop вручну." }
}
Write-Host "      ok"

# ---------- 2. Бази даних і брокер
Write-Host "[2/5] Піднімаю Mongo, Redis, Elasticsearch, Neo4j, RabbitMQ (чекаю healthy)..."
docker compose up -d --wait
if ($LASTEXITCODE -ne 0) { Fail "Щось не піднялось. Подивись: docker compose ps" }

# ---------- 3. Дані (лише якщо індекс порожній)
Write-Host "[3/5] Перевіряю дані в Elasticsearch..."
function Test-Es {
    try { Invoke-RestMethod "http://127.0.0.1:9200/_cluster/health" -TimeoutSec 5 | Out-Null; $true }
    catch { $false }
}
$esUp = Wait-Until 30 { Test-Es }
if (-not $esUp) {
    # ES живий усередині контейнера, але порт 9200 з Windows «завис» — пересоздаємо контейнер
    Write-Host "      ES не відповідає з Windows, перезапускаю контейнер elasticsearch..." -ForegroundColor Yellow
    docker compose up -d --force-recreate --wait elasticsearch
    $esUp = Wait-Until 120 { Test-Es }
}
if (-not $esUp) { Fail "Порт 9200 так і не відповідає. Перезапусти Docker Desktop (іконка кита в треї -> Restart) і запусти start.bat ще раз." }
$count = Get-EsCount
if ($count -gt 0) {
    Write-Host "      в індексі вже $count рецептів, пропускаю завантаження"
} else {
    Write-Host "      індекс порожній — завантажую 20000 рецептів у Mongo..."
    uv run python scripts/load_mongo.py --limit 20000
    if ($LASTEXITCODE -ne 0) { Fail "Не вдалося завантажити дані (чи лежить data\RAW_recipes.csv?)" }
    Write-Host "      переіндексовую Elasticsearch і Neo4j (1–3 хв)..."
    $env:ES_URL = "http://127.0.0.1:9200"
    uv run --package writer-service python scripts/reindex_from_mongo.py --es --neo4j
    if ($LASTEXITCODE -ne 0) { Fail "Переіндексація не вдалась." }
}

# ---------- 4. Сервіси
Write-Host "[4/5] Збираю і запускаю query, 3 writer-и, ingest (перший раз — 5–10 хв)..."
docker compose --profile app up -d --build
if ($LASTEXITCODE -ne 0) { Fail "Сервіси не запустились. Подивись: docker compose --profile app logs" }

# ---------- 5. Чекаю сайт і відкриваю
Write-Host "[5/5] Чекаю http://localhost:8000 ..."
$ok = Wait-Until 120 {
    try { Invoke-WebRequest "http://127.0.0.1:8000/" -UseBasicParsing -TimeoutSec 3 | Out-Null; $true }
    catch { $false }
}
if (-not $ok) { Fail "Сайт не відповідає. Логи: docker compose logs query-service" }
Start-Process "http://localhost:8000"

Write-Host ""
Write-Host " Готово!" -ForegroundColor Green
Write-Host "   сайт ............ http://localhost:8000"
Write-Host "   RabbitMQ ........ http://localhost:15672   (guest / guest)"
Write-Host "   Neo4j ........... http://localhost:7474    (neo4j / change-me)"
Write-Host ""
Write-Host " Шардований кластер для бенчмарку (не стартує автоматично):"
Write-Host "   docker compose -f docker-compose.sharded.yml up -d"
Write-Host ""
Write-Host " Зупинити все — stop.bat"
Read-Host "Enter — закрити це вікно (сервіси продовжать працювати)"
