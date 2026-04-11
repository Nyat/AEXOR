interface ResizerSettingsProps {
  resolutionLabel: string;
  setResolutionLabel: (val: string) => void;
  resizeMode: string;
  setResizeMode: (val: string) => void;
  bgColor: string;
  setBgColor: (val: string) => void;
}

export const ResizerSettings = ({ 
  resolutionLabel, setResolutionLabel, 
  resizeMode, setResizeMode, 
  bgColor, setBgColor 
}: ResizerSettingsProps) => {
  return (
    <div className="flex items-center gap-4">
      <div className="flex items-center gap-1 border border-white/10 rounded-lg p-0.5 bg-black/60 shadow-[0_4px_15px_rgba(0,0,0,0.5)]">
         {['HD', 'FHD', 'QHD', '4K'].map(res => (
           <button
             key={res}
             onClick={() => setResolutionLabel(res)}
             className={`px-3 py-1 font-orbitron text-[9px] tracking-widest rounded-md transition-all ${resolutionLabel === res ? 'bg-white text-black font-bold shadow-[0_0_10px_rgba(255,255,255,0.4)]' : 'text-gray-500 hover:text-white hover:bg-white/5'}`}
           >
             {res}
           </button>
         ))}
      </div>

      <div className="flex items-center gap-1 border border-white/10 rounded-lg p-0.5 bg-black/60 shadow-[0_4px_15px_rgba(0,0,0,0.5)]">
          <button 
            onClick={() => setResizeMode('FIT')}
            className={`px-3 py-1 font-orbitron text-[9px] tracking-widest rounded-md transition-all ${resizeMode === 'FIT' ? 'bg-[#00F3FF] text-black font-bold shadow-[0_0_10px_rgba(0,243,255,0.4)]' : 'text-gray-500 hover:text-white hover:bg-white/5'}`}
          >FIT</button>
          <button 
            onClick={() => setResizeMode('FILL')}
            className={`px-3 py-1 font-orbitron text-[9px] tracking-widest rounded-md transition-all ${resizeMode === 'FILL' ? 'bg-[#F205FF] text-black font-bold shadow-[0_0_10px_rgba(242,5,255,0.4)]' : 'text-gray-500 hover:text-white hover:bg-white/5'}`}
          >FILL</button>
      </div>

      {resizeMode === 'FIT' && (
        <div className="flex items-center gap-2 border border-white/10 rounded-lg p-1 bg-black/60">
           <button 
              onClick={() => setBgColor('BLACK')}
              className={`w-4 h-4 rounded-full border border-white/20 transition-all ${bgColor === 'BLACK' ? 'bg-black shadow-[0_0_8px_rgba(255,255,255,0.5)] scale-110' : 'bg-black hover:scale-110 opacity-50'}`} 
              title="Black Background"
           />
           <button 
              onClick={() => setBgColor('WHITE')}
              className={`w-4 h-4 rounded-full border border-white/20 transition-all ${bgColor === 'WHITE' ? 'bg-white shadow-[0_0_8px_rgba(255,255,255,0.8)] scale-110' : 'bg-white hover:scale-110 opacity-50'}`}
              title="White Background" 
           />
        </div>
      )}
    </div>
  );
};
