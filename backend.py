#!/usr/bin/env python3
# Vodacom Swahili Voice AI Assistant - FastAPI Backend Server
# Zero heavy system dependencies, blazing-fast execution
# Supports Google Swahili Speech-to-Text (STT) & ElevenLabs Victoria Text-to-Speech (TTS)
# Features Mock CRM Database, M-Pesa Ledgers, Security Verification, and Auto-Actions

import os
import sys
import json
import base64
import tempfile
import asyncio
import urllib.request
import urllib.parse
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import speech_recognition as sr

# Initialize FastAPI App
app = FastAPI(
    title="Vodacom Swahili Voice AI Assistant Backend",
    description="FastAPI Neural Engine for Swahili Voice Telecom Customer Care",
    version="1.0.0"
)

# Enable CORS for seamless HTML5 UI integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──  1. CORE CONFIGURATION & CREDENTIAL LOADERS  ──
ENV_DATA = {}
def load_env():
    global ENV_DATA
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    ENV_DATA[k.strip()] = v.strip().strip('"').strip("'")
                    os.environ[k.strip()] = v.strip().strip('"').strip("'")

load_env()

# Retrieve API keys from env
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "FZGeNF7bE3syeQOynDKC") # Victoria

# ──  2. IN-MEMORY CARRIER DATABASES (CRM, LEDGER, NIDA)  ──
vodacom_crm = {
    "255745123456": {
        "msisdn": "255745123456",
        "full_name": "Jane Dinah",
        "nida_number": "19950812-11102-00001-22",
        "sim_status": "ACTIVE",
        "puk_code": "87654321"
    },
    "255788998877": {
        "msisdn": "255788998877",
        "full_name": "Mr Dino",
        "nida_number": "20000101-12345-67890-12",
        "sim_status": "LOCKED",
        "puk_code": "12345678"
    }
}

mpesa_ledger = {
    "255745123456": {
        "msisdn": "255745123456",
        "account_status": "BLOCKED",
        "balance_tsh": 85000.00,
        "last_transaction": "Sent 15,000 Tsh to John"
    },
    "255788998877": {
        "msisdn": "255788998877",
        "account_status": "ACTIVE",
        "balance_tsh": 250000.00,
        "last_transaction": "Received 50,000 Tsh from M-Pesa Agent"
    }
}

# Transaction history log for dynamic display
sms_log = []
escalation_queue = []

# ──  3. BACKGROUND MOCK GATEWAY WORKERS  ──
async def trigger_mock_sms_gateway(msisdn: str, message: str):
    """Asynchronous background worker simulating carrier SMS gateway"""
    await asyncio.sleep(2.0)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{now}] SMS to {msisdn}: '{message}'"
    sms_log.append(log_entry)
    print(f"\033[92m[SMS GATEWAY SUCCESS]\033[0m Sent to {msisdn} -> {message}")

# ──  4. SYSTEM API SERVICE ENDPOINTS  ──

@app.get("/api/crm")
async def get_crm_database():
    """Retrieve full list of active mock CRM profiles"""
    return list(vodacom_crm.values())

@app.get("/api/mpesa")
async def get_mpesa_ledger():
    """Retrieve full list of active M-Pesa ledger configurations"""
    return list(mpesa_ledger.values())

@app.get("/api/sms-logs")
async def get_sms_logs():
    """Retrieve list of dispatched notification logs"""
    return sms_log

@app.get("/api/escalations")
async def get_escalations():
    """Retrieve lists of handoff support events"""
    return escalation_queue

@app.post("/api/reset")
async def reset_databases():
    """Resets mock databases back to locked/blocked states for live demonstration"""
    vodacom_crm["255745123456"]["sim_status"] = "ACTIVE"
    vodacom_crm["255788998877"]["sim_status"] = "LOCKED"
    mpesa_ledger["255745123456"]["account_status"] = "BLOCKED"
    mpesa_ledger["255788998877"]["account_status"] = "ACTIVE"
    sms_log.clear()
    escalation_queue.clear()
    return {"status": "success", "message": "Databases successfully reset to locked state for demo!"}

# ──  5. HIGH-FIDELITY SPEECH-TO-TEXT (STT) LAYER  ──

@app.post("/api/stt")
async def speech_to_text(file: UploadFile = File(...)):
    """
    Accepts raw WAV audio files recorded from browser mic,
    and returns a clean Swahili transcript using Google's Web speech translation.
    """
    suffix = ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_wav:
        temp_wav.write(await file.read())
        temp_wav_path = temp_wav.name

    try:
        r = sr.Recognizer()
        with sr.AudioFile(temp_wav_path) as source:
            # Adjust ambient noise threshold
            r.adjust_for_ambient_noise(source, duration=0.2)
            audio_data = r.record(source)
            
        print("[STT] Transcribing Swahili audio file...")
        text = r.recognize_google(audio_data, language="sw-TZ")
        print(f"[STT SUCCESS] Transcript: '{text}'")
        return {"status": "success", "transcript": text}
    except sr.UnknownValueError:
        return {"status": "error", "message": "Sauti haikueleweka, tafadhali rudia."}
    except Exception as e:
        print(f"[STT ERROR] Failed: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        if os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)

# ──  6. TEXT-TO-SPEECH (TTS) SYNTHESIS LAYER  ──

def tts_google_fallback(text: str) -> bytes:
    """Streams neural-quality Kiswahili audio bytes from Google Cloud TTS API"""
    try:
        encoded_text = urllib.parse.quote(text)
        url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl=sw&client=tw-ob&q={encoded_text}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req) as response:
            return response.read()
    except Exception as e:
        print(f"[TTS Fallback Error] Google Translate TTS failed: {e}")
        return b""

def tts_elevenlabs(text: str) -> bytes:
    """Synthesizes high-fidelity Kiswahili speech using ElevenLabs (Victoria Voice)"""
    if not ELEVENLABS_API_KEY:
        return tts_google_fallback(text)
        
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }
    
    req_data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        },
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            return response.read()
    except Exception as e:
        print(f"[!] ElevenLabs failed: {e}. Switching to Google TTS Fallback...")
        return tts_google_fallback(text)

class TTSRequest(BaseModel):
    text: str

@app.post("/api/tts")
async def text_to_speech(payload: TTSRequest):
    """Processes Swahili text and returns base64-encoded audio bytes for HTML5 playback"""
    try:
        audio_bytes = tts_elevenlabs(payload.text)
        if not audio_bytes:
            raise HTTPException(status_code=500, detail="Voice synthesis failed.")
        b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
        return {"status": "success", "audio_base64": b64_audio}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ──  7. CONVERSATIONAL CHAT ENGINE (LLM + TOOL TRIGGERS)  ──

class ChatRequest(BaseModel):
    message: str
    msisdn: str = "255745123456" # Default test profile (Jane Dinah)
    history: list = []           # Conversation context history

def get_vodacom_system_prompt(msisdn: str) -> str:
    """Dynamically builds time-aware system prompt injecting CRM and Ledger state"""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    
    # Retrieve customer data safely
    crm = vodacom_crm.get(msisdn, {"full_name": "Mteja", "sim_status": "ACTIVE"})
    ledger = mpesa_ledger.get(msisdn, {"account_status": "ACTIVE", "balance_tsh": 0.0})
    
    prompt_path = os.path.join(os.path.dirname(__file__), "personas", "vodacom.json")
    base_prompt = ""
    if os.path.exists(prompt_path):
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                base_prompt = json.load(f).get("prompt", "")
        except Exception:
            pass
            
    if not base_prompt:
        base_prompt = "Wewe ni Ana, mhudumu wa Vodacom."

    # Dynamic system prompt injects state, NIDA details, and database instructions
    dynamic_prompt = f"""{base_prompt}

[TAARIFA ZA MFUMO WA LEO & DATA YA MTEJA]:
- Tarehe ya Leo: {date_str}
- Saa za Sasa: {time_str}
- MSISDN ya Laini Inayotumika: {msisdn}
- Jina la Mteja: {crm['full_name']}
- NIDA Namba ya Mteja: {crm.get('nida_number', 'Haipo')}
- Hali ya SIM Laini: {crm['sim_status']} (PUK Code: {crm.get('puk_code', 'N/A')})
- Hali ya Akaunti ya M-Pesa: {ledger['account_status']}
- Salio la M-Pesa: {ledger['balance_tsh']:,} TZS
- Muamala wa Mwisho: {ledger['last_transaction']}

[MAHUSUSI YA UTENDAJI NA TOOLS]:
Wewe una uwezo wa kuanzisha 'action' (kufungua laini au akaunti) KAMA TU maelezo ya mteja yamethibitishwa.
Ukitaka kufungua M-Pesa ya mteja baada ya kuhakiki kwa usahihi jina, NIDA namba, na maelezo ya muamala wake wa mwisho, lazima uandike mwishoni mwa jibu lako tagi hii ya kipekee ili mfumo wa backend uisome na kufanya mabadiliko ya database:
`ACTION_TRIGGER:UNLOCK_MPESA:{msisdn}`

Ukitaka kufungua SIM ya mteja iliyofungwa baada ya kuhakiki PUK code au NIDA, andika tagi hii:
`ACTION_TRIGGER:UNLOCK_SIM:{msisdn}`

Kama mteja anafanya ghasia, ameshindwa kuhakiki maelezo mara 3 au anataka mhudumu wa kibinadamu, andika tagi hii kumuhamisha:
`ACTION_TRIGGER:ESCALATE_HUMAN:{msisdn}`
"""
    return dynamic_prompt

def query_groq_llm(messages: list) -> str:
    """Queries Groq Cloud API synchronously with fallback options"""
    if not GROQ_API_KEY:
        # Standard default offline simulation response
        return "Samahani, GROQ_API_KEY haijawekwa kwenye .env. Tafadhali sanikisha mfumo kikamilifu."

    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "messages": messages,
        "temperature": 0.3
    }
    
    req_data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data['choices'][0]['message']['content']
    except Exception as e:
        print(f"[LLM ERROR] Groq API call failed: {e}")
        return "Samahani, mtandao wangu wa kiakili una shida kwa sasa. Tafadhali jaribu tena baada ya muda mfupi."

@app.post("/api/chat")
async def chat_interaction(payload: ChatRequest):
    """
    Processes chat conversations, checks tool triggers, alters databases,
    dispatches SMS alerts, and compiles final Swahili responses.
    """
    msisdn = payload.msisdn
    user_message = payload.message
    
    # 1. Compile conversational context
    system_prompt = get_vodacom_system_prompt(msisdn)
    messages = [{"role": "system", "content": system_prompt}]
    
    # Append past conversational history
    for item in payload.history:
        messages.append(item)
    messages.append({"role": "user", "content": user_message})
    
    # 2. Get LLM response
    llm_raw_response = query_groq_llm(messages)
    
    # 3. Scan for active tool/action triggers
    action_executed = None
    processed_response = llm_raw_response
    
    if "ACTION_TRIGGER:UNLOCK_MPESA" in llm_raw_response:
        action_executed = "UNLOCK_MPESA"
        # Update Database
        if msisdn in mpesa_ledger:
            mpesa_ledger[msisdn]["account_status"] = "ACTIVE"
        # Remove tag from text output to keep display clean
        processed_response = processed_response.replace(f"ACTION_TRIGGER:UNLOCK_MPESA:{msisdn}", "").strip()
        # Fire background SMS confirmation
        crm = vodacom_crm.get(msisdn, {"full_name": "Mteja"})
        asyncio.create_task(
            trigger_mock_sms_gateway(
                msisdn, 
                f"Habari {crm['full_name']}, huduma yako ya M-Pesa kwenye laini {msisdn} imefunguliwa kwa mafanikio. Asante kwa kuchagua Vodacom, Pamoja Tunaweza!"
            )
        )
        
    elif "ACTION_TRIGGER:UNLOCK_SIM" in llm_raw_response:
        action_executed = "UNLOCK_SIM"
        if msisdn in vodacom_crm:
            vodacom_crm[msisdn]["sim_status"] = "ACTIVE"
        processed_response = processed_response.replace(f"ACTION_TRIGGER:UNLOCK_SIM:{msisdn}", "").strip()
        crm = vodacom_crm.get(msisdn, {"full_name": "Mteja"})
        asyncio.create_task(
            trigger_mock_sms_gateway(
                msisdn,
                f"Habari {crm['full_name']}, laini yako ya simu {msisdn} imefunguliwa kwa ufanisi. Asante kwa kuchagua Vodacom!"
            )
        )
        
    elif "ACTION_TRIGGER:ESCALATE_HUMAN" in llm_raw_response:
        action_executed = "ESCALATE_HUMAN"
        processed_response = processed_response.replace(f"ACTION_TRIGGER:ESCALATE_HUMAN:{msisdn}", "").strip()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        escalation_queue.append({
            "msisdn": msisdn,
            "timestamp": now,
            "status": "QUEUED",
            "transcript_summary": f"User requested agent or failed security checks. Input: '{user_message}'"
        })
        
    # Clean up empty lines or trailing formatting
    processed_response = processed_response.strip("`").strip()

    # 4. Generate vocal audio stream of response text
    audio_bytes = tts_elevenlabs(processed_response)
    b64_audio = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else ""
    
    return {
        "status": "success",
        "response_text": processed_response,
        "audio_base64": b64_audio,
        "action": action_executed,
        "db_states": {
            "sim_status": vodacom_crm.get(msisdn, {}).get("sim_status"),
            "account_status": mpesa_ledger.get(msisdn, {}).get("account_status")
        }
    }

# ──  8. COMBINED MULTI-MODAL AUDIO ROUNDTRIP ROUTE  ──

@app.post("/api/chat/voice")
async def voice_chat_endpoint(file: UploadFile = File(...), msisdn: str = Form("255745123456"), history_json: str = Form("[]")):
    """
    Ultimate multi-modal roundtrip route:
    Accepts WAV file from UI mic -> Converts speech to Swahili text (Google STT)
    -> Conversations with Llama LLM Core -> Triggers DB updates -> Synthesizes ElevenLabs audio
    -> Returns everything in a single HTTP request!
    """
    # 1. Transcribe WAV audio using our clean STT engine
    stt_res = await speech_to_text(file)
    if stt_res.get("status") == "error":
        # Voice not recognized - synthesize error message
        err_msg = stt_res.get("message", "Samahani, sauti yako haikueleweka. Tafadhali rudia.")
        audio_bytes = tts_elevenlabs(err_msg)
        b64_audio = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else ""
        return {
            "status": "stt_error",
            "transcript": "",
            "response_text": err_msg,
            "audio_base64": b64_audio,
            "action": None
        }
        
    transcript = stt_res.get("transcript", "")
    
    # 2. Parse context history
    try:
        history = json.loads(history_json)
    except Exception:
        history = []
        
    # 3. Trigger chat logic using the transcript
    chat_payload = ChatRequest(message=transcript, msisdn=msisdn, history=history)
    chat_res = await chat_interaction(chat_payload)
    
    # Include the captured transcript so frontend can render customer bubble
    chat_res["transcript"] = transcript
    return chat_res

# ──  9. RUN SERVER LAUNCHER  ──
if __name__ == "__main__":
    import uvicorn
    # Read port from env or fallback to standard 8000
    port = int(os.environ.get("BACKEND_PORT", 8000))
    print(f"[*] Kuanzisha Vodacom Swahili AI Assistant Backend kwenye port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
