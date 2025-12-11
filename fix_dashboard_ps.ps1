# PowerShell script to fix dashboard.html template syntax errors
$filePath = "c:\Users\Ryle Fritz\CSIT327-G8-HabitCanvas\main\templates\main\dashboard.html"

Write-Host "Reading file..." -ForegroundColor Yellow
$content = Get-Content $filePath -Raw -Encoding UTF8

Write-Host "Original file size: $($content.Length) bytes" -ForegroundColor Cyan

# Fix all the template syntax errors
$content = $content -replace "{% if request\.GET\.sort=='default'", "{% if request.GET.sort == 'default'"
$content = $content -replace "{% if request\.GET\.sort=='priority'", "{% if request.GET.sort == 'priority'"
$content = $content -replace "{% if request\.GET\.category=='School'", "{% if request.GET.category == 'School'"
$content = $content -replace "{% if request\.GET\.category=='Personal'", "{% if request.GET.category == 'Personal'"
$content = $content -replace "{% if request\.GET\.category=='Work'", "{% if request.GET.category == 'Work'"
$content = $content -replace "{% if request\.GET\.difficulty=='Easy'", "{% if request.GET.difficulty == 'Easy'"
$content = $content -replace "{% if request\.GET\.difficulty=='Medium'", "{% if request.GET.difficulty == 'Medium'"
$content = $content -replace "{% if request\.GET\.difficulty=='Hard'", "{% if request.GET.difficulty == 'Hard'"

# Fix the split line for "default" option
$content = $content -replace '{% endif\r?\n\s+%}', '{% endif %}'

Write-Host "Writing fixed content..." -ForegroundColor Yellow
$content | Set-Content $filePath -Encoding UTF8 -Force -NoNewline

Write-Host "Done! File fixed successfully." -ForegroundColor Green
Write-Host "New file size: $((Get-Item $filePath).Length) bytes" -ForegroundColor Cyan
