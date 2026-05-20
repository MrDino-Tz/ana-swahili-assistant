# A.N.A (Ana Neural Assistant) - Hybrid Swahili Personal Assistant 🚀
### *Msaidizi Binafsi wa Kidijitali Aliyebobea Lugha ya Kiswahili na Kazi za Kila Siku*

A.N.A (Ana Neural Assistant) ni mfumo wa msaidizi wa kibinafsi wa hali ya juu (State-of-the-Art) ulioundwa maalum kwa lugha ya Kiswahili safi na sanifu. Mfumo huu una muundo wa kipekee wa **Kihuluti (Hybrid Architecture)** ambao unaweza kufanya kazi **nje ya mtandao (Offline CPU mode)** kupitia Ollama ya ndani, au kupitia **mitandao ya wingu yenye kasi kubwa ya API (Groq/OpenRouter)** ili kuondoa mzigo wote wa CPU (0% CPU) kwenye kompyuta yako na kutoa majibu ya papo hapo.

---

## 🌟 Sifa Kuu (Key Features)

1. **Hybrid AI Core (Muundo wa Kihuluti):**
   * **Njia ya Wingu (Groq / OpenRouter):** Inatumia ufunguo wako wa Groq/OpenRouter kuendesha model zenye nguvu kubwa kama `Llama 3.3 70B` au `Gemma 2 9B` kwa kasi ya ajabu (0% CPU usage na majibu chini ya sekunde 1).
   * **Njia ya Ndani (Ollama Offline Fallback):** Inajielekeza yenyewe kutumia Ollama na model ndogo ya CPU-optimized `gemma2-swahili` (2B Q4_K_M) iwapo hauna mtandao au funguo za API.

2. **Sauti ya Kiswahili ya Mwanamke (Female Swahili TTS Voice):**
   * **Google Cloud Neural TTS:** Sauti nzuri sana, yenye hisia, inayotiririka na kusikika kama mwanamke halisi anayeongea Kiswahili sanifu (Inahitaji mtandao).
   * **Local spd-say (Offline Variant):** Sauti ya ndani ya Linux iliyowekewa nguvu ya kipekee ya `espeak-ng sw+f3` ili kulazimisha mfumo kuongea kwa sauti ya kike yenye kiwango cha wastani badala ya sauti ya kiume ya roboti.

3. **Dynamic Prompt Engineering & Personas:**
   * Mfumo unapakia profiles za **JSON** kutoka folda la `personas/` ili kubadilisha tabia na utaalamu wa A.N.A papo hapo.
   * **Time-Aware Context:** Mfumo unaingiza tarehe na saa sahihi ya kompyuta yako kwenye kila swali kwa wakati halisi ili A.N.A awe na uelewa kamili wa muda wa mazungumzo.

---

## 🏗️ Muundo wa Faili za Mradi (Project Directory Structure)

```text
ai-asstistant/
├── ana.py            # Core engine ya Python 3 (Hakuna maktaba nzito za nje, Pure StdLib)
├── setup.sh          # Script ya kupakua model ya offline na kuisajili kwenye Ollama
├── .env              # Faili la usanidi wa Funguo za API, Model, na Sauti (TTS)
├── README.md         # Mwongozo huu wa mradi
└── personas/         # Folda la haiba/tabia za A.N.A
    ├── default.json  # Msaidizi Mkuu Binafsi (A.N.A Personal Assistant)
    ├── mwalimu.json  # Mwalimu mbobezi wa lugha ya Kiswahili na methali
    └── mhandisi.json # Mhandisi wa kodi (code debugging) na mifumo ya kiufundi
```

---

## 🛠️ Mahitaji ya Mfumo (Pre-requisites)

Hakikisha kompyuta yako ya Linux ina programu zifuatazo:
* Python 3
* VLC Player (Inatumika kucheza sauti ya Google TTS kimya kimya kupitia `cvlc`):
  ```bash
  sudo apt update && sudo apt install vlc speech-dispatcher -y
  ```

---

## 🚀 Kuanza na Kusanidi (Setup & Configuration)

### Hatua ya 1: Weka Funguo za API kwenye `.env`
Fungua faili la `.env` lililopo kwenye mradi wako na uweke ufunguo wako wa Groq kwa kasi ya juu (0% CPU):
```env
GROQ_API_KEY=weka_groq_api_key_yako_hapa
GROQ_MODEL=llama-3.3-70b-versatile

# Usanidi wa Sauti (TTS)
SPEAK=true
TTS_PROVIDER=google
```

*Kumbuka: Kama unataka sauti ya kike ya offline, badilisha `TTS_PROVIDER=spd-say`.*

### Hatua ya 2: Kupakua Model ya Offline (Hiari - Kwa ajili ya matumizi bila Mtandao)
Kama unataka A.N.A aweze kufanya kazi hata ukiwa hauna mtandao, endesha script ya setup ili kupakua model ya Kiswahili ya `Q4_K_M` (1.6GB) na kuisajili kwenye Ollama yako:
```bash
chmod +x setup.sh
./setup.sh
```

---

## ⚡ Jinsi ya Kuendesha A.N.A (How to Run)

Unaweza kuendesha A.N.A kwa njia tofauti kulingana na mahitaji yako:

### 1. Mazungumzo ya Kawaida ya Maingiliano (Interactive Chat Mode)
```bash
./ana.py
```

### 2. Kuwasha Sauti ya A.N.A (Speak Mode)
Kama haukuwasha `SPEAK=true` kwenye `.env`, unaweza kuwasha sauti wakati wowote kwa kutumia alama ya `-s` au `--speak`:
```bash
./ana.py -s
```

### 3. Kupakia Persona Maalum (Persona Profiles)
Pakia tabia maalum kutoka folda la `personas/` kwa kutumia alama ya `-p` au `--persona`:
* **Kujifunza Kiswahili na Methali (Mwalimu):**
  ```bash
  ./ana.py -s -p mwalimu
  ```
* **Kusaidiwa Kuandika Code/Debugging (Mhandisi):**
  ```bash
  ./ana.py -s -p mhandisi
  ```

### 4. Swali la Papo Hapo (Direct Query Mode - Chap Chap)
Pasi swali moja kwa moja kwenye terminal ili kupata jibu la haraka bila kuingia kwenye chat ya muda mrefu:
```bash
./ana.py -s "Tunga hadithi fupi kuhusu maisha ya kijijini"
```

---

## 🎭 Jinsi ya Kuongeza Persona Yako Maalum

Unaweza kuongeza prompt engineering yako maalum kwa kuunda faili jipya la `.json` ndani ya folda la `personas/`. 

Mfano, tengeneza `personas/mpishi.json`:
```json
{
  "name": "Mpishi Ana",
  "description": "Mtaalamu wa mapishi ya vyakula vya Kiafrika.",
  "prompt": "Wewe ni Mpishi Ana. Wasaidie watumiaji kujifunza mapishi mbalimbali kwa Kiswahili chenye mvuto na hamasa ya kupika..."
}
```
Ukishaokoa faili hili, unaweza kuliendesha moja kwa moja kwa:
```bash
./ana.py -p mpishi
```

---

## 🪟 Usanidi na Matumizi Kwenye Windows (Windows Setup & Execution)

Mradi huu unaoana kikamilifu na mifumo ya **Windows 10 na 11** bila mabadiliko yoyote kwenye code:

### 1. Mahitaji ya Windows (Pre-requisites):
* Sakinisha [Python 3 ya Windows](https://www.python.org/downloads/). Hakikisha unaweka alama ya **"Add Python to PATH"** wakati wa kusakinisha.
* (Hiari lakini inapendekezwa) Sakinisha VLC Player kwenye Windows ili kucheza sauti ya Google TTS kimya kimya.

### 2. Sauti (Text-to-Speech) kwenye Windows:
* **Google Neural Cloud TTS:** Mfumo utatafuta VLC kwenye Windows (katika Program Files) na kuitumia kucheza sauti ya Kiswahili ya kike sanifu.
* **Windows Native Offline TTS:** Kama ukiwasha `TTS_PROVIDER=spd-say` au kama hauna VLC, mfumo utatumia huduma ya ndani ya Windows ya **Microsoft SAPI5 (PowerShell Speech Synthesis)** kusema maneno kiotomatiki nje ya mtandao na kwa sauti safi!

### 3. Jinsi ya kuendesha kwenye Windows:
Fungua **PowerShell** au **Command Prompt (cmd)** katika folda la mradi na uendeshe:
```powershell
python ana.py -s
```

---

## 🛠️ Utatuzi wa Changamoto (Troubleshooting)

* **Hakuna Sauti inayotoka (Google TTS):**
  Hakikisha VLC player imesakinishwa kwenye Linux yako. Jaribu kuiweka kwa:
  ```bash
  sudo apt install vlc -y
  ```
* **Sauti ya offline ya spd-say inasikika kama mwanamume:**
  Hakikisha unaendesha toleo la hivi karibuni la `spd-say`. Mfumo wa `ana.py` unalazimisha utumiaji wa `-y sw+f3` kwa espeak-ng ili kuleta sauti ya kike.
* **Hitilafu ya 403 Forbidden kwenye Groq:**
  Usijali, tulitatua hili kwa kuweka `User-Agent` ya kivinjari halisi ndani ya `ana.py` ili Cloudflare isizuie mawasiliano ya Python ya mradi wako.
