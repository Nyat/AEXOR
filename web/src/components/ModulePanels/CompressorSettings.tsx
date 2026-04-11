

interface CompressorSettingsProps {
  quality: number;
  setQuality: (val: string) => void;
}

export const CompressorSettings = ({ quality, setQuality }: CompressorSettingsProps) => {
  return (
    <div className="flex items-center gap-3">
       <span className="text-[10px] font-orbitron text-[#00F3FF] uppercase font-bold tracking-widest drop-shadow-[0_0_5px_rgba(0,243,255,0.4)]">Quality: {quality}%</span>
      <input 
        type="range" 
        className="w-24 accent-[#00F3FF]" 
        value={quality} 
        onChange={(e) => setQuality(e.target.value)} 
      />
    </div>
  );
};
