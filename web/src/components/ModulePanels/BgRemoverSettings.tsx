interface BgRemoverSettingsProps {
  format: 'PNG' | 'WEBP';
  setFormat: (val: 'PNG' | 'WEBP') => void;
}

export const BgRemoverSettings = ({ format, setFormat }: BgRemoverSettingsProps) => {
  return (
    <div className="flex gap-2 items-center">
      <span className="text-[10px] font-orbitron text-gray-400 tracking-[0.2em] uppercase">OUTPUT:</span>
      {(['PNG', 'WEBP'] as const).map(f => (
        <button 
          key={f}
          type="button"
          onClick={() => setFormat(f)}
          className={`px-3 py-1 text-[10px] font-orbitron tracking-widest border transition-all cursor-pointer ${
            format === f 
              ? 'bg-[#00F3FF]/20 border-[#00F3FF] text-[#00F3FF] shadow-[0_0_8px_rgba(0,243,255,0.3)]' 
              : 'border-white/10 text-gray-500 hover:text-white hover:border-white/30'
          }`}
        >
          {f}
        </button>
      ))}
    </div>
  );
};
