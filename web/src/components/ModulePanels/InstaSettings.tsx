import { Info } from 'lucide-react';

interface InstaSettingsProps {
  instaUrl: string;
  setInstaUrl: (val: string) => void;
  instaSessionId: string;
  setInstaSessionId: (val: string) => void;
}

export const InstaSettings = ({ instaUrl, setInstaUrl, instaSessionId, setInstaSessionId }: InstaSettingsProps) => {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <div className="font-anta text-[10px] tracking-[0.3em] uppercase opacity-50">IG_MEDIA_ENDPOINT</div>
        <input
          type="text"
          placeholder="Paste Instagram Post/Reel URL here..."
          className="w-full bg-white/5 border border-white/10 p-4 rounded font-oxanium text-white focus:border-[#00F3FF] outline-none transition-colors text-sm placeholder:text-gray-700 shadow-inner"
          value={instaUrl}
          onChange={(e) => setInstaUrl(e.target.value)}
        />
      </div>
      
      <div className="flex flex-col gap-2">
        <div className="font-anta text-[10px] tracking-[0.3em] uppercase flex items-center gap-2">
          <span className="opacity-50">NEURAL_SESSION_KEY</span>
          <span className="text-[#00F3FF]/40 text-[8px]">(COOKIE_SESSIONID)</span>
          <div className="relative group/info inline-flex items-center">
            <Info size={12} className="text-[#00F3FF]/50 hover:text-[#00F3FF] transition-colors cursor-pointer" />
            <div className="absolute left-5 bottom-full mb-1.5 w-72 p-3 bg-black/95 border border-[#00F3FF]/30 rounded-lg shadow-[0_0_20px_rgba(0,243,255,0.15)] opacity-0 pointer-events-none group-hover/info:opacity-100 transition-opacity duration-200 z-50 font-oxanium tracking-wide normal-case">
              <div className="font-orbitron text-[9px] text-[#00F3FF] tracking-[0.15em] uppercase mb-1.5 border-b border-white/10 pb-1">
                HOW TO GET SESSIONID
              </div>
              <ol className="text-[10px] text-gray-300 space-y-1 list-decimal list-inside leading-relaxed">
                <li>Log in to <span className="text-white">instagram.com</span> on your browser.</li>
                <li>Press <span className="text-[#00F3FF]">F12</span> (DevTools) &rarr; <span className="text-white">Application</span> tab.</li>
                <li>Open <span className="text-white">Cookies</span> &rarr; <span className="text-white">https://www.instagram.com</span>.</li>
                <li>Find <span className="text-[#00F3FF] font-mono">sessionid</span> and copy its <span className="text-white">Value</span>.</li>
              </ol>
            </div>
          </div>
        </div>
        <div className="relative group/session">
          <input
            type="password"
            placeholder="Paste your sessionid from browser cookies..."
            className="w-full bg-black/40 border border-white/5 p-4 rounded font-mono text-[11px] text-[#00F3FF]/80 focus:border-[#00F3FF]/50 outline-none transition-all placeholder:text-gray-800 pr-12 focus:bg-black/60"
            value={instaSessionId}
            onChange={(e) => setInstaSessionId(e.target.value)}
          />
        </div>
      </div>
    </div>
  );
};
