Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$PublicRepo = "C:\Users\Administrator\wenallpapersstatus-page"
$PublicRepoUrl = "https://github.com/WENQUAN0816/wenallpapersstatus-page.git"

& pwsh -File (Join-Path $PSScriptRoot "Update-PaperStatus.ps1")

if (-not (Test-Path $PublicRepo)) {
    git clone $PublicRepoUrl $PublicRepo
}

Copy-Item -LiteralPath (Join-Path $RepoRoot "index.html") -Destination (Join-Path $PublicRepo "index.html") -Force
Copy-Item -LiteralPath (Join-Path $RepoRoot "status_bar_chart.svg") -Destination (Join-Path $PublicRepo "status_bar_chart.svg") -Force
Copy-Item -LiteralPath (Join-Path $RepoRoot "status_data.json") -Destination (Join-Path $PublicRepo "status_data.json") -Force

$Changed = git -C $PublicRepo status --short
if ($Changed) {
    git -C $PublicRepo add index.html status_bar_chart.svg status_data.json
    git -C $PublicRepo commit -m "Update public dashboard"
    git -C $PublicRepo push origin HEAD:main
}
else {
    Write-Host "Public dashboard is already up to date."
}
