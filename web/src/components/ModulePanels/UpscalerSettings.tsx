

interface UpscalerSettingsProps {
  upscale: number;
  setUpscale: (val: number) => void;
}

export const UpscalerSettings = ({ upscale, setUpscale }: UpscalerSettingsProps) => {
  return (
    <div className="flex gap-4 items-center">
      <div className="flex gap-2">
        {[2, 4].map(s => (
          <button 
            key={s}
            onClick={() => setUpscale(s)}
            className={`px-3 py-1 text-[10px] font-orbitron tracking-widest border transition-all ${upscale === s ? 'bg-[#00F3FF]/20 border-[#00F3FF] text-[#00F3FF]' : 'border-white/10 text-gray-600'}`}
          >
            {s}X
          </button>
        ))}
      </div>
    </div>
  );
};
