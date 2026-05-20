#!/usr/bin/env python3
# A.N.A (Ana Neural Assistant) - Swahili Hybrid Core
# Supports Local Ollama (Offline) and Blazing Fast Free Cloud APIs (Groq / OpenRouter)
# Zero heavy dependencies (Pure Python 3 standard library)
# Custom Prompt Engineering & Dynamic Time-Aware Persona Engine
# High-Fidelity Swahili Text-to-Speech (TTS) Voice Engine

import sys
import os
import json
import urllib.request
import urllib.error
import urllib.parse
import argparse
from datetime import datetime
import platform


OLLAMA_API_URL = "http://localhost:11434/api/chat"

# ANSI Terminal Colors
C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_BLUE = "\033[94m"
C_MAGENTA = "\033[95m"
C_CYAN = "\033[96m"
C_WHITE = "\033[97m"
C_GRAY = "\033[90m"
C_BOLD = "\033[1m"
C_RESET = "\033[0m"

# Premium Banner
BANNER = f"""{C_CYAN}{C_BOLD}
   ▄████████  ███▄▄▄▄      ▄████████ 
  ███    ███  ███▀▀▀██▄   ███    ███ 
  ███    ███  ███   ███   ███    ███ 
  ███    ███  ███   ███   ███    ███ 
▀███████████  ███   ███ ▀███████████ 
  ███    ███  ███   ███   ███    ███ 
  ███    ███  ███   ███   ███    ███ 
  ███    █▀    ▀█   █▀    ███    █▀  
{C_MAGENTA}{C_BOLD}  ──  ANA NEURAL ASSISTANT (HYBRID SWAHILI CORE)  ──
{C_RESET}"""

# Global configuration
MODEL_ENGINE = "local" # local, groq, or openrouter
MODEL_NAME = "gemma2-swahili"
API_KEY = ""
API_URL = ""
SPEAK_ENABLED = False

SYSTEM_PROMPT = "Wewe ni A.N.A (Ana Neural Assistant), Msaidizi Binafsi wa kidijitali aliyebobea kusaidia mtumiaji kusimamia majukumu, kupanga siku yake, kutatua changamoto za kiufundi, na kutoa ushauri wa kimaisha na kikazi. Unajieleza kwa lugha ya Kiswahili sanifu, chenye adabu, heshima na uelewa mkubwa wa utamaduni wa Afrika Mashariki. Kuwa makini, tayari kuandaa barua pepe, kupanga ratiba za siku, kufanya muhtasari wa nyaraka, na kuleta ufanisi mkubwa katika kila jukumu la mteja wako."

def load_dotenv():
    """Load configuration from local .env file securely without python-dotenv."""
    global SPEAK_ENABLED
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip().strip('"').strip("'")
    
    # Check if voice is globally enabled in .env
    if os.environ.get("SPEAK") == "true":
        SPEAK_ENABLED = True

def load_persona(persona_name="default"):
    """Load dynamic system prompt from a JSON persona profile or override via .env."""
    global SYSTEM_PROMPT
    
    # 1. Check if overridden directly in .env (Highest developer priority)
    env_prompt = os.environ.get("SYSTEM_PROMPT")
    if env_prompt:
        SYSTEM_PROMPT = env_prompt
        print(f"{C_GREEN}[✓] Umetumia System Prompt maalum kutoka '.env'!{C_RESET}")
        return
        
    # 2. Check if a JSON persona profile exists
    persona_path = os.path.join(os.path.dirname(__file__), "personas", f"{persona_name}.json")
    if os.path.exists(persona_path):
        try:
            with open(persona_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                SYSTEM_PROMPT = data.get("prompt", SYSTEM_PROMPT)
                print(f"{C_GREEN}[✓] Persona Inayotumika: {C_BOLD}{data.get('name')}{C_RESET} - {C_GRAY}{data.get('description')}{C_RESET}")
        except Exception as e:
            print(f"{C_YELLOW}[!] Kushindwa kupakia faili la persona: {e}. Inatumia default.{C_RESET}")
    else:
        if persona_name != "default":
            print(f"{C_YELLOW}[!] ONYO: Persona '{persona_name}' haijapatikana. Inatumia default.{C_RESET}")
        print(f"{C_GREEN}[✓] Persona Inayotumika: {C_BOLD}Ana Standard{C_RESET} - {C_GRAY}Msaidizi mkuu wa Swahili.{C_RESET}")

def detect_engine():
    """Determine best engine (Groq, OpenRouter, or Local Ollama) based on env vars."""
    global MODEL_ENGINE, MODEL_NAME, API_KEY, API_URL
    
    groq_key = os.environ.get("GROQ_API_KEY")
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    
    if groq_key:
        MODEL_ENGINE = "groq"
        MODEL_NAME = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
        API_KEY = groq_key
        API_URL = "https://api.groq.com/openai/v1/chat/completions"
        print(f"{C_GREEN}[✓] Mtandao wa Cloud: GROQ API (Kasi ya Juu sana, 0% CPU!){C_RESET}")
        print(f"{C_GRAY}Model: {C_BOLD}{MODEL_NAME}{C_RESET}")
        return True
        
    elif openrouter_key:
        MODEL_ENGINE = "openrouter"
        MODEL_NAME = os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
        API_KEY = openrouter_key
        API_URL = "https://openrouter.ai/api/v1/chat/completions"
        print(f"{C_GREEN}[✓] Mtandao wa Cloud: OPENROUTER FREE API (0% CPU!){C_RESET}")
        print(f"{C_GRAY}Model: {C_BOLD}{MODEL_NAME}{C_RESET}")
        return True
        
    else:
        MODEL_ENGINE = "local"
        MODEL_NAME = "gemma2-swahili"
        print(f"{C_BLUE}[i] Mtandao wa Ndani: OLLAMA (Njia ya Nje ya Mtandao / Offline){C_RESET}")
        return check_local_ollama()

def check_local_ollama():
    """Verify if Ollama service is active and local models are loaded."""
    global MODEL_NAME
    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/tags",
            method="GET"
        )
        with urllib.request.urlopen(req, timeout=2) as response:
            data = json.loads(response.read().decode('utf-8'))
            models = [m['name'] for m in data.get('models', [])]
            
            # Check for direct gemma2-swahili
            if MODEL_NAME in models or f"{MODEL_NAME}:latest" in models:
                print(f"{C_GRAY}Model: {C_BOLD}{MODEL_NAME}{C_RESET}")
                return True
                
            # Fallback to llama3.2 if installed locally
            fallback_models = ["llama3.2:latest", "llama3.2"]
            for fm in fallback_models:
                if fm in models:
                    print(f"{C_YELLOW}[!] ONYO: Model '{MODEL_NAME}' haijapatikana (inapakuliwa kwa sasa).{C_RESET}")
                    print(f"{C_GREEN}[✓] Nimefanikiwa kuanzisha model mbadala ya haraka: '{fm}'!{C_RESET}")
                    MODEL_NAME = fm
                    return True
            
            print(f"{C_YELLOW}[!] ONYO: Model '{MODEL_NAME}' haijapatikana kwenye Ollama.{C_RESET}")
            print(f"{C_GRAY}Tafadhali endesha './setup.sh' kwanza ili kupakua na kusajili model.{C_RESET}\n")
            return False
    except Exception:
        print(f"{C_RED}[X] HITILAFU: Huduma ya Ollama haijawashwa kwenye mfumo wako.{C_RESET}")
        print(f"{C_GRAY}Kama unataka kutumia Cloud API ya bure na kupunguza CPU, weka GROQ_API_KEY kwenye faili la '.env'.{C_RESET}")
        print(f"{C_GRAY}Kama unataka kutumia Ollama ya ndani, washa 'ollama serve' au washa desktop app yake.{C_RESET}\n")
        return False

def speak_text(text):
    """Synthesize Swahili speech. Supports Google Neural Cloud TTS and Local spd-say (female2) / Windows SAPI5."""
    # Clean text to remove markdown formatting, code snippets, etc. for smooth reading
    clean_text = ""
    in_code = False
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        
        # Clean common markdown markup symbols
        line = line.replace("*", "").replace("#", "").replace("- ", "").replace("_", "")
        if line:
            clean_text += " " + line
            
    clean_text = clean_text.strip()
    if not clean_text:
        return
        
    provider = os.environ.get("TTS_PROVIDER", "google").lower()
    system = platform.system()
    
    if provider == "spd-say" or provider == "local":
        if system == "Windows":
            try:
                import subprocess
                # Run silent PowerShell command to synthesize Swahili text using native Windows SAPI5
                ps_text = clean_text.replace("'", "''").replace('"', '`"')
                cmd = f"Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Speak('{ps_text}')"
                subprocess.run(["powershell", "-Command", cmd], check=False)
            except Exception:
                speak_text_google(clean_text)
        else:
            try:
                import subprocess
                # Force spd-say to use espeak-ng with sw+f3 (Swahili female voice variant) on Linux
                subprocess.run(["spd-say", "-o", "espeak-ng", "-y", "sw+f3", "-t", "female2", "-l", "sw"], input=clean_text.encode("utf-8"), check=False)
            except Exception:
                speak_text_google(clean_text)
    elif provider == "elevenlabs" or provider == "eleven":
        speak_text_elevenlabs(clean_text)
    else:
        speak_text_google(clean_text)


def speak_text_google(clean_text):
    """Synthesize Swahili speech using Google Translate TTS API and play natively via VLC."""
    # Split text into chunks because Google TTS has a maximum parameter length limit (~200 characters)
    words = clean_text.split()
    chunks = []
    current_chunk = []
    current_len = 0
    
    for word in words:
        if current_len + len(word) + 1 > 180:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_len = len(word)
        else:
            current_chunk.append(word)
            current_len += len(word) + 1
            
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    temp_file = os.path.join(os.path.dirname(__file__), "temp_tts.mp3")
    system = platform.system()
    
    # Process and play chunks sequentially
    for chunk in chunks:
        if not chunk.strip():
            continue
            
        encoded_query = urllib.parse.quote(chunk)
        url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl=sw&client=tw-ob&q={encoded_query}"
        
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req) as response:
                with open(temp_file, "wb") as f:
                    f.write(response.read())
            
            # Cross-platform silent audio playback via VLC
            if system == "Windows":
                # Check typical default installation folders for VLC on Windows
                vlc_paths = [
                    r"C:\Program Files\VideoLAN\VLC\vlc.exe",
                    r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"
                ]
                vlc_found = None
                for path in vlc_paths:
                    if os.path.exists(path):
                        vlc_found = path
                        break
                if vlc_found:
                    os.system(f'"{vlc_found}" --play-and-exit "{temp_file}" >nul 2>nul')
                else:
                    # Fallback to local Windows speech synthesizer if VLC is not installed
                    import subprocess
                    ps_text = chunk.replace("'", "''").replace('"', '`"')
                    cmd = f"Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Speak('{ps_text}')"
                    subprocess.run(["powershell", "-Command", cmd], check=False)
            else:
                # Linux execution
                os.system(f"cvlc --play-and-exit '{temp_file}' >/dev/null 2>&1")
        except Exception:
            pass
            
    if os.path.exists(temp_file):
        try:
            os.remove(temp_file)
        except Exception:
            pass

def speak_text_elevenlabs(clean_text):
    """Synthesize Swahili speech using ElevenLabs API and play natively via VLC."""
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print(f"{C_YELLOW}[!] ELEVENLABS_API_KEY haipo kwenye faili la .env. Inajielekeza kwa Google...{C_RESET}")
        speak_text_google(clean_text)
        return
        
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "FZGeNF7bE3syeQOynDKC") # Victoria default
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    payload = {
        "text": clean_text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    req_data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        },
        method="POST"
    )
    
    temp_file = os.path.join(os.path.dirname(__file__), "temp_tts.mp3")
    system = platform.system()
    
    try:
        with urllib.request.urlopen(req) as response:
            with open(temp_file, "wb") as f:
                f.write(response.read())
                
        # Play the audio using VLC
        if system == "Windows":
            vlc_paths = [
                r"C:\Program Files\VideoLAN\VLC\vlc.exe",
                r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"
            ]
            vlc_found = None
            for path in vlc_paths:
                if os.path.exists(path):
                    vlc_found = path
                    break
            if vlc_found:
                os.system(f'"{vlc_found}" --play-and-exit "{temp_file}" >nul 2>nul')
            else:
                import subprocess
                ps_text = clean_text.replace("'", "''").replace('"', '`"')
                cmd = f"Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Speak('{ps_text}')"
                subprocess.run(["powershell", "-Command", cmd], check=False)
        else:
            os.system(f"cvlc --play-and-exit '{temp_file}' >/dev/null 2>&1")
            
    except Exception as e:
        print(f"{C_RED}[!] Hitilafu ya ElevenLabs: {e}. Inatumia Google...{C_RESET}")
        speak_text_google(clean_text)
        
    if os.path.exists(temp_file):
        try:
            os.remove(temp_file)
        except Exception:
            pass

def generate_response(messages, stream=True):
    """Query selected engine (Ollama, Groq, or OpenRouter) with stream support and dynamic time injection."""
    
    # 1. Dynamic Prompt Engineering: Inject real-time local date and time context!
    full_messages = messages.copy()
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    
    # Append real-time time awareness to the system prompt
    dynamic_prompt = f"{SYSTEM_PROMPT}\n[Taarifa za Wakati Halisi: Leo ni tarehe {date_str}, saa za eneo lako kwa sasa ni {time_str}. Jibu maswali kwa uelewa kamili wa tarehe na saa hii.]"

    if not any(m.get("role") == "system" for m in full_messages):
        full_messages.insert(0, {"role": "system", "content": dynamic_prompt})

    if MODEL_ENGINE == "local":
        payload = {
            "model": MODEL_NAME,
            "messages": full_messages,
            "stream": stream
        }
        headers = {"Content-Type": "application/json"}
        url = OLLAMA_API_URL
    else:
        payload = {
            "model": MODEL_NAME,
            "messages": full_messages,
            "stream": stream
        }
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        if MODEL_ENGINE == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/Alfaxad/gemma2-swahili-models"
            headers["X-Title"] = "ANA Swahili Neural CLI Core"
        url = API_URL

    req_data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=req_data,
        headers=headers,
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            sys.stdout.write(f"{C_GREEN}{C_BOLD}A.N.A: {C_RESET}{C_CYAN}")
            sys.stdout.flush()
            
            full_response = ""
            
            if not stream:
                res_data = json.loads(response.read().decode('utf-8'))
                if MODEL_ENGINE == "local":
                    content = res_data['message']['content']
                else:
                    content = res_data['choices'][0]['message']['content']
                sys.stdout.write(content + "\n")
                return content
                
            for line in response:
                if line:
                    line_str = line.decode('utf-8').strip()
                    if not line_str:
                        continue
                        
                    if MODEL_ENGINE == "local":
                        chunk = json.loads(line_str)
                        content = chunk.get('message', {}).get('content', '')
                        full_response += content
                        sys.stdout.write(content)
                        sys.stdout.flush()
                    else:
                        if line_str.startswith("data: "):
                            data_content = line_str[6:]
                            if data_content == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_content)
                                content = chunk.get('choices', [{}])[0].get('delta', {}).get('content', '')
                                full_response += content
                                sys.stdout.write(content)
                                sys.stdout.flush()
                            except Exception:
                                pass
            
            sys.stdout.write(f"{C_RESET}\n")
            
            # 2. Text-to-Speech Trigger: If voice output is enabled, speak A.N.A's response!
            if SPEAK_ENABLED:
                speak_text(full_response)
                
            return full_response
            
    except urllib.error.URLError as e:
        print(f"\n{C_RED}[X] Hitilafu ya Mawasiliano ya API: {e}{C_RESET}")
        return ""
    except KeyboardInterrupt:
        print(f"\n{C_YELLOW}[!] Uingiliaji kati umefanyika. Ninasitisha jibu...{C_RESET}")
        return ""

def main():
    global SPEAK_ENABLED
    parser = argparse.ArgumentParser(description="A.N.A Swahili Neural CLI Assistant Core")
    parser.add_argument("prompt", type=str, nargs="?", help="Swahili prompt to execute directly")
    parser.add_argument("-p", "--persona", type=str, default="default", 
                        help="Weka jina la persona ya kupakia (default, mwalimu, mhandisi)")
    parser.add_argument("-s", "--speak", action="store_true", 
                        help="Washa sauti ya A.N.A ili kuongea majibu aloud")
    args = parser.parse_args()

    print(BANNER)
    
    # 1. Load Dynamic Prompt Engineering Configs / Persona
    load_dotenv()
    load_persona(args.persona)
    
    # Override voice option if --speak CLI flag is supplied
    if args.speak:
        SPEAK_ENABLED = True
    
    # 2. Auto detect best engine to protect CPU usage
    if not detect_engine():
        sys.exit(1)
    print()

    if args.prompt:
        messages = [{"role": "user", "content": args.prompt}]
        print(f"{C_YELLOW}{C_BOLD}Swali: {C_RESET}{args.prompt}")
        generate_response(messages, stream=True)
        print()
        sys.exit(0)

    # Interactive Chat Mode
    tts_provider = os.environ.get("TTS_PROVIDER", "google").lower()
    if tts_provider in ["elevenlabs", "eleven"]:
        provider_name = "ElevenLabs Ultra-Realistic (Mwanamke)"
    elif tts_provider == "google":
        provider_name = "Google Cloud Neural (Mwanamke Sanifu)"
    else:
        provider_name = "Local spd-say/SAPI5 (Mwanamke)"
    print(f"{C_GRAY}Mawasiliano salama yameanzishwa. Andika 'exit' au 'ondoka' kumaliza mazungumzo.{C_RESET}")
    print(f"{C_GRAY}Sauti (TTS): {C_BOLD}{'IMEWASHWA (' + provider_name + ')' if SPEAK_ENABLED else 'IMEZIMWA (Andika -s kuwasha)'}{C_RESET}")
    print(f"{C_GRAY}Njia ya CPU: {C_BOLD}{'Inatumia Cloud API (0% CPU)' if MODEL_ENGINE != 'local' else 'Inatumia CPU ya Ndani (100% CPU)'}{C_RESET}\n")
    
    chat_history = []
    
    while True:
        try:
            user_input = input(f"{C_YELLOW}{C_BOLD}Wewe: {C_RESET}")
            if not user_input.strip():
                continue
                
            if user_input.lower() in ['exit', 'quit', 'ondoka', 'kwaheri']:
                print(f"\n{C_MAGENTA}{C_BOLD}A.N.A: Kwaheri! Tutaonana tena.{C_RESET}\n")
                
                # Say goodbye in Swahili if speak is enabled!
                if SPEAK_ENABLED:
                    speak_text("Kwaheri! Tutaonana tena.")
                break
                
            chat_history.append({"role": "user", "content": user_input})
            
            # Query and stream response
            response_text = generate_response(chat_history, stream=True)
            if response_text:
                chat_history.append({"role": "assistant", "content": response_text})
            print()
            
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n{C_MAGENTA}{C_BOLD}A.N.A: Mazungumzo yamefungwa. Kwaheri!{C_RESET}\n")
            if SPEAK_ENABLED:
                speak_text("Mazungumzo yamefungwa. Kwaheri!")
            break

if __name__ == "__main__":
    main()
