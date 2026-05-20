'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Home, History, Mic, Keyboard, Loader2 } from 'lucide-react';
import clsx from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs));
}

// Components
const GlassCard = ({ children, className, active = false }: { children: React.ReactNode; className?: string; active?: boolean }) => {
  return (
    <div
      className={cn(
        "relative rounded-xl overflow-hidden bg-[#262b36]/40 backdrop-blur-[20px] transition-all duration-300",
        active ? "border border-[#e60000]/30 shadow-[0_0_20px_rgba(230,0,0,0.15)]" : "border border-white/5",
        className
      )}
    >
      <div className="relative z-10 w-full h-full p-4 lg:p-5">
        {children}
      </div>
    </div>
  );
};

interface LogItem {
  timestamp: string;
  text: string;
}

export default function ANAApp() {
  const [activeTab, setActiveTab] = useState<'home' | 'activity'>('home');
  const [isListening, setIsListening] = useState(false);
  const [transcription, setTranscription] = useState<string>('');
  const [response, setResponse] = useState<string>('Karibu huduma kwa wateja. Bonyeza kitufe cha MIC hapo chini ili kuanza.');
  const [isLoading, setIsLoading] = useState(false);
  const [textInput, setTextInput] = useState('');
  const [showTextInput, setShowTextInput] = useState(false);
  const [hasGreeted, setHasGreeted] = useState(false);

  // Audio state
  const [audioElement, setAudioElement] = useState<HTMLAudioElement | null>(null);

  const selectedPersona = 'default';

  // Refs to avoid stale closures in web speech listeners and eliminate double-triggering
  const finalTranscriptRef = React.useRef('');
  const hasSentRef = React.useRef(false);
  const handleSendRef = React.useRef<any>(null);

  // Logs & Telemetry
  const [logs, setLogs] = useState<LogItem[]>([
    { timestamp: '14:22:01', text: 'STT: System initialized successfully.' },
    { timestamp: '14:22:03', text: 'NLP: Awaiting user Swahili voice input or manual text entry...' }
  ]);

  const [telemetry, setTelemetry] = useState<Record<string, any>>({
    name: 'Jane Dinah',
    msisdn: '+255 754 *** 123',
    nida_status: 'VERIFIED',
    account_level: 'Tier_2',
    sim_status: 'ACTIVE',
    roaming: false,
    last_tower_id: 'T-DAR-091',
    auth_vector: 'AES-256',
    intent: 'None',
    engine: 'groq',
    model: 'llama-3.3-70b-versatile',
    tts_provider: 'google'
  });

  // Pulse effect states for transcription
  const [transcriptionDots, setTranscriptionDots] = useState('');

  useEffect(() => {
    const interval = setInterval(() => {
      setTranscriptionDots(prev => prev.length >= 3 ? '' : prev + '.');
    }, 500);
    return () => clearInterval(interval);
  }, []);

  // Keep handleSendRef updated with latest handleSend
  useEffect(() => {
    handleSendRef.current = handleSend;
  }, [handleSend]);

  const handleMicClick = () => {
    if (!hasGreeted) {
      if (audioElement) {
        audioElement.pause();
      }

      const greetText = "Karibu huduma kwa wateja, nikusaidie nini?";
      setResponse(greetText);
      setIsLoading(true);
      setHasGreeted(true);

      const audioUrl = `/api/tts?text=${encodeURIComponent(greetText)}`;
      const newAudio = new Audio(audioUrl);
      setAudioElement(newAudio);

      newAudio.play().catch(err => {
        console.error("Audio playback blocked/interrupted:", err);
        setIsLoading(false);
        setIsListening(true);
      });

      newAudio.onended = () => {
        setIsLoading(false);
        setIsListening(true);
      };
    } else {
      if (isLoading) {
        if (audioElement) {
          audioElement.pause();
        }
        setIsLoading(false);
      } else {
        setIsListening(prev => !prev);
      }
    }
  };

  // Web Speech API
  const [recognition, setRecognition] = useState<any>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        const rec = new SpeechRecognition();
        rec.continuous = false;
        rec.interimResults = true;
        rec.lang = 'sw-TZ'; // Swahili - Tanzania / Kenya

        rec.onstart = () => {
          setIsListening(true);
          setTranscription('Ninakusikiliza, ongea sasa...');
          setResponse('');
          finalTranscriptRef.current = '';
          hasSentRef.current = false;
        };

        rec.onresult = (event: any) => {
          let interimTranscript = '';
          let finalTranscript = '';

          for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
              finalTranscript += event.results[i][0].transcript;
            } else {
              interimTranscript += event.results[i][0].transcript;
            }
          }

          if (finalTranscript) {
            finalTranscriptRef.current = finalTranscript;
            setTranscription(finalTranscript);
          } else if (interimTranscript) {
            setTranscription(interimTranscript);
          }
        };

        rec.onerror = (event: any) => {
          console.error("Speech recognition error", event.error);
          setIsListening(false);
          if (event.error === 'no-speech') {
            setTranscription('Sikupata sauti. Tafadhali bonyeza mic na ujaribu tena.');
          } else {
            setTranscription(`Hitilafu ya sauti: ${event.error}`);
          }
        };

        rec.onend = () => {
          setIsListening(false);
          // Only send if we have a valid accumulated final transcript and haven't sent it yet
          const finalVal = finalTranscriptRef.current;
          if (finalVal && !hasSentRef.current) {
            hasSentRef.current = true;
            if (handleSendRef.current) {
              handleSendRef.current(finalVal);
            }
          }
        };

        setRecognition(rec);
      }
    }
  }, []);

  // Handle Voice capture trigger
  useEffect(() => {
    if (!recognition) return;
    if (isListening) {
      if (audioElement) {
        audioElement.pause();
      }
      try {
        recognition.start();
      } catch (e) {
        console.error(e);
      }
    } else {
      try {
        recognition.stop();
      } catch (e) {
        console.error(e);
      }
    }
  }, [isListening, recognition, audioElement]);

  async function handleSend(messageText: string) {
    if (!messageText.trim()) return;
    setIsLoading(true);
    setTranscription(messageText);
    setResponse('');
    
    if (audioElement) {
      audioElement.pause();
    }

    // Capture logs update
    const timeNow = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, {
      timestamp: timeNow,
      text: `STT: User triggered input: "${messageText}"`
    }]);

    const requestHistory = showTextInput ? [] : []; // We keep it simple (current session history is optional, we pass empty or state list)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: messageText,
          persona: selectedPersona,
          history: requestHistory
        })
      });

      if (!res.ok) {
        throw new Error('API server communication failure.');
      }

      const data = await res.json();
      setResponse(data.response);

      // Dynamically load logs and telemetry
      if (data.telemetry) {
        setTelemetry(prev => ({
          ...prev,
          ...data.telemetry,
          intent: data.telemetry.intent || 'General'
        }));
      }

      if (data.logs) {
        const timeReceived = new Date().toLocaleTimeString();
        const formattedLogs = data.logs.map((log: string) => ({
          timestamp: timeReceived,
          text: log
        }));
        setLogs(prev => [...prev, ...formattedLogs]);
      }

      // Voice Playback
      const audioUrl = `/api/tts?text=${encodeURIComponent(data.response)}`;
      const newAudio = new Audio(audioUrl);
      setAudioElement(newAudio);
      newAudio.play().catch(err => console.error("Audio playback interrupted/blocked by browser autoplay rules:", err));

    } catch (error) {
      console.error(error);
      setResponse('Mtafaruku umetokea. Tafadhali hakikisha kuwa backend API server inafanya kazi kwenye port 5000.');
      setLogs(prev => [...prev, {
        timestamp: new Date().toLocaleTimeString(),
        text: 'API Error: Kushindwa kuunganisha na server. Hakikisha python server ipo hai.'
      }]);
    } finally {
      setIsLoading(false);
    }
  }


  const tabs = [
    { id: 'home', label: 'Home', icon: Home },
    { id: 'activity', label: 'Activity History', icon: History },
  ];

  return (
    <div className="min-h-screen w-full flex flex-col bg-[#0a0505] text-[#ffdad4] overflow-hidden font-[family-name:var(--font-outfit)] selection:bg-[#e60000]/30">
      
      {/* Main Content Area */}
      <main className="flex-1 w-full max-w-7xl mx-auto flex flex-col items-center justify-center p-6 pb-28">
        <AnimatePresence mode="wait">
          {activeTab === 'home' && (
            <motion.div 
              key="home"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
              className="w-full flex flex-col items-center max-w-3xl"
            >
              <h1 className="text-2xl font-semibold mb-2 text-white">Hujambo Jane!</h1>
              
              <div className="flex items-center gap-3 mb-8">
                <p className="text-base text-[#e9bcb5]">Ninaweza kukusaidia nini leo?</p>
                <button 
                  onClick={() => setShowTextInput(!showTextInput)} 
                  className={cn(
                    "p-1.5 rounded-lg border border-white/5 text-white/50 hover:text-white hover:border-white/10 transition-all cursor-pointer flex items-center gap-1",
                    showTextInput && "border-[#e60000]/30 text-[#e60000] bg-[#e60000]/5"
                  )}
                  title="Andika ujumbe badala ya kuongea"
                >
                  <Keyboard className="w-3.5 h-3.5" />
                  <span className="text-[10px] uppercase font-mono tracking-wider px-1">Typing Mode</span>
                </button>
              </div>

              {/* Transcription / Response card */}
              <GlassCard active={isListening || isLoading} className="w-full min-h-[200px] flex flex-col justify-center items-center relative transition-all duration-300">
                <AnimatePresence mode="wait">
                  {isListening ? (
                    <motion.div 
                      key="listening"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="flex flex-col items-center gap-3"
                    >
                      <p className="font-mono text-lg text-center tracking-wide text-[#ffb4a8] animate-pulse">
                        {transcription || 'Kusikiliza...'}
                      </p>
                      <span className="text-xs text-white/40">Zungumza kwa Kiswahili na ubonyeze kitufe ukimaliza</span>
                    </motion.div>
                  ) : isLoading ? (
                    <motion.div 
                      key="loading"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="flex flex-col items-center gap-3"
                    >
                      <Loader2 className="w-8 h-8 text-[#e60000] animate-spin" />
                      <p className="font-mono text-sm tracking-wide text-[#ffb4a8]">
                        Ana anatafakari majibu{transcriptionDots}
                      </p>
                    </motion.div>
                  ) : response ? (
                    <motion.div 
                      key="response"
                      initial={{ opacity: 0, y: 5 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                      className="w-full text-left"
                    >
                      <span className="text-[10px] uppercase font-bold tracking-widest text-[#e60000] font-mono block mb-2">Ana Neural Assistant</span>
                      <p className="text-base text-white/90 leading-relaxed font-sans whitespace-pre-wrap">
                        {response}
                      </p>
                      {transcription && (
                        <div className="mt-4 pt-3 border-t border-white/5 text-xs text-white/30 font-mono">
                          Swali Lako: "{transcription}"
                        </div>
                      )}
                    </motion.div>
                  ) : (
                    <motion.div 
                      key="idle"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="text-center"
                    >
                      <p className="font-mono text-sm text-[#ffb4a8]/60">
                        {transcription || 'Bonyeza kitufe cha MIC hapo chini ili kuongea, au washa Typing Mode kuandika.'}
                      </p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </GlassCard>

              {/* Toggleable Text Input Bar */}
              {showTextInput && (
                <motion.form 
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSend(textInput);
                    setTextInput('');
                  }} 
                  className="w-full mt-6 flex gap-2"
                >
                  <input
                    type="text"
                    value={textInput}
                    onChange={(e) => setTextInput(e.target.value)}
                    placeholder="Andika swali lako kwa Kiswahili hapa..."
                    disabled={isLoading}
                    className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-[#e60000]/50 transition-all font-mono placeholder:text-white/20"
                  />
                  <button
                    type="submit"
                    disabled={isLoading || !textInput.trim()}
                    className="bg-gradient-to-r from-[#e60000] to-[#990000] text-white px-5 py-3 rounded-xl text-sm font-medium hover:scale-105 active:scale-95 transition-all cursor-pointer disabled:opacity-50 disabled:scale-100"
                  >
                    Tuma
                  </button>
                </motion.form>
              )}



            </motion.div>
          )}

          {activeTab === 'activity' && (
            <motion.div 
               key="activity"
               initial={{ opacity: 0, y: 10 }}
               animate={{ opacity: 1, y: 0 }}
               exit={{ opacity: 0, y: -10 }}
               transition={{ duration: 0.3 }}
               className="w-full h-full flex flex-col lg:flex-row gap-6 max-w-6xl mt-8"
            >
              {/* Logic Flow Pane */}
              <div className="flex-1 flex flex-col">
                <div className="flex items-center justify-between mb-4">
                   <h2 className="text-base font-medium text-white/90">Logic Flow</h2>
                   <div className="flex items-center space-x-2 border border-green-500/30 bg-green-500/10 px-2 py-1 rounded-sm">
                     <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></div>
                     <span className="text-[10px] uppercase tracking-wider font-mono text-green-400">Live Analytics</span>
                   </div>
                </div>
                <GlassCard className="flex-1 flex flex-col font-mono text-xs space-y-3 min-h-[350px] max-h-[500px] overflow-y-auto">
                  {logs.map((log, index) => (
                    <div key={index} className="text-[#ffb4a8]/80 leading-relaxed">
                      <span className="opacity-50 mr-2">[{log.timestamp}]</span>
                      {log.text}
                    </div>
                  ))}
                </GlassCard>
              </div>

              {/* Data Retrieval Pane */}
              <div className="flex-1 flex flex-col">
                <h2 className="text-base font-medium text-white/90 mb-4">Data Retrieval</h2>
                <div className="flex flex-col gap-4">
                  <GlassCard className="font-mono text-xs">
                    <div className="text-white/50 mb-2">{`// Customer_Profile_Telemetry`}</div>
                    <pre className="text-[#e9bcb5] overflow-x-auto text-[11px] leading-relaxed">
{`{
  "name": "${telemetry.name || 'Jane Dinah'}",
  "msisdn": "${telemetry.msisdn || '+255 754 *** 123'}",
  "nida_status": "${telemetry.nida_status || 'VERIFIED'}",
  "account_level": "${telemetry.account_level || 'Tier_2'}",
  "detected_intent": "${telemetry.intent || 'None'}"
}`}
                    </pre>
                  </GlassCard>

                  <GlassCard className="font-mono text-xs">
                    <div className="text-white/50 mb-2">{`// System_Engine_Metrics`}</div>
                    <pre className="text-[#e9bcb5] overflow-x-auto text-[11px] leading-relaxed">
{`{
  "engine_mode": "${telemetry.engine || 'groq'}",
  "llm_model": "${telemetry.model || 'llama-3.3-70b-versatile'}",
  "tts_provider": "${telemetry.tts_provider || 'google'}",
  "sim_status": "${telemetry.sim_status || 'ACTIVE'}",
  "roaming_status": ${telemetry.roaming ?? false},
  "last_tower_id": "${telemetry.last_tower_id || 'T-DAR-091'}"
}`}
                    </pre>
                  </GlassCard>
                </div>
              </div>
            </motion.div>
          )}

        </AnimatePresence>
      </main>

      {/* Bottom Navigation & Vocal UI Centerpiece */}
      <div className="fixed bottom-0 left-0 w-full pointer-events-none pb-6 px-4 flex justify-center z-50">
        
        {/* Floating Nav Container */}
        <div className="relative pointer-events-auto bg-[#1b0907]/90 border border-white/5 backdrop-blur-3xl rounded-full px-6 py-2 w-full max-w-xl flex items-center justify-between shadow-[0_20px_40px_rgba(0,0,0,0.5)]">
           
           {/* Center Mic Wrapper Container - cuts out nav visually */}
           <div className="absolute left-1/2 -top-8 -translate-x-1/2 flex flex-col items-center justify-center">
              
              {/* Ripple Effect Animation */}
              {isListening && (
                 <div className="absolute inset-0 m-auto flex items-center justify-center pointer-events-none">
                    <motion.div
                       animate={{ scale: [1, 1.6], opacity: [0.3, 0] }}
                       transition={{ repeat: Infinity, duration: 1.5, ease: "easeOut" }}
                       className="absolute w-20 h-20 border border-[#e60000] rounded-full"
                    />
                    <motion.div
                       animate={{ scale: [1, 2.2], opacity: [0.15, 0] }}
                       transition={{ repeat: Infinity, duration: 1.5, delay: 0.4, ease: "easeOut" }}
                       className="absolute w-20 h-20 border border-[#e60000] rounded-full"
                    />
                 </div>
              )}

              {/* The Mic Button itself */}
              <button 
                onClick={handleMicClick}
                className="relative z-10 w-16 h-16 rounded-full flex items-center justify-center overflow-hidden border-[3px] border-[#410000] bg-gradient-to-br from-[#e60000] to-[#990000] shadow-[0_0_20px_rgba(230,0,0,0.4)] transition-transform hover:scale-105 active:scale-95 cursor-pointer"
              >
                 <Mic className="w-6 h-6 text-white relative z-10" />
                 {/* Internal pulse glow */}
                 <div className="absolute inset-0 bg-white/20 blur-md rounded-full pointer-events-none mix-blend-overlay"></div>
              </button>

              <span className="text-[10px] uppercase font-bold tracking-widest text-[#e60000] mt-3 font-mono">
                {isListening ? 'Listening...' : 'Tap to speak'}
              </span>
           </div>

           {/* Left Tabs */}
           <div className="flex flex-1 justify-around items-center pr-10">
             {tabs.slice(0, 1).map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => {
                    setActiveTab(tab.id as any);
                    if (tab.id === 'home') {
                      // reset text input views
                    }
                  }}
                  className={cn(
                    "flex flex-col items-center gap-1 transition-colors p-1.5 cursor-pointer",
                    activeTab === tab.id ? "text-[#e60000]" : "text-white/40 hover:text-white/80"
                  )}
                >
                  <tab.icon className="w-5 h-5 stroke-[1.5]" />
                  <span className="text-[11px] font-medium">{tab.label}</span>
                </button>
             ))}
           </div>

           {/* Right Tabs */}
           <div className="flex flex-1 justify-around items-center pl-10">
             {tabs.slice(1, 2).map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={cn(
                    "flex flex-col items-center gap-1 transition-colors p-1.5 cursor-pointer",
                    activeTab === tab.id ? "text-[#e60000]" : "text-white/40 hover:text-white/80"
                  )}
                >
                  <tab.icon className="w-5 h-5 stroke-[1.5]" />
                  <span className="text-[11px] font-medium">{tab.label}</span>
                </button>
             ))}
           </div>
        </div>
      </div>

    </div>
  );
}
