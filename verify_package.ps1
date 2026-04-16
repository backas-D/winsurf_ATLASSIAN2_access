Add-Type -AssemblyName System.IO.Compression.FileSystem

$zipPath = ".\dist\ATLASSIAN2_Access_v1.5.0.zip"
$zip = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path $zipPath).Path)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " Package Contents Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$entries = $zip.Entries | Sort-Object FullName

Write-Host "Total Files: $($entries.Count)" -ForegroundColor Green
Write-Host ""

$categories = @{
    "Python Files" = @()
    "Config Files" = @()
    "Scripts" = @()
    "Documentation" = @()
    "Static Files" = @()
    "Templates" = @()
    "Other" = @()
}

foreach ($entry in $entries) {
    $name = $entry.FullName
    if ($name -match '\.py$') {
        $categories["Python Files"] += $name
    }
    elseif ($name -match '\.(bat|ps1)$') {
        $categories["Scripts"] += $name
    }
    elseif ($name -match '\.(md|txt|json|example|gitignore)$') {
        if ($name -match '\.md$') {
            $categories["Documentation"] += $name
        } else {
            $categories["Config Files"] += $name
        }
    }
    elseif ($name -match '^static/') {
        $categories["Static Files"] += $name
    }
    elseif ($name -match '^templates/') {
        $categories["Templates"] += $name
    }
    else {
        $categories["Other"] += $name
    }
}

foreach ($category in $categories.Keys | Sort-Object) {
    $files = $categories[$category]
    if ($files.Count -gt 0) {
        Write-Host "[$category]" -ForegroundColor Yellow
        foreach ($file in $files | Sort-Object) {
            Write-Host "  - $file" -ForegroundColor Gray
        }
        Write-Host ""
    }
}

$zip.Dispose()

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Verification Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
