#!/bin/bash
# A.N.A Swahili Neural CLI Assistant Setup Script
# Developed by Antigravity

set -e

WORKSPACE_DIR="/home/mrdino/Desktop/DTC/1/A.N.A project FYP/ai-asstistant"
MODEL_URL="https://huggingface.co/Skier8402/gemma2-2b-swahili-it-Q4_K_M-GGUF/resolve/main/gemma2-2b-swahili-it-q4_k_m.gguf"
MODEL_FILE="gemma2-2b-swahili-it-q4_k_m.gguf"
MODEL_NAME="gemma2-swahili"

echo "=== A.N.A Swahili Neural CLI Assistant Setup ==="
echo "Working directory: $WORKSPACE_DIR"

# 1. Download Gemma 2 Swahili IT Q4_K_M GGUF if it doesn't exist
if [ ! -f "$MODEL_FILE" ]; then
    echo "Downloading Gemma 2 Swahili IT (Q4_K_M CPU-Optimized, ~1.6GB) from Hugging Face..."
    echo "This will download significantly faster and run much faster on CPU hardware!"
    echo "Please wait..."
    curl -L -# -o "$MODEL_FILE" "$MODEL_URL"
    echo "Download completed successfully!"
else
    echo "Model file $MODEL_FILE already exists, skipping download."
fi

# 2. Create Ollama Modelfile
echo "Creating Ollama Modelfile..."
cat <<EOF > Modelfile
FROM ./$MODEL_FILE

# Set parameters
PARAMETER temperature 0.7
PARAMETER stop "<import>"
PARAMETER stop "<|im_start|>"
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|endoftext|>"

# Set system prompt customized for Swahili personal assistant A.N.A
SYSTEM """Wewe ni A.N.A (Ana Neural Assistant), msaidizi mwenye ujumbe wa kibinafsi na mtaalamu wa teknolojia na maisha ya kila siku. Unajieleza kwa lugha ya Kiswahili safi na yenye uelewa mkubwa wa utamaduni wa Afrika Mashariki. Jibu kwa ufupi na kwa usahihi wa hali ya juu."""
EOF

# 3. Register model with Ollama
echo "Registering model '$MODEL_NAME' with local Ollama service..."
ollama create "$MODEL_NAME" -f Modelfile

echo "=== Setup Completed Successfully! ==="
echo "You can now run 'ollama run $MODEL_NAME' or run the A.N.A CLI script."
