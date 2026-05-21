"use client";

import { useUser } from "@clerk/nextjs";
import Dashboard from "../components/Dashboard";

export default function Home() {
  const { isSignedIn, isLoaded, user } = useUser();

  // Wait for Clerk to fully hydrate before rendering anything
  if (!isLoaded) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black">
        <div className="text-center">
          <div className="text-4xl font-black italic uppercase tracking-tighter text-white mb-4">
            Bio<span className="text-[var(--primary)]">Hevy</span>
          </div>
          <div className="w-8 h-8 border-2 border-[var(--primary)] border-t-transparent rounded-full animate-spin mx-auto"></div>
        </div>
      </div>
    );
  }

  if (isSignedIn) {
    return <Dashboard clerkUser={user} />;
  }

  return (
    <div className="min-h-[calc(100vh-80px)] flex flex-col items-center text-center px-6 py-24">
      <div className="inline-block border border-[var(--primary)] text-[var(--primary)] px-4 py-1 rounded-full text-[10px] font-black uppercase tracking-widest mb-8 bg-[var(--primary)]/10">
        The BioMechanical Engine
      </div>
      <h1 className="text-5xl lg:text-7xl xl:text-8xl font-black tracking-tighter uppercase italic leading-[0.9] mb-8 text-white">
        Desata tu <br />
        <span className="text-transparent bg-clip-text bg-gradient-to-r from-[var(--primary)] to-cyan-700">
          Potencial
        </span>
      </h1>
      <p className="text-zinc-400 max-w-2xl mx-auto mb-12 text-sm md:text-lg leading-relaxed font-light">
        BioHevy integra análisis biomecánico real (EMG) con el seguimiento de hipertrofia más avanzado del mercado. Historial en la nube, métricas exactas, rendimiento profesional.
      </p>

      {/* Mockup Image Placeholder */}
      <div className="relative w-full max-w-5xl mx-auto rounded-3xl overflow-hidden border border-zinc-800 shadow-[0_0_120px_rgba(0,242,255,0.15)] ring-1 ring-white/10 group mt-12 bg-zinc-900 h-96 flex items-center justify-center">
        <span className="text-zinc-500 font-black tracking-widest uppercase">Mockup Dashboard UI</span>
      </div>
    </div>
  );
}
