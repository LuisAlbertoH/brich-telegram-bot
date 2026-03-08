$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$PythonCmd = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCmd = "py -3"
}
elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCmd = "python"
}
else {
    throw "No se encontro py ni python en PATH."
}

if (-not (Test-Path ".venv")) {
    Invoke-Expression "$PythonCmd -m venv .venv"
}

.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements.txt

.\.venv\Scripts\python main.py
