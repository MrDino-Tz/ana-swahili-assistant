$ErrorActionPreference = "Stop"

$MODEL_URL = "https://huggingface.co/Skier8402/gemma2-2b-swahili-it-Q4_K_M-GGUF/resolve/main/gemma2-2b-swahili-it-q4_k_m.gguf"
$MODEL_FILE = "gemma2-2b-swahili-it-q4_k_m.gguf"
$MODEL_NAME = "gemma2-swahili"

Write-Host "=== A.N.A Swahili Neural CLI Assistant Setup (Windows PowerShell) ===" -ForegroundColor Cyan
Write-Host "Working directory: $PSScriptRoot" -ForegroundColor Gray

# 1. Download Gemma 2 Swahili IT Q4_K_M GGUF if it doesn't exist
if (-not (Test-Path $MODEL_FILE)) {
    Write-Host "Downloading Gemma 2 Swahili IT (Q4_K_M CPU-Optimized, ~1.6GB) from Hugging Face..." -ForegroundColor Yellow
    Write-Host "This will download significantly faster and run much faster on CPU hardware!" -ForegroundColor Yellow
    Write-Host "Please wait..." -ForegroundColor Gray
    
    if (Get-Command "curl.exe" -ErrorAction SilentlyContinue) {
        curl.exe -L -# -o $MODEL_FILE $MODEL_URL
    } else {
        Invoke-WebRequest -Uri $MODEL_URL -OutFile $MODEL_FILE -UseBasicParsing
    }
    Write-Host "Download completed successfully!" -ForegroundColor Green
} else {
    Write-Host "Model file $MODEL_FILE already exists, skipping download." -ForegroundColor Green
}

# 2. Create Ollama Modelfile
Write-Host "Creating Ollama Modelfile..." -ForegroundColor Gray
$ModelfileContent = @"
FROM ./$MODEL_FILE

# Set parameters
PARAMETER temperature 0.7
PARAMETER stop "<import>"
PARAMETER stop "<|im_start|>"
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|endoftext|>"

# Set system prompt customized for Swahili personal assistant A.N.A
SYSTEM """Wewe ni A.N.A (Ana Neural Assistant), msaidizi mwenye ujumbe wa kibinafsi na mtaalamu wa teknolojia na maisha ya kila siku. Unajieleza kwa lugha ya Kiswahili safi na yenye uelewa mkubwa wa utamaduni wa Afrika Mashariki. Jibu kwa ufupi na kwa usahihi wa hali ya juu."""
"@

Set-Content -Path "Modelfile" -Value $ModelfileContent -Encoding UTF8

# 3. Register model with Ollama
Write-Host "Registering model '$MODEL_NAME' with local Ollama service..." -ForegroundColor Gray
if (Get-Command "ollama" -ErrorAction SilentlyContinue) {
    ollama create $MODEL_NAME -f Modelfile
    Write-Host "=== Setup Completed Successfully! ===" -ForegroundColor Green
    Write-Host "You can now run 'ollama run $MODEL_NAME' or run the A.N.A CLI script via 'python ana.py'." -ForegroundColor Green
} else {
    Write-Host "Ollama command was not found. Please install Ollama from https://ollama.com/ to run A.N.A in offline/local CPU mode." -ForegroundColor Yellow
    Write-Host "You can still run A.N.A in cloud mode via Groq since GROQ_API_KEY is configured." -ForegroundColor Green
}
