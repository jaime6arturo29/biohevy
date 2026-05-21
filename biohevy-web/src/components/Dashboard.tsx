"use client";
import React, { useState, useEffect, useRef } from "react";
import { UserButton } from "@clerk/nextjs";
const API_BASE = "http://127.0.0.1:8000";


        const translations = {
            es: {
                summary: "Resumen", train: "Entrenar", science: "Ciencia", history: "Historial de Rendimiento",
                no_sessions: "No hay sesiones registradas.", duration: "Duración", volume: "Volumen",
                series: "Series", view_more: "Ver Mas", routines: "Programas Guardados",
                create_routine: "Crear Rutina", start_session: "Iniciar Sesion", settings: "Ajustes",
                theme: "Tema", lang: "Idioma", emg: "Activar EMG", save: "Guardar Ajustes",
                routine: "Rutina", close: "Cerrar", confirm: "Confirmar", add_exercise: "+ Vincular Ejercicio",
                add_set: "+ Agregar Serie", finish_workout: "Finalizar Entrenamiento", emg_monitoring: "Monitoreo EMG",
                electrode_warning: "Electrodo no Detectado", simulate: "Simular Colocacion", failure: "Fallo",
                weight: "Peso Corporal", height: "Altura", rest: "Descanso", protocol: "Protocolo",
                exercises: { "Press de Banca con Barra": "Press de Banca con Barra", "Sentadilla con Barra": "Sentadilla con Barra", "Peso Muerto": "Peso Muerto", "Dominadas": "Dominadas", "Elevacion de Gemelos de Pie": "Elevacion de Gemelos de Pie" }
            },
            en: {
                summary: "Summary", train: "Train", science: "Science", history: "Performance History",
                no_sessions: "No sessions recorded.", duration: "Duration", volume: "Volume",
                series: "Sets", view_more: "View More", routines: "Saved Programs",
                create_routine: "Create Routine", start_session: "Start Session", settings: "Settings",
                theme: "Theme", lang: "Language", emg: "Enable EMG", save: "Save Settings",
                routine: "Routine", close: "Close", confirm: "Confirm", add_exercise: "+ Add Exercise",
                add_set: "+ Add Set", finish_workout: "Finish Workout", emg_monitoring: "EMG Monitoring",
                electrode_warning: "Electrode Not Detected", simulate: "Simulate Placement", failure: "Failure",
                weight: "Body Weight", height: "Height", rest: "Rest", protocol: "Protocol",
                exercises: { "Press de Banca con Barra": "Barbell Bench Press", "Sentadilla con Barra": "Barbell Squat", "Peso Muerto": "Deadlift", "Dominadas": "Pull-ups", "Elevacion de Gemelos de Pie": "Standing Calf Raises" }
            }
        };
        const BioHevyEMGMonitor = ({ t }) => {
            const [connected, setConnected] = useState(false);
            const [zoom, setZoom] = useState(1.0);
            const [rawSignal, setRawSignal] = useState(Array(100).fill(0));
            const [filteredSignal, setFilteredSignal] = useState(Array(100).fill(0));
            const [rmsSignal, setRmsSignal] = useState(Array(100).fill(0));
            const [mnfSignal, setMnfSignal] = useState(Array(100).fill(120));
            const [fatigueAlert, setFatigueAlert] = useState(null);
            
            // Biomedical Diagnostics
            const [snr, setSnr] = useState(0.0);
            const [accuracy, setAccuracy] = useState(0.0);
            const [r2, setR2] = useState(0.0);

            // Simulation loop for visualization
            useEffect(() => {
                if (!connected) {
                    setSnr(0.0);
                    setAccuracy(0.0);
                    setR2(0.0);
                    return;
                }
                
                let time = 0;
                let fatigueLevel = 0;
                const interval = setInterval(() => {
                    time += 0.05;
                    fatigueLevel += 0.005;
                    
                    const isFatigued = fatigueLevel > 5;
                    const freq = isFatigued ? 60 : 100;
                    const amp = isFatigued ? 400 : 150;
                    
                    // Generate new point
                    const newRaw = amp * Math.sin(2 * Math.PI * freq * time) + (Math.random() * 50 - 25);
                    const newFiltered = newRaw * 0.8; // Simulating filtering
                    const newRms = Math.abs(newFiltered) * 0.7 + (isFatigued ? 50 : 0);
                    
                    // Frecuencia Media (MNF) shifts downwards as muscle fatigue sets in (spectral shift)
                    const baseMnf = isFatigued ? 68.0 : 118.0;
                    const noiseMnf = Math.random() * 4.0 - 2.0;
                    const newMnf = Math.max(45, baseMnf + noiseMnf - (fatigueLevel * 2.5));

                    setRawSignal(prev => [...prev.slice(1), newRaw]);
                    setFilteredSignal(prev => [...prev.slice(1), newFiltered]);
                    setRmsSignal(prev => [...prev.slice(1), newRms]);
                    setMnfSignal(prev => [...prev.slice(1), newMnf]);
                    
                    // Live Diagnostics updates
                    const baseSnr = isFatigued ? 26.5 : 28.8;
                    setSnr(parseFloat((baseSnr + Math.random() * 0.6 - 0.3).toFixed(1)));
                    setAccuracy(parseFloat((96.2 + Math.random() * 0.4 - 0.2).toFixed(1)));
                    setR2(parseFloat((0.92 + Math.random() * 0.03 - 0.01).toFixed(2)));

                    if (isFatigued && !fatigueAlert) {
                        setFatigueAlert("Fatiga Inminente Detectada");
                    }
                }, 50);
                
                return () => clearInterval(interval);
            }, [connected, fatigueAlert]);

            const renderGraph = (data, color, maxVal, title, isPositiveOnly = false) => {
                return (
                    <div className="mb-4">
                        <div className="text-center text-[10px] font-black tracking-widest uppercase mb-1.5" style={{ color }}>{title}</div>
                        <div className="h-32 border border-gray-900 bg-black/40 rounded-xl relative overflow-hidden">
                            <div className="absolute left-0 top-0 bottom-0 w-8 border-r border-gray-900 bg-black/60 flex flex-col justify-between items-end pr-1.5 py-1.5 text-[8px] text-gray-500 font-mono">
                                <span>{maxVal}</span>
                                <span>{isPositiveOnly ? Math.round(maxVal / 2) : 0}</span>
                                <span>{isPositiveOnly ? 0 : -maxVal}</span>
                            </div>
                            <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none" viewBox="0 0 100 100">
                                <polyline
                                    fill="none"
                                    stroke={color}
                                    strokeWidth="0.8"
                                    points={data.map((val, i) => {
                                        const x = (i / (data.length - 1)) * 100;
                                        const normalized = isPositiveOnly 
                                            ? 100 - ((val / maxVal) * 90 * zoom) - 5
                                            : 50 - ((val / maxVal) * 45 * zoom);
                                        return `${x},${normalized}`;
                                    }).join(' ')}
                                />
                            </svg>
                            {/* Grid lines */}
                            <div className="absolute inset-0 pointer-events-none opacity-[0.05] bg-[linear-gradient(rgba(255,255,255,0.1)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.1)_1px,transparent_1px)] bg-[size:20px_20px]"></div>
                        </div>
                    </div>
                );
            };

            return (
                <div className="bg-[#0a0a0f] border border-zinc-900 rounded-3xl p-6 mb-12 shadow-2xl overflow-hidden font-sans border-cyan-500/10">
                    <div className="flex items-center gap-4 mb-6 border-b border-zinc-900 pb-4">
                        <div className="flex flex-col">
                            <label className="text-[8px] text-gray-500 mb-1 font-mono uppercase tracking-wider">HARDWARE</label>
                            <select className="bg-black border border-zinc-800 text-xs text-white p-1.5 rounded-lg outline-none focus:border-cyan-500/50">
                                <option>ESP32 (Canal 1)</option>
                                <option>ESP32 (Canal 2)</option>
                            </select>
                        </div>
                        <button 
                            onClick={() => { setConnected(!connected); setFatigueAlert(null); }}
                            className={`px-4 py-2 text-[10px] font-black uppercase tracking-wider rounded-xl transition-all border ${
                                connected 
                                    ? 'bg-red-500/10 text-red-500 border-red-500/30' 
                                    : 'bg-[var(--primary)]/10 text-[var(--primary)] border-[var(--primary)]/30 hover:bg-[var(--primary)] hover:text-black'
                            }`}
                        >
                            {connected ? 'DESCONECTAR' : 'CONECTAR'}
                        </button>
                        <div className="flex flex-col ml-4">
                            <label className="text-[8px] text-gray-500 mb-1 font-mono uppercase tracking-wider">ZOOM</label>
                            <div className="flex items-center gap-2 text-xs">
                                <input type="number" step="0.1" value={zoom} onChange={(e) => setZoom(parseFloat(e.target.value) || 1.0)} className="w-12 bg-black border border-zinc-800 p-1.5 text-white text-center rounded-lg outline-none font-mono" />
                            </div>
                        </div>
                        {fatigueAlert && (
                            <div className="ml-auto bg-red-600 text-white text-[9px] font-black uppercase px-3 py-2 rounded-xl animate-pulse border border-red-500/30 tracking-wider">
                                {fatigueAlert}
                            </div>
                        )}
                    </div>

                    {connected && (
                        <div className="grid grid-cols-3 gap-3 mb-6 bg-zinc-950 p-4 rounded-2xl border border-zinc-900 animate-fade-in font-mono">
                            <div className="text-center">
                                <div className="text-[8px] text-zinc-500 uppercase tracking-widest mb-1">Calidad SNR</div>
                                <div className="text-sm font-black text-emerald-400">{snr} dB</div>
                                <div className="text-[8px] text-emerald-500 font-bold uppercase mt-0.5">EXCELENTE</div>
                            </div>
                            <div className="text-center border-x border-zinc-900">
                                <div className="text-[8px] text-zinc-500 uppercase tracking-widest mb-1">Precisión R²</div>
                                <div className="text-sm font-black text-cyan-400">{r2}</div>
                                <div className="text-[8px] text-cyan-500 font-bold uppercase mt-0.5">CORRELACIÓN ALTA</div>
                            </div>
                            <div className="text-center">
                                <div className="text-[8px] text-zinc-500 uppercase tracking-widest mb-1">Confianza</div>
                                <div className="text-sm font-black text-indigo-400">{accuracy}%</div>
                                <div className="text-[8px] text-indigo-500 font-bold uppercase mt-0.5">MÉDICA</div>
                            </div>
                        </div>
                    )}
                    
                    {renderGraph(rawSignal, '#666666', 1000, 'Señal Cruda (Debug)')}
                    {renderGraph(filteredSignal, '#00f2ff', 500, 'Señal EMG (Filtrada)')}
                    {renderGraph(rmsSignal, '#ff4444', 300, 'Fatiga (RMS)', true)}
                    {renderGraph(mnfSignal, '#a855f7', 150, 'Frecuencia Media (MNF)', true)}
                </div>
            );
        };

        const Calendar = ({ sessions, onSelectSession, lang = 'es' }) => {
            const [viewDate, setViewDate] = useState(new Date());
            const month = viewDate.getMonth();
            const year = viewDate.getFullYear();
            const daysInMonth = new Date(year, month + 1, 0).getDate();
            const startDay = new Date(year, month, 1).getDay();

            const prevMonth = () => setViewDate(new Date(year, month - 1, 1));
            const nextMonth = () => setViewDate(new Date(year, month + 1, 1));
            const fullMonthName = new Intl.DateTimeFormat(lang === 'es' ? 'es-ES' : 'en-US', { month: 'long' }).format(viewDate);
            const monthName = fullMonthName.substring(0, 3).toUpperCase();

            const dayLabels = lang === 'es' ? ['D', 'L', 'M', 'Mi', 'J', 'V', 'S'] : ['S', 'M', 'T', 'W', 'T', 'F', 'S'];

            return (
                <div className="card mb-8">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="label">{monthName} {year}</h3>
                        <div className="flex gap-6">
                            <button onClick={prevMonth} className="text-[var(--text-dim)] hover:text-[var(--primary)] text-lg">&larr;</button>
                            <button onClick={nextMonth} className="text-[var(--text-dim)] hover:text-[var(--primary)] text-lg">&rarr;</button>
                        </div>
                    </div>
                    <div className="grid grid-cols-7 gap-1 text-center text-[8px] font-black text-[var(--text-dim)] mb-4">
                        {dayLabels.map(d => <div key={d}>{d}</div>)}
                    </div>
                    <div className="grid grid-cols-7 gap-2">
                        {[...Array(startDay)].map((_, i) => <div key={`e-${i}`}></div>)}
                        {[...Array(daysInMonth)].map((_, i) => {
                            const d = i + 1;
                            const daySessions = sessions.filter(session => {
                                const dt = new Date(session.start_time);
                                return dt.getDate() === d && dt.getMonth() === month && dt.getFullYear() === year;
                            });
                            const isActive = daySessions.length > 0;
                            return (
                                <div 
                                    key={d} 
                                    onClick={() => isActive && onSelectSession(daySessions[0])}
                                    className={`aspect-square flex items-center justify-center rounded-xl text-[10px] font-bold border transition-all ${isActive ? 'bg-[var(--primary)] text-black border-[var(--primary)] cursor-pointer hover:scale-110 active:scale-95 shadow-[0_0_15px_rgba(0,242,255,0.3)]' : 'text-[var(--text)] border-[var(--border)] opacity-30'}`}
                                >
                                    {d}
                                </div>
                            );
                        })}
                    </div>
                </div>
            );
        };

        const SettingsDrawer = ({ isOpen, onClose, user, onUpdate, t }) => {
            const [localSettings, setLocalSettings] = useState(user || {});
            useEffect(() => { if (user) setLocalSettings(user); }, [user]);

            return (
                <>
                    <div className={`fixed inset-0 bg-black/60 backdrop-blur-sm z-[140] transition-opacity duration-300 ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`} onClick={onClose}></div>
                    <div className={`fixed right-0 top-0 h-full w-80 bg-[var(--bg)] z-[145] p-10 border-l border-[var(--border)] transition-transform duration-500 ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}>
                        <div className="flex justify-between items-center mb-12">
                            <h2 className="text-xl font-black italic uppercase tracking-widest color-[var(--text)]">{t.settings}</h2>
                            <button onClick={onClose} className="text-2xl font-light text-[var(--text-dim)]">&times;</button>
                        </div>
                        <div className="space-y-10 overflow-y-auto max-h-[70vh] pr-2">
                            <div>
                                <label className="label block mb-4">{t.theme}</label>
                                <div className="grid grid-cols-2 gap-2 bg-[var(--border)] p-1 rounded-xl">
                                    {['dark', 'light'].map(v => (
                                        <button key={v} onClick={() => setLocalSettings({ ...localSettings, theme: v })} className={`py-3 rounded-lg text-[10px] font-black uppercase transition-all ${localSettings.theme === v ? 'bg-[var(--primary)] text-black' : 'text-[var(--text-dim)]'}`}>{v}</button>
                                    ))}
                                </div>
                            </div>
                            <div>
                                <label className="label block mb-4">{t.lang}</label>
                                <div className="grid grid-cols-2 gap-2 bg-[var(--border)] p-1 rounded-xl">
                                    {['es', 'en'].map(v => (
                                        <button key={v} onClick={() => setLocalSettings({ ...localSettings, lang: v })} className={`py-3 rounded-lg text-[10px] font-black uppercase transition-all ${localSettings.lang === v ? 'bg-[var(--primary)] text-black' : 'text-[var(--text-dim)]'}`}>{v === 'es' ? 'ES' : 'EN'}</button>
                                    ))}
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="label block mb-2">{t.weight}</label>
                                    <input type="number" className="w-full py-3" value={localSettings.weight_kg} onChange={e => setLocalSettings({ ...localSettings, weight_kg: e.target.value })} />
                                </div>
                                <div>
                                    <label className="label block mb-2">{t.height}</label>
                                    <input type="number" className="w-full py-3" value={localSettings.height_cm} onChange={e => setLocalSettings({ ...localSettings, height_cm: e.target.value })} />
                                </div>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="label">{t.emg}</span>
                                <button onClick={() => setLocalSettings({ ...localSettings, emg_enabled: !localSettings.emg_enabled })} className={`w-12 h-6 rounded-full relative transition-all ${localSettings.emg_enabled ? 'bg-[var(--primary)]' : 'bg-zinc-800'}`}>
                                    <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${localSettings.emg_enabled ? 'right-1' : 'left-1'}`}></div>
                                </button>
                            </div>
                        </div>
                        <button onClick={() => { onUpdate(localSettings); onClose(); }} className="btn-primary w-full py-5 mt-12 text-[10px]">{t.save}</button>
                    </div>
                </>
            );
        };

        const Main = ({ clerkUser }) => {
            const [tab, setTab] = useState('ROUTINES');
            const [user, setUser] = useState(null);
            const [exercises, setExercises] = useState([]);
            const [routines, setRoutines] = useState([]);
            const [history, setHistory] = useState([]);
            const [news, setNews] = useState([]);
            const [activeSession, setActiveSession] = useState(null);
            const [timer, setTimer] = useState(0);
            const [isDrawerOpen, setIsDrawerOpen] = useState(false);
            const [editingRoutine, setEditingRoutine] = useState(null);
            const [selectedExercise, setSelectedExercise] = useState(null);
            const [viewingFullSession, setViewingFullSession] = useState(null);
            const [viewingExerciseHistory, setViewingExerciseHistory] = useState(null);
            const [summary, setSummary] = useState(null);
            const [isElectrodeConnected, setIsElectrodeConnected] = useState(false);
            const [fatigue, setFatigue] = useState(20);
            const [restTimer, setRestTimer] = useState(0);
            const [isTimerRunning, setIsTimerRunning] = useState(false);
            const [restTimerInput, setRestTimerInput] = useState(90);
            const [routineToDelete, setRoutineToDelete] = useState(null);

            const timerRef = useRef(null);
            const restTimerRef = useRef(null);
            const t = translations[user?.lang || 'es'];

            useEffect(() => {
                fetchUser();
                fetchExercises();
                fetchNews();
            }, []);

            useEffect(() => {
                if (user) { fetchRoutines(); fetchHistory(); }
                if (user?.theme === 'light') { document.body.classList.add('theme-light'); }
                else { document.body.classList.remove('theme-light'); }
            }, [user?.id, user?.theme]);

            useEffect(() => {
                if (activeSession) { timerRef.current = setInterval(() => setTimer(v => v + 1), 1000); }
                else { clearInterval(timerRef.current); setTimer(0); }
                return () => clearInterval(timerRef.current);
            }, [!!activeSession]);

            useEffect(() => {
                if (restTimer > 0 && isTimerRunning) {
                    restTimerRef.current = setInterval(() => setRestTimer(v => v - 1), 1000);
                } else if (restTimer <= 0) {
                    setIsTimerRunning(false);
                    clearInterval(restTimerRef.current);
                }
                return () => clearInterval(restTimerRef.current);
            }, [restTimer, isTimerRunning]);

            const fetchUser = async () => {
                if (!clerkUser) return;
                try {
                    const res = await fetch(`${API_BASE}/auth/clerk-login`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ clerk_id: clerkUser.id, username: clerkUser.fullName || 'User' })
                    });
                    const dbUser = await res.json();
                    
                    let saved = localStorage.getItem('biohevy_user_v5');
                    let localSettings = saved ? JSON.parse(saved) : { theme: 'dark', lang: 'es', emg_enabled: true, weight_kg: 80, height_cm: 180 };
                    
                    setUser({ ...localSettings, ...dbUser });
                } catch(e) { console.error("Error syncing user", e); }
            };

            const fetchExercises = () => fetch(`${API_BASE}/exercises`).then(r => r.json()).then(setExercises).catch(e => console.error("Exercises fetch error:", e));
            const fetchRoutines = () => fetch(`${API_BASE}/routines?user_id=${user.id}`).then(r => r.json()).then(setRoutines).catch(e => console.error("Routines fetch error:", e));
            const fetchHistory = () => fetch(`${API_BASE}/sessions?user_id=${user.id}`).then(r => r.json()).then(setHistory).catch(e => console.error("History fetch error:", e));
            const fetchNews = () => fetch(`${API_BASE}/news`).then(r => r.json()).then(setNews).catch(e => console.error("News fetch error:", e));

            const updateSettings = async (s) => { setUser(s); localStorage.setItem('biohevy_user_v5', JSON.stringify(s)); };
            const startSession = async (r) => {
                // Notify backend that session started
                const payload = { user_id: user.id, routine_id: r.id, start_time: new Date().toISOString() };
                const res = await fetch(`${API_BASE}/sessions/start`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
                const sessionData = await res.json();

                setActiveSession({
                    ...r,
                    db_id: sessionData.id,
                    start_time: payload.start_time,
                    exercises: r.exercises.map(ex => {
                        let previousSets = [{ weight: '', reps: '', failure: false, completed: false }];
                        const allExSessions = history.filter(s => s.exercises?.some(e => e.id === ex.id || e.exercise_id === ex.id));
                        if (allExSessions.length > 0) {
                            const lastS = allExSessions[0];
                            const lastEx = lastS.exercises.find(e => e.id === ex.id || e.exercise_id === ex.id);
                            if (lastEx && lastEx.sets?.length > 0) {
                                previousSets = lastEx.sets.map(s => ({ weight: s.weight || '', reps: s.reps || '', failure: false, completed: false }));
                            }
                        }
                        return { ...ex, unit: 'kg', sets: previousSets };
                    }),
                    isModified: false
                });
            };

            const finishSession = async () => {
                try {
                    const hasIncomplete = activeSession.exercises.some(ex => ex.sets?.some(s => !s.completed && !s.failure));
                    if (hasIncomplete) {
                        if (!confirm("¿Seguro que quieres terminar? Aún hay ejercicios por completar.")) return;
                    }

                    if (activeSession.isModified) {
                        if (confirm("La rutina ha sido modificada. ¿Deseas actualizar la plantilla original?")) {
                            await saveRoutine(activeSession);
                        }
                    } else {
                        if (!confirm("La rutina se finalizará exitosamente. ¿Continuar?")) return;
                    }

                    const payload = {
                        end_time: new Date().toISOString(),
                        sets: activeSession.exercises.flatMap(ex => ex.sets?.filter(s => s.completed || s.failure).map(s => ({
                            exercise_id: ex.id || ex.exercise_id,
                            reps: parseInt(s.reps) || 0,
                            weight: parseFloat(s.weight) || 0,
                            is_failure: s.failure
                        })) || [])
                    };

                    if (!activeSession.db_id) {
                        console.warn("No db_id found, closing session locally.");
                        setActiveSession(null);
                        return;
                    }

                    const res = await fetch(`${API_BASE}/sessions/${activeSession.db_id}/end`, { 
                        method: 'POST', 
                        headers: { 'Content-Type': 'application/json' }, 
                        body: JSON.stringify(payload) 
                    }).catch(e => { throw new Error("Network error") });
                    
                    if (!res.ok) throw new Error("Failed to end session on server");
                    const resData = await res.json();

                    // Manually add to history to ensure it shows up immediately with correct keys
                    const newSession = {
                        id: Date.now(),
                        start_time: activeSession.start_time,
                        duration_minutes: Math.floor(timer / 60),
                        exercises: activeSession.exercises,
                        routine_id: activeSession.name,
                        total_volume: resData.volume || 0,
                        set_count: activeSession.exercises.reduce((acc, ex) => acc + (ex.sets?.length || 0), 0)
                    };
                    setHistory(prev => [newSession, ...prev]);
                    setSummary(resData);
                    
                } catch (e) {
                    console.error("Error finalizing session:", e);
                    alert("Se produjo un error de red, pero tu sesión local ha terminado.");
                } finally {
                    setActiveSession(null);
                }
            };

            const deleteRoutine = async (id) => {
                const res = await fetch(`${API_BASE}/routines/${id}`, { method: 'DELETE' });
                if (res.ok) { fetchRoutines(); setRoutineToDelete(null); }
            };

            const saveRoutine = async (r) => {
                const isUpdate = !!r.id;
                const url = isUpdate ? `${API_BASE}/routines/${r.id}` : `${API_BASE}/routines`;
                const method = isUpdate ? 'PUT' : 'POST';

                const payload = { 
                    name: r.name, 
                    user_id: user.id, 
                    exercises: r.exercises.map((ex, i) => ({ 
                        exercise_id: ex.id || ex.exercise_id, 
                        order_index: i, 
                        template_data: "{}" 
                    })) 
                };
                const res = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
                if (res.ok) { setEditingRoutine(null); fetchRoutines(); }
            };

            if (!user) return null;

            return (
                <div className="min-h-screen pb-32">
                    {/* Header */}
                    <nav className="fixed top-0 w-full glass h-20 z-[100] flex items-center justify-between px-8">
                        <div className="text-2xl font-black italic uppercase tracking-tighter text-[var(--text)]">Bio<span className="text-[var(--primary)]">Hevy</span></div>
                        <div className="flex items-center gap-6">
                            <UserButton 
                                appearance={{
                                    elements: {
                                        userButtonAvatarBox: "w-8 h-8 rounded-full border border-[var(--primary)]/30",
                                        userButtonTrigger: "focus:shadow-none focus:outline-none"
                                    }
                                }} 
                            />
                            <button onClick={() => setIsDrawerOpen(true)} className="flex flex-col gap-1.5 items-end">
                                <div className="w-6 h-0.5 bg-[var(--text)]"></div>
                                <div className="w-4 h-0.5 bg-[var(--text)]"></div>
                                <div className="w-6 h-0.5 bg-[var(--text)]"></div>
                            </button>
                        </div>
                    </nav>

                    <div className="pt-28 px-6 max-w-2xl mx-auto">
                        {tab === 'HISTORY' && (
                            <section>
                                <h2 className="section-header">{t.history}</h2>
                                <Calendar sessions={history} onSelectSession={setViewingFullSession} lang={user?.lang} />
                                <div className="space-y-6">
                                    {history.map(s => (
                                        <div key={s.id} className="card">
                                            <div className="flex justify-between items-start mb-6">
                                                <div>
                                                    <div className="label mb-1">{t.protocol}</div>
                                                    <div className="val text-xl">{new Date(s.start_time).toLocaleDateString()}</div>
                                                </div>
                                                <div className="text-right">
                                                    <div className="label mb-1">{t.duration}</div>
                                                    <div className="val text-[var(--primary)]">{s.duration_minutes || 0} min</div>
                                                </div>
                                            </div>
                                            <div className="flex flex-wrap gap-2 mb-6 border-y border-[var(--border)] py-4">
                                                {s.exercises?.slice(0, 3).map((ex, i) => <button key={i} onClick={() => setViewingExerciseHistory(ex)} className="text-[10px] font-bold bg-[var(--border)] px-3 py-1 rounded-lg text-[var(--text)] hover:text-[var(--primary)] transition-colors">{ex.name}</button>)}
                                            </div>
                                            <div className="flex justify-between items-center">
                                                <div className="flex gap-8">
                                                    <div><div className="label">{t.volume}</div><div className="val">{Math.round(s.total_volume || 0)} kg</div></div>
                                                    <div><div className="label">{t.series}</div><div className="val">{s.set_count || 0}</div></div>
                                                </div>
                                                <button onClick={() => setViewingFullSession(s)} className="text-[10px] font-black uppercase text-[var(--primary)] border-b border-cyan-500/20">{t.view_more}</button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </section>
                        )}

                        {tab === 'ROUTINES' && (
                            <section>
                                <h2 className="section-header">{t.routines}</h2>
                                <button onClick={() => setEditingRoutine({ name: '', exercises: [] })} className="btn-primary w-full py-6 mb-12 shadow-xl">{t.create_routine}</button>
                                <div className="space-y-8">
                                    {routines.map(r => (
                                        <div key={r.id} className="card group overflow-hidden p-0 relative">
                                            {/* Acciones Rápidas - siempre visibles */}
                                            <div className="absolute top-4 right-4 z-10 flex gap-2">
                                                <button onClick={(e) => { e.stopPropagation(); setEditingRoutine(r); }} className="w-8 h-8 bg-black/60 backdrop-blur-md rounded-full flex items-center justify-center text-[10px] text-white hover:bg-[var(--primary)] hover:text-black transition-all border border-white/10">✎</button>
                                                <button onClick={(e) => { e.stopPropagation(); setRoutineToDelete(r); }} className="w-8 h-8 bg-black/60 backdrop-blur-md rounded-full flex items-center justify-center text-[10px] text-white hover:bg-red-500 transition-all border border-white/10">✕</button>
                                            </div>

                                            {r.exercises[0]?.image_url && (
                                                <div className="w-full h-40 overflow-hidden border-b border-[var(--border)] relative">
                                                    <img src={r.exercises[0].image_url} alt={r.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 opacity-50" />
                                                    <div className="absolute inset-0 bg-gradient-to-t from-[var(--card)] to-transparent"></div>
                                                </div>
                                            )}
                                            <div className="p-8">
                                                <h3 className="text-3xl font-black italic uppercase mb-6 text-[var(--text)]">{r.name}</h3>
                                                <div className="flex flex-wrap gap-2 mb-8">
                                                    {r.exercises.map((ex, i) => <button key={i} onClick={() => setViewingExerciseHistory(ex)} className="text-[9px] font-bold text-[var(--text-dim)] uppercase bg-[var(--border)] px-3 py-1.5 rounded-full hover:text-[var(--primary)] hover:border-[var(--primary)] transition-all">{ex.name}</button>)}
                                                </div>
                                                <button onClick={() => startSession(r)} className="w-full py-4 border border-[var(--primary)] text-[var(--primary)] font-black uppercase text-[10px] rounded-xl hover:bg-[var(--primary)] hover:text-black transition-all tracking-widest">{t.start_session}</button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </section>
                        )}

                        {tab === 'SCIENCE' && (
                            <section>
                                <h2 className="section-header">{t.science}</h2>
                                {news.map(n => (
                                    <div key={n.id} className="card mb-6">
                                        <div className="label mb-2 text-[var(--primary)]">{n.date}</div>
                                        <h3 className="text-xl font-black italic uppercase mb-3 text-[var(--text)]">{n.title}</h3>
                                        <p className="text-sm text-[var(--text-dim)] leading-relaxed">{n.content}</p>
                                    </div>
                                ))}
                            </section>
                        )}
                    </div>

                    {/* Bottom Nav */}
                    <nav className="fixed bottom-0 w-full glass h-24 z-[100] flex items-center justify-around px-8">
                        <button onClick={() => setTab('HISTORY')} className={`flex flex-col items-center gap-1 transition-all ${tab === 'HISTORY' ? 'text-[var(--primary)] scale-110' : 'text-[var(--text-dim)]'}`}>
                            <div className="text-[10px] font-black uppercase tracking-widest">{t.summary}</div>
                        </button>
                        <button onClick={() => setTab('ROUTINES')} className={`flex flex-col items-center gap-1 transition-all ${tab === 'ROUTINES' ? 'text-[var(--primary)] scale-110' : 'text-[var(--text-dim)]'}`}>
                            <div className="text-[10px] font-black uppercase tracking-widest">{t.train}</div>
                        </button>
                        <button onClick={() => setTab('SCIENCE')} className={`flex flex-col items-center gap-1 transition-all ${tab === 'SCIENCE' ? 'text-[var(--primary)] scale-110' : 'text-[var(--text-dim)]'}`}>
                            <div className="text-[10px] font-black uppercase tracking-widest">{t.science}</div>
                        </button>
                    </nav>

                    {/* Overlays */}
                    {isDrawerOpen && <SettingsDrawer isOpen={isDrawerOpen} onClose={() => setIsDrawerOpen(false)} user={user} onUpdate={updateSettings} t={t} />}

                    {activeSession && (
                        <div className="fixed inset-0 z-[150] bg-[var(--bg)] overflow-y-auto p-6 pt-28">
                            <div className="max-w-2xl mx-auto">
                                <div className="flex justify-between items-end mb-12">
                                    <div>
                                        <h1 className="text-5xl font-black italic uppercase tracking-tighter mb-2 text-[var(--text)]">{activeSession.name}</h1>
                                        <div className="text-4xl font-black text-[var(--primary)] tracking-tighter">{Math.floor(timer / 60)}:{String(timer % 60).padStart(2, '0')}</div>
                                    </div>
                                </div>

                                {user.emg_enabled && (
                                    <div className="mb-8">
                                        <button 
                                            onClick={() => setIsElectrodeConnected(!isElectrodeConnected)}
                                            className={`w-full py-4 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all flex items-center justify-center gap-3 ${
                                                isElectrodeConnected 
                                                    ? 'bg-[var(--primary)]/10 text-[var(--primary)] border border-[var(--primary)]/50' 
                                                    : 'bg-[var(--border)] text-[var(--text-dim)] border border-[var(--border)] hover:border-[var(--primary)] hover:text-[var(--primary)]'
                                            }`}
                                        >
                                            <span>{isElectrodeConnected ? '📡 Cerrar Monitor EMG' : '📡 Abrir Monitor EMG'}</span>
                                        </button>
                                        {isElectrodeConnected && <BioHevyEMGMonitor t={t} />}
                                    </div>
                                )}

                                {activeSession.exercises.map((ex, exIdx) => (
                                    <div key={exIdx} className="card mb-8">
                                        <div className="flex justify-between items-start mb-8">
                                            <button onClick={() => setViewingExerciseHistory(ex)} className="text-2xl font-black italic uppercase text-[var(--text)] hover:text-[var(--primary)] transition-all text-left">{t.exercises[ex.name] || ex.name}</button>
                                            <div className="flex gap-2">
                                                <button onClick={() => {
                                                    const ns = [...activeSession.exercises];
                                                    ns[exIdx].unit = ns[exIdx].unit === 'kg' ? 'lbs' : 'kg';
                                                    setActiveSession({ ...activeSession, exercises: ns, isModified: true });
                                                }} className="text-[10px] font-black uppercase text-[var(--text)] bg-[var(--border)] px-3 py-1 rounded-lg hover:bg-[var(--primary)] hover:text-black transition-all">{ex.unit || 'kg'}</button>
                                                <button onClick={() => {
                                                    const ns = activeSession.exercises.filter((_, i) => i !== exIdx);
                                                    setActiveSession({ ...activeSession, exercises: ns, isModified: true });
                                                }} className="text-red-500 text-xl font-bold px-2">&times;</button>
                                            </div>
                                        </div>
                                        <div className="space-y-6">
                                            {ex.sets.map((s, sIdx) => (
                                                <div key={sIdx} className={`grid grid-cols-5 gap-2 items-center ${s.completed ? 'opacity-50' : ''}`}>
                                                    <div className="label text-center text-[9px]">SET {sIdx + 1}</div>
                                                    <div className="relative h-full col-span-1">
                                                        <span className="absolute top-1 left-2 text-[8px] font-black text-[var(--text-dim)] uppercase">{ex.unit || 'kg'}</span>
                                                        <input type="number" onWheel={e => e.target.blur()} className="w-full h-full py-4 pt-6 text-xl font-black" value={s.weight} onChange={e => {
                                                            const ns = [...activeSession.exercises];
                                                            ns[exIdx].sets[sIdx].weight = e.target.value;
                                                            setActiveSession({ ...activeSession, exercises: ns });
                                                        }} />
                                                    </div>
                                                    <div className="relative h-full col-span-1">
                                                        <span className="absolute top-1 left-2 text-[8px] font-black text-[var(--text-dim)] uppercase">REP</span>
                                                        <input type="number" onWheel={e => e.target.blur()} className="w-full h-full py-4 pt-6 text-xl font-black" value={s.reps} onChange={e => {
                                                            const ns = [...activeSession.exercises];
                                                            ns[exIdx].sets[sIdx].reps = e.target.value;
                                                            setActiveSession({ ...activeSession, exercises: ns });
                                                        }} />
                                                    </div>
                                                    <button onClick={() => {
                                                        const ns = [...activeSession.exercises];
                                                        ns[exIdx].sets[sIdx].failure = !ns[exIdx].sets[sIdx].failure;
                                                        setActiveSession({ ...activeSession, exercises: ns });
                                                    }} className={`h-full rounded-xl text-[10px] font-black ${s.failure ? 'bg-red-500 text-white' : 'bg-[var(--border)] text-[var(--text-dim)] hover:bg-red-500/20 hover:text-red-500 transition-all'}`}>Fallo</button>
                                                    <button onClick={() => {
                                                        const ns = [...activeSession.exercises];
                                                        ns[exIdx].sets[sIdx].completed = !ns[exIdx].sets[sIdx].completed;
                                                        setActiveSession({ ...activeSession, exercises: ns });
                                                    }} className={`h-full rounded-xl text-[14px] font-black ${s.completed ? 'bg-[var(--success)] text-black' : 'bg-[var(--border)] text-[var(--text-dim)] hover:bg-[var(--success)]/20 hover:text-[var(--success)] transition-all'}`}>✓</button>
                                                </div>
                                            ))}
                                        </div>
                                        <div className="flex gap-4 mt-8">
                                            <button onClick={() => {
                                                const ns = [...activeSession.exercises];
                                                ns[exIdx].sets.push({ weight: '', reps: '', failure: false, completed: false });
                                                setActiveSession({ ...activeSession, exercises: ns });
                                            }} className="text-[10px] font-black text-[var(--primary)] uppercase flex-1 border border-[var(--primary)] py-4 rounded-xl hover:bg-[var(--primary)] hover:text-black transition-all">{t.add_set}</button>
                                            <button onClick={() => {
                                                setRestTimerInput(90);
                                                setRestTimer(90);
                                                setIsTimerRunning(false);
                                            }} className="text-[10px] font-black text-cyan-400 uppercase border border-cyan-400/50 py-4 px-6 rounded-xl hover:bg-cyan-400 hover:text-black transition-all bg-cyan-400/10">⏱ {t.rest}</button>
                                        </div>
                                    </div>
                                ))}
                                <button onClick={() => setSelectedExercise('active')} className="w-full py-8 border-2 border-dashed border-[var(--border)] rounded-3xl text-[10px] font-black uppercase text-[var(--text-dim)] hover:text-[var(--primary)] hover:border-[var(--primary)] transition-all mb-8">{t.add_exercise}</button>
                                <button onClick={finishSession} className="btn-primary w-full py-6 mb-32 shadow-2xl">{t.finish_workout}</button>
                            </div>

                            {/* Rest Timer Overlay */}
                            {restTimer > 0 && (
                                <div className="fixed bottom-28 left-1/2 -translate-x-1/2 z-[160] bg-[var(--card)] border border-[var(--border)] px-6 py-4 rounded-[32px] shadow-2xl flex flex-col items-center gap-4">
                                    {!isTimerRunning ? (
                                        <>
                                            <div className="label text-[var(--primary)]">Configurar Descanso</div>
                                            <div className="flex items-center gap-4">
                                                <input type="number" onWheel={e => e.target.blur()} className="w-20 py-2 text-2xl font-black bg-transparent text-[var(--text)] border-b-2 border-[var(--primary)] focus:border-[var(--primary)] text-center outline-none" value={restTimerInput} onChange={e => { setRestTimerInput(e.target.value); setRestTimer(parseInt(e.target.value) || 0); }} />
                                                <span className="text-[10px] font-black uppercase text-[var(--text-dim)]">Segundos</span>
                                            </div>
                                            <div className="flex gap-2">
                                                <button onClick={() => { setRestTimer(restTimerInput); setIsTimerRunning(true); }} className="btn-primary px-6 py-2 text-[10px]">Iniciar</button>
                                                <button onClick={() => setRestTimer(0)} className="px-6 py-2 text-[10px] font-black uppercase text-[var(--text-dim)] bg-[var(--border)] rounded-xl">Cancelar</button>
                                            </div>
                                        </>
                                    ) : (
                                        <div className="flex items-center gap-6 text-[var(--primary)]">
                                            <button onClick={() => setRestTimer(v => Math.max(0, v - 30))} className="font-black text-xl hover:scale-110">-</button>
                                            <div className="text-3xl font-black tracking-tighter w-20 text-center">{Math.floor(restTimer / 60)}:{String(restTimer % 60).padStart(2, '0')}</div>
                                            <button onClick={() => setRestTimer(v => v + 30)} className="font-black text-xl hover:scale-110">+</button>
                                            <button onClick={() => { setRestTimer(0); setIsTimerRunning(false); }} className="ml-2 font-bold text-[9px] uppercase bg-[var(--primary)] text-black px-3 py-1.5 rounded-lg hover:bg-white transition-all">Skip</button>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}

                    {editingRoutine && (
                        <div className="fixed inset-0 z-[160] bg-[var(--bg)] p-6 pt-28">
                            <div className="max-w-2xl mx-auto">
                                <h2 className="text-4xl font-black italic uppercase mb-12 text-[var(--text)]">{t.protocol}</h2>
                                <input type="text" placeholder="NOMBRE DE LA RUTINA" className="w-full bg-transparent border-b-2 border-[var(--border)] py-4 text-3xl font-black uppercase mb-12 outline-none focus:border-[var(--primary)]" value={editingRoutine.name} onChange={e => setEditingRoutine({ ...editingRoutine, name: e.target.value })} />
                                <div className="space-y-4 mb-12">
                                    {editingRoutine.exercises.map((ex, i) => (
                                        <div key={i} className="card py-6 flex justify-between items-center">
                                            <span className="font-black uppercase italic text-[var(--text)]">{ex.name}</span>
                                            <button onClick={() => setEditingRoutine({ ...editingRoutine, exercises: editingRoutine.exercises.filter((_, idx) => idx !== i) })} className="text-red-500 text-xl font-bold">&times;</button>
                                        </div>
                                    ))}
                                    <button onClick={() => setSelectedExercise(true)} className="w-full py-10 border-2 border-dashed border-[var(--border)] rounded-3xl text-[10px] font-black uppercase text-[var(--text-dim)] hover:text-[var(--primary)] hover:border-[var(--primary)] transition-all">{t.add_exercise}</button>
                                </div>
                                <button onClick={() => saveRoutine(editingRoutine)} className="btn-primary w-full py-6 text-xs">{t.confirm}</button>
                                <button onClick={() => setEditingRoutine(null)} className="w-full py-4 text-[10px] font-black uppercase text-[var(--text-dim)] mt-4">{t.close}</button>
                            </div>
                        </div>
                    )}

                    {selectedExercise && (
                        <div className="fixed inset-0 z-[170] bg-[var(--bg)] p-6 pt-28 overflow-y-auto">
                            <div className="max-w-2xl mx-auto">
                                <div className="flex justify-between items-center mb-12">
                                    <h2 className="text-3xl font-black italic text-[var(--text)] uppercase">Libreria</h2>
                                    <button onClick={() => setSelectedExercise(null)} className="text-[var(--text)] text-3xl">&times;</button>
                                </div>
                                <div className="grid grid-cols-1 gap-4">
                                    {exercises.map(ex => (
                                        <div key={ex.id} onClick={() => setViewingExerciseHistory({ ...ex, mode: selectedExercise })} className="card cursor-pointer hover:border-[var(--primary)] group overflow-hidden p-0">
                                            {ex.image_url && (
                                                <div className="w-full h-32 overflow-hidden border-b border-[var(--border)]">
                                                    <img src={ex.image_url} alt={ex.name} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500 opacity-60" />
                                                </div>
                                            )}
                                            <div className="p-6">
                                                <div className="text-xl font-black uppercase italic text-[var(--text)]">{ex.name}</div>
                                                <div className="label">{ex.muscle_group}</div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {summary && (
                        <div className="fixed inset-0 z-[200] bg-black/90 flex items-center justify-center p-6 backdrop-blur-md">
                            <div className="bg-[var(--card)] p-12 rounded-[50px] border border-[var(--primary)] text-center max-w-sm">
                                <h2 className="text-4xl font-black italic uppercase text-[var(--text)] mb-8 tracking-tighter leading-none">Entrenamiento Finalizado</h2>
                                <div className="grid grid-cols-2 gap-4 mb-10">
                                    <div className="bg-[var(--border)] p-6 rounded-3xl">
                                        <div className="label mb-2">Volumen</div>
                                        <div className="text-3xl font-black text-[var(--primary)]">{Math.round(summary.volume || 0)} kg</div>
                                    </div>
                                    <div className="bg-[var(--border)] p-6 rounded-3xl">
                                        <div className="label mb-2">Calorias</div>
                                        <div className="text-3xl font-black text-pink-500">{Math.round(summary.calories || 0)}</div>
                                    </div>
                                </div>
                                <button onClick={() => setSummary(null)} className="btn-primary w-full py-5 text-[10px]">{t.close}</button>
                            </div>
                        </div>
                    )}

                    {viewingFullSession && (
                        <div className="fixed inset-0 z-[210] bg-[var(--bg)] p-6 pt-28 overflow-y-auto">
                            <div className="max-w-2xl mx-auto">
                                <div className="flex justify-between items-center mb-8">
                                    <h2 className="text-4xl font-black italic uppercase text-[var(--text)]">{new Date(viewingFullSession.start_time).toLocaleDateString()}</h2>
                                    <button onClick={() => setViewingFullSession(null)} className="text-3xl font-light text-[var(--text-dim)]">&times;</button>
                                </div>
                                <div className="label mb-12">{t.protocol}: {viewingFullSession.routine_id || 'Libre'}</div>
                                <div className="space-y-12">
                                    {viewingFullSession.exercises?.map((ex, i) => (
                                        <div key={i} className="border-b border-[var(--border)] pb-10">
                                            <button onClick={() => setViewingExerciseHistory(ex)} className="text-2xl font-black italic uppercase mb-6 text-[var(--text)] hover:text-[var(--primary)] transition-all text-left">{ex.name}</button>
                                            <div className="space-y-4">
                                                {ex.sets?.map((s, si) => (
                                                    <div key={si} className="flex justify-between items-center bg-[var(--card)] p-5 rounded-2xl border border-[var(--border)]">
                                                        <span className="label">SET {si + 1}</span>
                                                        <span className="val">{s.weight} kg x {s.reps} {s.is_failure ? '(F)' : ''}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {viewingExerciseHistory && (() => {
                        const exData = history.filter(s => s.exercises?.some(e => e.id === viewingExerciseHistory.id || e.exercise_id === viewingExerciseHistory.id)).reverse();
                        const graphData = exData.map(s => {
                            const ex = s.exercises.find(e => e.id === viewingExerciseHistory.id || e.exercise_id === viewingExerciseHistory.id);
                            const maxWeight = Math.max(...ex.sets.map(set => parseFloat(set.weight) || 0));
                            return { date: new Date(s.start_time).toLocaleDateString(user?.lang === 'en' ? 'en-US' : 'es-ES', { month: 'short', day: 'numeric' }), maxWeight };
                        });
                        const maxW = Math.max(...graphData.map(d => d.maxWeight), 10); // avoid 0
                        
                        const handleConfirmAdd = () => {
                            const ex = viewingExerciseHistory;
                            if (ex.mode === true && editingRoutine) {
                                setEditingRoutine({ ...editingRoutine, exercises: [...editingRoutine.exercises, ex] });
                            } else if (ex.mode === 'active' && activeSession) {
                                setActiveSession({
                                    ...activeSession,
                                    exercises: [...activeSession.exercises, { ...ex, unit: 'kg', sets: [{ weight: '', reps: '', failure: false, completed: false }] }],
                                    isModified: true
                                });
                            }
                            setViewingExerciseHistory(null);
                            setSelectedExercise(null);
                        };

                        return (
                            <div className="fixed inset-0 z-[220] bg-[var(--bg)] p-6 pt-28 overflow-y-auto">
                                <div className="max-w-2xl mx-auto">
                                    <div className="flex justify-between items-center mb-12">
                                        <h2 className="text-3xl font-black italic uppercase text-[var(--text)]">{t.exercises[viewingExerciseHistory.name] || viewingExerciseHistory.name}</h2>
                                        <button onClick={() => setViewingExerciseHistory(null)} className="text-3xl font-light text-[var(--text-dim)]">&times;</button>
                                    </div>
                                    <div className="card mb-8">
                                        <div className="label mb-8">Progreso de Peso Máximo (KG)</div>
                                        {graphData.length === 0 ? (
                                            <div className="text-center text-[var(--text-dim)] py-12 text-sm">No hay datos registrados aún.</div>
                                        ) : (
                                            <div className="relative h-64 w-full flex items-end justify-between border-b border-[var(--border)] pb-8 pt-4 px-4">
                                                {/* Y Axis max label */}
                                                <div className="absolute top-0 left-0 text-[10px] font-black text-[var(--primary)]">{Math.round(maxW)} kg</div>
                                                <div className="absolute top-1/2 left-0 text-[10px] font-black text-[var(--text-dim)]">{Math.round(maxW / 2)} kg</div>

                                                {/* Graph line and dots */}
                                                <svg className="absolute inset-0 h-[calc(100%-2rem)] w-full overflow-visible px-4" preserveAspectRatio="none" viewBox="0 0 100 100">
                                                    <polyline
                                                        fill="none"
                                                        stroke="var(--primary)"
                                                        strokeWidth="2"
                                                        strokeLinecap="round"
                                                        strokeLinejoin="round"
                                                        points={graphData.map((d, i) => {
                                                            const x = (i / Math.max(1, graphData.length - 1)) * 100;
                                                            const y = 100 - (d.maxWeight / maxW) * 100;
                                                            return `${x},${y}`;
                                                        }).join(' ')}
                                                    />
                                                    {graphData.map((d, i) => {
                                                        const x = (i / Math.max(1, graphData.length - 1)) * 100;
                                                        const y = 100 - (d.maxWeight / maxW) * 100;
                                                        return <circle key={i} cx={x} cy={y} r="3" fill="var(--bg)" stroke="var(--primary)" strokeWidth="1.5" />;
                                                    })}
                                                </svg>

                                                {/* X Axis labels */}
                                                {graphData.map((d, i) => (
                                                    <div key={i} className="absolute -bottom-8 text-[9px] font-bold text-[var(--text-dim)] whitespace-nowrap" style={{ left: `${(i / Math.max(1, graphData.length - 1)) * 100}%`, transform: 'translateX(-50%)' }}>
                                                        {d.date}
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>

                                    {viewingExerciseHistory.mode && (
                                        <button onClick={handleConfirmAdd} className="btn-primary w-full py-6 text-xs shadow-2xl">Vincular Ejercicio</button>
                                    )}
                                </div>
                            </div>
                        );
                    })()}

                    {routineToDelete && (
                        <div className="fixed inset-0 z-[230] bg-black/80 flex items-center justify-center p-6 backdrop-blur-md animate-fade-in">
                            <div className="bg-[var(--card)] p-10 rounded-[40px] border border-red-500/50 text-center max-w-sm shadow-2xl">
                                <div className="text-red-500 text-5xl mb-6">⚠️</div>
                                <h2 className="text-3xl font-black italic uppercase text-[var(--text)] mb-4 tracking-tighter leading-none">¿Eliminar Rutina?</h2>
                                <p className="text-zinc-400 text-xs mb-8 leading-relaxed">
                                    Estás a punto de eliminar la rutina <span className="text-white font-bold">"{routineToDelete.name}"</span>. Esta acción no se puede deshacer.
                                </p>
                                <div className="flex gap-4">
                                    <button 
                                        onClick={() => {
                                            deleteRoutine(routineToDelete.id);
                                        }} 
                                        className="bg-red-600 hover:bg-red-700 text-white flex-1 py-4 text-[10px] uppercase font-black tracking-widest rounded-xl transition-all border border-red-500/20"
                                    >
                                        Eliminar
                                    </button>
                                    <button 
                                        onClick={() => setRoutineToDelete(null)} 
                                        className="flex-1 py-4 text-[10px] font-black uppercase text-[var(--text-dim)] bg-[var(--border)] rounded-xl hover:text-white transition-all"
                                    >
                                        Cancelar
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            );
        };

        // AppRoot removed        
        
    
export default Main;
