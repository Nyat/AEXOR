

interface ConverterSettingsProps {
  format: string;
  setFormat: (val: string) => void;
}

export const ConverterSettings = ({ format, setFormat }: ConverterSettingsProps) => {
  return (
    <div className="flex gap-2">
      {['JPG', 'PNG', 'WEBP'].map(f => (
        <button 
          key={f}
          onClick={() => setFormat(f)}
          className={`px-3 py-1 text-[10px] font-orbitron tracking-widest border transition-all ${format === f ? 'bg-[#00F3FF]/20 border-[#00F3FF] text-[#00F3FF]' : 'border-white/10 text-gray-600'}`}
        >
          {f}
        </button>
      ))}
    </div>
  );
};
