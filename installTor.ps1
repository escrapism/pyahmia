$ErrorActionPreference = "Stop"

Write-Output "Checking for winget..."

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Error "winget not found. Please install winget first."
    exit 1
}

Write-Output "Installing Tor Browser..."
try {
    winget install --id TorProject.TorBrowser -e --accept-source-agreements --accept-package-agreements
    Write-Output "Tor Browser installation complete."
} catch {
    Write-Error "Failed to install Tor Browsers. Error: $_"
    exit 1
}
