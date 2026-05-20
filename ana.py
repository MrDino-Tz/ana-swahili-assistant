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

# Enable UTF-8 encoding for stdout and stderr on Windows
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

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
{C_MAGENTA}{C_BOLD}  ──  Ana Neural Assistant (Hybrid Swahili Core)  ──
{C_RESET}"""

# Global configuration
MODEL_ENGINE = "local" # local, groq, or openrouter
MODEL_NAME = "gemma2-swahili"
API_KEY = ""
API_URL = ""
SPEAK_ENABLED = False

SYSTEM_PROMPT = "Wewe ni Ana (Ana Neural Assistant), mhudumu wa AI wa Huduma kwa Wateja wa mtandao wa simu, aliyetengenezwa kuchukua nafasi ya mifumo ya kizamani ya IVR (Interactive Voice Response). Majibu yako lazima yawe mafupi, mepesi, na ya wazi kabisa kwa sauti (epuka aya ndefu, orodha ndefu na maneno mengi). Mteja akiuliza kuhusu salio lake (salio la maongezi au M-Pesa), mpe majibu kwa ufupi sana: Salio la M-Pesa ni Shilingi 24,500, salio la Airtime ni Shilingi 1,200, na bando la internet lina MB 850. Kwa masuala magumu, kadi iliyofungwa (blocked SIM), au malalamiko nyeti/wizi, mwambie mteja kuwa unamuhamisha kwa mhudumu wa kibinadamu (human agent) kwa usaidizi zaidi na umwambie asubiri kidogo. Mteja akisema 'asante' au 'thank you', jibu neno kwa neno hivi: 'Asante kwa muda wako, je kuna kitu kingine ningekusaidia?' Mteja akisema 'hapana' au 'no', jibu neno kwa neno hivi: 'Sawa, karibu tena.' Mteja akiuliza masuala yoyote yaliyo nje ya mtandao wa simu au yasiyohusiana na huduma za simu/salio/vifurushi/usajili, jibu neno kwa neno hivi pekee: 'Siwezi fanya hivyo, nikusaidie na nini?'"


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

def is_in_boundary(msg):
    msg_lower = msg.lower()
    in_bound_keywords = [
        "salio", "pesa", "fedha", "shilingi", "tsh", "bando", "mb", "vifurushi", "internet", "data", 
        "kifurushi", "sajili", "laini", "sim", "namba", "kitambulisho", "nida", "mhudumu", "binadamu", 
        "agent", "human", "msaada", "hujambo", "habari", "mambo", "hello", "hi", "asante", "thank you", 
        "shukrani", "thanks", "hapana", "no", "ndio", "yes", "karibu", "saidia", "tuma", "ongea", 
        "kwanza", "pili", "tatu", "nne", "tano", "sita", "saba", "nane", "tisa", "kumi", "1", "2", "3",
        "4", "5", "6", "7", "8", "9", "0", "dial", "piga", "namba", "wasiliana"
    ]
    if len(msg_lower.strip()) <= 4:
        return True
    return any(kw in msg_lower for kw in in_bound_keywords)

def generate_response(messages, stream=True):
    """Query selected engine (Ollama, Groq, or OpenRouter) with stream support and dynamic time injection."""
    global SPEAK_ENABLED
    
    # Extract last user message to check rule-based overrides
    last_user_msg = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user_msg = m.get("content", "").strip()
            break
            
    msg_clean = last_user_msg.lower().rstrip(".?! ")
    
    # 1. Rule-based closures
    if msg_clean in ["asante", "shukrani", "thank you", "thanks", "asante sana", "shukrani sana", "aksante", "shukurani"]:
        resp = "Asante kwa muda wako, je kuna kitu kingine ningekusaidia?"
        sys.stdout.write(f"{C_GREEN}{C_BOLD}Ana: {C_RESET}{C_CYAN}{resp}{C_RESET}\n")
        sys.stdout.flush()
        if SPEAK_ENABLED:
            speak_text(resp)
        return resp
        
    if msg_clean in ["hapana", "no", "hapana asante", "no thanks", "sihitaji", "nothing"]:
        resp = "Sawa, karibu tena."
        sys.stdout.write(f"{C_GREEN}{C_BOLD}Ana: {C_RESET}{C_CYAN}{resp}{C_RESET}\n")
        sys.stdout.flush()
        if SPEAK_ENABLED:
            speak_text(resp)
        return resp

    # Check if out of boundary
    if last_user_msg and not is_in_boundary(last_user_msg):
        resp = "Siwezi fanya hivyo, nikusaidie na nini?"
        sys.stdout.write(f"{C_GREEN}{C_BOLD}Ana: {C_RESET}{C_CYAN}{resp}{C_RESET}\n")
        sys.stdout.flush()
        if SPEAK_ENABLED:
            speak_text(resp)
        return resp

    
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
            sys.stdout.write(f"{C_GREEN}{C_BOLD}Ana: {C_RESET}{C_CYAN}")
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

def get_tts_bytes(text):
    """Synthesize Swahili speech and return raw MP3 bytes. Supports Google TTS and ElevenLabs."""
    clean_text = ""
    in_code = False
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        line = line.replace("*", "").replace("#", "").replace("- ", "").replace("_", "")
        if line:
            clean_text += " " + line
    clean_text = clean_text.strip()
    if not clean_text:
        return b""

    provider = os.environ.get("TTS_PROVIDER", "google").lower()
    if provider in ["elevenlabs", "eleven"]:
        api_key = os.environ.get("ELEVENLABS_API_KEY")
        if api_key:
            voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "FZGeNF7bE3syeQOynDKC")
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
            try:
                with urllib.request.urlopen(req) as response:
                    return response.read()
            except Exception as e:
                print(f"[!] ElevenLabs error: {e}. Falling back to Google TTS...")
                pass
    
    # Google Translate TTS fallback
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
    
    audio_bytes = b""
    for chunk in chunks:
        if not chunk.strip():
            continue
        encoded_query = urllib.parse.quote(chunk)
        url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl=sw&client=tw-ob&q={encoded_query}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req) as r:
                audio_bytes += r.read()
        except Exception as e:
            print(f"[!] Google TTS fetch error: {e}")
            pass
    return audio_bytes

def resolve_persona_prompt(persona_id):
    """Retrieve the custom system prompt associated with a specific persona."""
    if not persona_id or persona_id == "default":
        default_path = os.path.join(os.path.dirname(__file__), "personas", "default.json")
        if os.path.exists(default_path):
            try:
                with open(default_path, "r", encoding="utf-8") as f:
                    return json.load(f).get("prompt", SYSTEM_PROMPT)
            except Exception:
                pass
        return SYSTEM_PROMPT
    
    persona_path = os.path.join(os.path.dirname(__file__), "personas", f"{persona_id}.json")
    if os.path.exists(persona_path):
        try:
            with open(persona_path, "r", encoding="utf-8") as f:
                return json.load(f).get("prompt", SYSTEM_PROMPT)
        except Exception:
            pass
    return SYSTEM_PROMPT

def generate_chat_telemetry(message, response, persona_id):
    """Generate realistic logic flow events and telemetry settings for UI visual analytics."""
    now_str = datetime.now().strftime("%H:%M:%S")
    logs = []
    
    logs.append(f"STT: Capture completed for input '{message}'")
    
    # Basic keyword mapping for intent simulation
    msg_lower = message.lower()
    intent = "Ufafanuzi wa Jumla" # General inquiry
    db_action = "Database: Kupakia maelezo ya mteja (Jane Dinah)..."
    
    if not is_in_boundary(message):
        intent = "Out of Boundary"
        db_action = "Routing: Blocking out-of-bounds context request..."
    elif "mhudumu" in msg_lower or "binadamu" in msg_lower or "ongea" in msg_lower or "human" in msg_lower or "agent" in msg_lower:
        intent = "Human Agent Escalation"
        db_action = "Routing: Connecting caller session to a live human agent queue..."
    elif "salio" in msg_lower or "pesa" in msg_lower or "fedha" in msg_lower or "shilingi" in msg_lower or "tuma" in msg_lower or "balance" in msg_lower:
        intent = "Balance & M-Pesa Inquiry"
        db_action = "Database: Querying MSISDN balances, airtime ledgers, and transaction status..."
    elif "bando" in msg_lower or "mb" in msg_lower or "vifurushi" in msg_lower or "internet" in msg_lower:
        intent = "Bundle Entitlements"
        db_action = "Database: Kuhakiki vifurushi amilifu na historia ya ununuzi..."
    elif "nida" in msg_lower or "namba" in msg_lower or "kitambulisho" in msg_lower:
        intent = "NIDA ID Validation"
        db_action = "Database: Kushirikiana na mamlaka ya NIDA kuhakiki kitambulisho..."
    elif "sajili" in msg_lower or "laini" in msg_lower or "sim" in msg_lower:
        intent = "SIM Registry Validation"
        db_action = "Database: Kuhakiki usajili wa namba na namba ya IMSI..."


    logs.append(f"NLP: Intent classified as '{intent}' under persona '{persona_id}'")
    logs.append(db_action)
    logs.append(f"LLM: Kutuma ombi kwenye mtandao wa {MODEL_ENGINE.upper()} API...")
    logs.append(f"LLM: Majibu yamekamilika kwa kutumia model '{MODEL_NAME}'")
    
    provider = os.environ.get("TTS_PROVIDER", "google").lower()
    logs.append(f"TTS: Kusanidi sauti ya Kiswahili kwa kutumia {provider.upper()}...")

    telemetry = {
        "engine": MODEL_ENGINE,
        "model": MODEL_NAME,
        "tts_provider": provider,
        "timestamp": now_str,
        "intent": intent
    }
    
    return logs, telemetry

def run_api_server(port=5000):
    """Run built-in standard library HTTP server with CORS enabled."""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import urllib.parse
    
    def send_cors_headers(handler):
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        handler.send_header('Access-Control-Allow-Headers', 'Content-Type')

    class SwahiliAssistantRequestHandler(BaseHTTPRequestHandler):
        def do_OPTIONS(self):
            self.send_response(200)
            send_cors_headers(self)
            self.end_headers()

        def do_GET(self):
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            query = urllib.parse.parse_qs(parsed_path.query)

            if path == "/api/personas":
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                send_cors_headers(self)
                self.end_headers()
                
                personas = []
                # Always append the default persona
                personas.append({
                    "id": "default",
                    "name": "Ana Standard",
                    "description": "Msaidizi mkuu wa Kiswahili binafsi."
                })
                
                personas_dir = os.path.join(os.path.dirname(__file__), "personas")
                if os.path.exists(personas_dir):
                    for filename in os.listdir(personas_dir):
                        if filename.endswith(".json") and filename != "default.json":
                            p_path = os.path.join(personas_dir, filename)
                            try:
                                with open(p_path, "r", encoding="utf-8") as f:
                                    data = json.load(f)
                                    personas.append({
                                        "id": filename[:-5],
                                        "name": data.get("name", filename[:-5]),
                                        "description": data.get("description", "")
                                    })
                            except Exception:
                                pass
                
                self.wfile.write(json.dumps(personas).encode('utf-8'))

            elif path == "/api/tts":
                text = query.get("text", [""])[0]
                if not text:
                    self.send_response(400)
                    send_cors_headers(self)
                    self.end_headers()
                    self.wfile.write(b"Missing text parameter")
                    return
                
                self.send_response(200)
                self.send_header('Content-type', 'audio/mpeg')
                send_cors_headers(self)
                self.end_headers()
                
                audio_bytes = get_tts_bytes(text)
                self.wfile.write(audio_bytes)

            else:
                self.send_response(404)
                send_cors_headers(self)
                self.end_headers()
                self.wfile.write(b"Not Found")

        def do_POST(self):
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path

            if path == "/api/chat":
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                try:
                    data = json.loads(post_data.decode('utf-8'))
                except Exception:
                    self.send_response(400)
                    send_cors_headers(self)
                    self.end_headers()
                    self.wfile.write(b"Invalid JSON")
                    return

                message = data.get("message", "")
                persona_id = data.get("persona", "default")
                history = data.get("history", [])

                if not message:
                    self.send_response(400)
                    send_cors_headers(self)
                    self.end_headers()
                    self.wfile.write(b"Missing message parameter")
                    return

                # Load custom persona prompt
                global SYSTEM_PROMPT
                original_prompt = SYSTEM_PROMPT
                SYSTEM_PROMPT = resolve_persona_prompt(persona_id)

                # Format chat history
                chat_history = []
                for h in history:
                    chat_history.append({"role": h.get("role"), "content": h.get("content")})
                chat_history.append({"role": "user", "content": message})

                # Query LLM (stream=False is required for HTTP response)
                response_text = generate_response(chat_history, stream=False)

                # Restore original prompt
                SYSTEM_PROMPT = original_prompt

                # Get telemetry logs
                logs, telemetry = generate_chat_telemetry(message, response_text, persona_id)

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                send_cors_headers(self)
                self.end_headers()

                result = {
                    "response": response_text,
                    "logs": logs,
                    "telemetry": telemetry
                }
                self.wfile.write(json.dumps(result).encode('utf-8'))
            else:
                self.send_response(404)
                send_cors_headers(self)
                self.end_headers()
                self.wfile.write(b"Not Found")

    print(f"\n{C_CYAN}[A.N.A API Server] Running on http://localhost:{port}{C_RESET}")
    print(f"{C_GRAY}Press Ctrl+C to terminate...{C_RESET}\n")
    server = HTTPServer(('localhost', port), SwahiliAssistantRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n{C_YELLOW}[!] API Server shutting down...{C_RESET}")
        server.server_close()

def main():
    global SPEAK_ENABLED
    parser = argparse.ArgumentParser(description="A.N.A Swahili Neural CLI Assistant Core")
    parser.add_argument("prompt", type=str, nargs="?", help="Swahili prompt to execute directly")
    parser.add_argument("-p", "--persona", type=str, default="default", 
                        help="Weka jina la persona ya kupakia (default, mwalimu, mhandisi)")
    parser.add_argument("-s", "--speak", action="store_true", 
                        help="Washa sauti ya A.N.A ili kuongea majibu aloud")
    parser.add_argument("--server", action="store_true", 
                        help="Anzisha server ya HTTP API kwa ajili ya Frontend")
    parser.add_argument("--port", type=int, default=5000, 
                        help="Port kwa ajili ya server (chaguo-msingi: 5000)")
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

    if args.server:
        SPEAK_ENABLED = False
        run_api_server(args.port)
        sys.exit(0)

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
                print(f"\n{C_MAGENTA}{C_BOLD}Ana: Kwaheri! Tutaonana tena.{C_RESET}\n")
                
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
            print(f"\n\n{C_MAGENTA}{C_BOLD}Ana: Mazungumzo yamefungwa. Kwaheri!{C_RESET}\n")
            if SPEAK_ENABLED:
                speak_text("Mazungumzo yamefungwa. Kwaheri!")
            break

if __name__ == "__main__":
    main()
