

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
        <div className="font-anta text-[10px] tracking-[0.3em] uppercase opacity-50 flex items-center gap-2">
          NEURAL_SESSION_KEY <span className="text-[#00F3FF]/30 text-[8px]">(COOKIE_SESSIONID)</span>
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
