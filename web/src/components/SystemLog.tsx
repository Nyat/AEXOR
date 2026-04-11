import { useRef, useEffect, useState } from 'react';

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
  const [height, setHeight] = useState(200);
  const logContainerRef = useRef<HTMLDivElement>(null);
  const isDraggingRef = useRef(false);
  const startYRef = useRef(0);
  const startHRef = useRef(200);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDraggingRef.current) return;
      const dy = startYRef.current - e.clientY;
      const newHeight = Math.max(100, Math.min(600, startHRef.current + dy));
      setHeight(newHeight);
    };

    const handleMouseUp = () => {
      isDraggingRef.current = false;
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = 0;
    }
  }, [logs]);

  return (
    <div className="absolute bottom-0 left-0 w-full flex flex-col bg-[#0A0A0B] border-t border-white/5 font-mono text-[11px] overflow-hidden no-drag z-50" style={{ height: `${height}px` }}>
      
      {/* Resize Handle */}
      <div 
        className="absolute top-0 left-0 w-full h-2 cursor-row-resize hover:bg-white/5 z-10 transition-colors flex items-center justify-center group/resize"
        onMouseDown={(e) => {
          isDraggingRef.current = true;
          startYRef.current = e.clientY;
          startHRef.current = height;
        }}
      >
         <div className="w-12 h-[2px] bg-white/10 group-hover/resize:bg-[#00F3FF]/50 rounded-full"></div>
      </div>
      
      <div className="p-6 pb-2 flex-1 flex flex-col min-h-0">
        <div className="flex items-center justify-between mb-4 pb-2 w-full">
          <div className="flex items-center gap-4 flex-shrink-0">
            <span className="font-orbitron tracking-[0.3em] uppercase text-[10px] text-white drop-shadow-[0_0_5px_rgba(255,255,255,0.3)]">SYSTEM_LOG // CONSOLE</span>
          </div>
          
          <div className="flex-1 h-[1px] bg-white/10 mx-6 opacity-30 mt-1"></div>
          
          <div className="flex items-center gap-6 flex-shrink-0">
            <button 
               onClick={() => setHeight(200)}
               className="px-3 py-1 rounded border border-white/10 text-gray-500 hover:text-[#00F3FF] hover:border-[#00F3FF]/30 text-[9px] tracking-widest font-anta transition-all bg-white/5 uppercase"
            >
              DEFAULT
            </button>
          </div>
        </div>
        
        {/* Status Header */}
        {isTaskRunning ? (
          <div className="text-[#00FF00] uppercase tracking-[0.2em] text-[10px] mb-4 flex items-center gap-3 bg-[#00FF00]/5 p-2 rounded border border-[#00FF00]/20 flex-shrink-0">
            <span className="animate-pulse">●</span> EXECUTING_{activeModule}_SEQUENCE{dots}
          </div>
        ) : (
          <div className="text-[#00F3FF] uppercase tracking-[0.2em] text-[10px] mb-4 flex items-center gap-3 drop-shadow-[0_0_8px_rgba(0,243,255,0.4)] flex-shrink-0">
            <span>AWAITING_SEQUENCE_INITIATION{dots}</span>
          </div>
        )}

        <div 
          ref={logContainerRef} 
          className="flex-1 overflow-y-auto space-y-1.5 custom-scrollbar pr-2 min-h-0 pb-4 block"
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
    </div>
  );
};
