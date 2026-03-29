import React, { useRef, useEffect } from 'react';

interface LogEntry {
  text: string;
  type: 'info' | 'success' | 'error' | 'progress';
}

interface SystemLogProps {
  logs: LogEntry[];
  isTaskRunning: boolean;
  activeModule: string;
  dots: string;
}

export const SystemLog = ({ logs, isTaskRunning, activeModule, dots }: SystemLogProps) => {
  const logContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = 0; // The logs are prepended in Dashboard.tsx
    }
  }, [logs]);

  return (
    <div className="flex-1 flex flex-col bg-black/60 border-t border-white/5 p-6 font-mono text-[11px] overflow-hidden">
      <div className="flex items-center gap-2 mb-4 opacity-50">
        <span className="font-orbitron tracking-[0.3em] uppercase text-[10px] text-white">SYSTEM_LOG // CONSOLE</span>
        <div className="flex-1 h-[1px] bg-white/5 ml-4"></div>
      </div>
      
      {/* Status Header */}
      {isTaskRunning ? (
        <div className="text-[#00FF00] uppercase tracking-[0.2em] text-[10px] mb-4 flex items-center gap-3 bg-[#00FF00]/5 p-2 rounded border border-[#00FF00]/20">
          <span className="animate-pulse">●</span> EXECUTING_{activeModule}_SEQUENCE{dots}
        </div>
      ) : (
        <div className="text-[#00F3FF] uppercase tracking-[0.2em] text-[10px] mb-4 flex items-center gap-3 drop-shadow-[0_0_8px_rgba(0,243,255,0.4)]">
          <span>AWAITING_SEQUENCE_INITIATION{dots}</span>
        </div>
      )}

      <div 
        ref={logContainerRef} 
        className="flex-1 overflow-y-auto space-y-1.5 custom-scrollbar pb-4 pr-2"
        style={{ display: 'flex', flexDirection: 'column' }}
      >
        {logs.map((log, i) => (
          <div key={i} className={`tracking-wider leading-relaxed ${
            log.type === 'error' ? 'text-[#FF00FF]' : 
            log.type === 'success' ? 'text-[#00FF00]' : 
            log.type === 'progress' ? 'text-[#00FF00]' : 
            'text-gray-500'
          }`}>
            {log.text}
          </div>
        ))}
      </div>
    </div>
  );
};
