import React from 'react';
import { Globe } from 'lucide-react';

const GroupBox = ({ children }: { children: React.ReactNode }) => (
  <div className="flex items-center gap-1 border border-white/10 rounded-lg p-0.5 bg-black/60 shadow-[0_4px_15px_rgba(0,0,0,0.5)]">
    {children}
  </div>
);

const PillBtn = ({
  active,
  label,
  onClick,
  accent = '#00F3FF'
}: {
  active: boolean;
  label: string;
  onClick: () => void;
  accent?: string;
}) => (
  <button
    type="button"
    onClick={onClick}
    style={
      active
        ? {
            backgroundColor: accent,
            color: '#000',
            boxShadow: `0 0 10px ${accent}66`
          }
        : undefined
    }
    className={`px-2.5 py-1 font-orbitron text-[9px] tracking-widest rounded-md transition-all cursor-pointer ${
      active ? 'font-bold' : 'text-gray-500 hover:text-white hover:bg-white/5'
    }`}
  >
    {label}
  </button>
);

export const MediaDownloaderView = ({
  mediaUrl,
  setMediaUrl,
  mediaMode,
  setMediaMode,
  mediaQuality,
  setMediaQuality
}: {
  mediaUrl: string;
  setMediaUrl: (v: string) => void;
  mediaMode: string;
  setMediaMode: (v: string) => void;
  mediaQuality: string;
  setMediaQuality: (v: string) => void;
}) => {
  return (
    <div className="flex-1 flex flex-col justify-center gap-5 border border-white/5 bg-black/30 rounded-xl p-6 mb-4 relative overflow-hidden">
      <div className="scanline-overlay opacity-10"></div>
      <div className="flex flex-col gap-2 relative z-10">
        <div className="font-anta text-[10px] tracking-[0.3em] uppercase text-[#F205FF] flex items-center gap-2">
          <Globe size={13} />
          <span>UNIVERSAL_STREAM_ENDPOINT (YOUTUBE / X / TIKTOK / SOUNDCLOUD / VIMEO)</span>
        </div>
        <input
          type="text"
          placeholder="Paste Video or Audio Stream URL here..."
          className="w-full bg-white/5 border border-white/10 p-4 rounded font-oxanium text-white focus:border-[#F205FF] outline-none transition-colors text-sm placeholder:text-gray-700 shadow-inner"
          value={mediaUrl}
          onChange={(e) => setMediaUrl(e.target.value)}
        />
      </div>

      <div className="flex flex-wrap items-center gap-4 relative z-10">
        <div className="flex items-center gap-2">
          <span className="font-oxanium text-[9px] text-gray-500 uppercase tracking-widest">STREAM_MODE:</span>
          <GroupBox>
            {['VIDEO_MP4', 'AUDIO_MP3', 'AUDIO_WAV'].map((m) => (
              <PillBtn key={m} active={mediaMode === m} label={m} accent="#F205FF" onClick={() => setMediaMode(m)} />
            ))}
          </GroupBox>
        </div>

        {mediaMode === 'VIDEO_MP4' && (
          <div className="flex items-center gap-2">
            <span className="font-oxanium text-[9px] text-gray-500 uppercase tracking-widest">MAX_RES:</span>
            <GroupBox>
              {['BEST', '1080P', '720P'].map((q) => (
                <PillBtn key={q} active={mediaQuality === q} label={q} accent="#00F3FF" onClick={() => setMediaQuality(q)} />
              ))}
            </GroupBox>
          </div>
        )}
      </div>
    </div>
  );
};

export const ExtendedModuleSettings = ({
  activeModule,
  settings,
  updateSettings
}: {
  activeModule: string;
  settings: any;
  updateSettings: (patch: Record<string, any>) => void;
}) => {
  if (activeModule === 'NEURAL_OCR') {
    return (
      <div className="flex items-center gap-3">
        <span className="font-oxanium text-[9px] text-gray-500 uppercase tracking-widest">OUTPUT:</span>
        <GroupBox>
          {['TXT', 'MD', 'JSON'].map((fmt) => (
            <PillBtn
              key={fmt}
              active={settings.ocrFormat === fmt}
              label={fmt}
              onClick={() => updateSettings({ ocrFormat: fmt })}
            />
          ))}
        </GroupBox>
      </div>
    );
  }

  if (activeModule === 'WATERMARK_REMOVER') {
    const regions = [
      { id: 'AUTO_DETECT', label: 'AUTO' },
      { id: 'BOTTOM_RIGHT', label: 'BTM_R' },
      { id: 'BOTTOM_LEFT', label: 'BTM_L' },
      { id: 'TOP_RIGHT', label: 'TOP_R' },
      { id: 'TOP_LEFT', label: 'TOP_L' },
      { id: 'CENTER_STAMP', label: 'CENTER' }
    ];
    return (
      <div className="flex items-center gap-3">
        <GroupBox>
          {regions.map((r) => (
            <PillBtn
              key={r.id}
              active={settings.wmRegion === r.id}
              label={r.label}
              onClick={() => updateSettings({ wmRegion: r.id })}
            />
          ))}
        </GroupBox>
        <GroupBox>
          {['TELEA', 'NS'].map((alg) => (
            <PillBtn
              key={alg}
              active={settings.wmAlgorithm === alg}
              label={alg}
              accent="#F205FF"
              onClick={() => updateSettings({ wmAlgorithm: alg })}
            />
          ))}
        </GroupBox>
      </div>
    );
  }

  if (activeModule === 'PALETTE_GENERATOR') {
    return (
      <div className="flex items-center gap-3">
        <GroupBox>
          {[5, 8, 10].map((cnt) => (
            <PillBtn
              key={cnt}
              active={settings.paletteCount === cnt}
              label={`${cnt}_COLORS`}
              onClick={() => updateSettings({ paletteCount: cnt })}
            />
          ))}
        </GroupBox>
        <GroupBox>
          {[
            { id: 'STUDIO_CARD', label: 'CARD' },
            { id: 'SWATCH_GRID', label: 'SWATCH' },
            { id: 'CARD_+_CSS', label: 'CARD+CSS' }
          ].map((exp) => (
            <PillBtn
              key={exp.id}
              active={settings.paletteMode === exp.id}
              label={exp.label}
              accent="#F205FF"
              onClick={() => updateSettings({ paletteMode: exp.id })}
            />
          ))}
        </GroupBox>
      </div>
    );
  }

  if (activeModule === 'VECTOR_TRACER') {
    return (
      <div className="flex items-center gap-3">
        <GroupBox>
          {['COLOR', 'BINARY'].map((cm) => (
            <PillBtn
              key={cm}
              active={settings.vectorColor === cm}
              label={cm}
              onClick={() => updateSettings({ vectorColor: cm })}
            />
          ))}
        </GroupBox>
        <GroupBox>
          {[
            { id: 'POSTER', label: 'POSTER' },
            { id: 'LOGO_SHARP', label: 'LOGO_SHARP' },
            { id: 'PHOTO_DETAILED', label: 'DETAILED' }
          ].map((pr) => (
            <PillBtn
              key={pr.id}
              active={settings.vectorPreset === pr.id}
              label={pr.label}
              accent="#F205FF"
              onClick={() => updateSettings({ vectorPreset: pr.id })}
            />
          ))}
        </GroupBox>
      </div>
    );
  }

  if (activeModule === 'PDF_FORGE') {
    return (
      <div className="flex items-center gap-3">
        <GroupBox>
          {[
            { id: 'IMAGES_TO_PDF', label: 'IMG_TO_PDF' },
            { id: 'PDF_TO_IMAGES', label: 'PDF_TO_IMG' },
            { id: 'COMPRESS_PDF', label: 'COMPRESS_PDF' }
          ].map((m) => (
            <PillBtn
              key={m.id}
              active={settings.pdfMode === m.id}
              label={m.label}
              onClick={() => updateSettings({ pdfMode: m.id })}
            />
          ))}
        </GroupBox>
        {settings.pdfMode === 'PDF_TO_IMAGES' && (
          <GroupBox>
            {[150, 300].map((d) => (
              <PillBtn
                key={d}
                active={settings.pdfDpi === d}
                label={`${d}_DPI`}
                accent="#F205FF"
                onClick={() => updateSettings({ pdfDpi: d })}
              />
            ))}
          </GroupBox>
        )}
      </div>
    );
  }

  if (activeModule === 'VIDEO_OPTIMIZER') {
    return (
      <div className="flex items-center gap-3">
        <GroupBox>
          {[
            { id: 'COMPRESS_MP4', label: 'MP4_OPT' },
            { id: 'GIF_FORGE', label: 'GIF_FORGE' },
            { id: 'ANIMATED_WEBP', label: 'ANIM_WEBP' }
          ].map((m) => (
            <PillBtn
              key={m.id}
              active={settings.videoMode === m.id}
              label={m.label}
              accent="#FFAA00"
              onClick={() => updateSettings({ videoMode: m.id })}
            />
          ))}
        </GroupBox>
        <GroupBox>
          {['ORIGINAL', '1080P', '720P', '480P'].map((res) => (
            <PillBtn
              key={res}
              active={settings.videoRes === res}
              label={res}
              onClick={() => updateSettings({ videoRes: res })}
            />
          ))}
        </GroupBox>
        {settings.videoMode !== 'COMPRESS_MP4' && (
          <GroupBox>
            {[10, 15, 24].map((fps) => (
              <PillBtn
                key={fps}
                active={settings.videoFps === fps}
                label={`${fps}_FPS`}
                accent="#F205FF"
                onClick={() => updateSettings({ videoFps: fps })}
              />
            ))}
          </GroupBox>
        )}
      </div>
    );
  }

  if (activeModule === 'AUDIO_EXTRACTOR') {
    return (
      <div className="flex items-center gap-3">
        <GroupBox>
          {[
            { id: 'MP3_320K', label: 'MP3_320K' },
            { id: 'WAV_PCM', label: 'WAV_PCM' },
            { id: 'FLAC_LOSSLESS', label: 'FLAC' },
            { id: 'MUTE_VIDEO', label: 'MUTE_VIDEO' }
          ].map((m) => (
            <PillBtn
              key={m.id}
              active={settings.audioExtMode === m.id}
              label={m.label}
              accent="#00FF88"
              onClick={() => updateSettings({ audioExtMode: m.id })}
            />
          ))}
        </GroupBox>
      </div>
    );
  }

  if (activeModule === 'AUDIO_SEPARATOR') {
    return (
      <div className="flex items-center gap-3">
        <GroupBox>
          {[
            { id: 'VOCALS_INSTRUMENTAL', label: 'VOCAL+INST' },
            { id: 'VOCALS_ONLY', label: 'VOCALS_ONLY' },
            { id: 'INSTRUMENTAL_ONLY', label: 'KARAOKE_INST' },
            { id: '4_STEMS', label: '4_STEMS' }
          ].map((m) => (
            <PillBtn
              key={m.id}
              active={settings.stemMode === m.id}
              label={m.label}
              accent="#00FF88"
              onClick={() => updateSettings({ stemMode: m.id })}
            />
          ))}
        </GroupBox>
      </div>
    );
  }

  if (activeModule === 'AUTO_SUBTITLER') {
    return (
      <div className="flex items-center gap-3">
        <GroupBox>
          {['base', 'small', 'medium'].map((sz) => (
            <PillBtn
              key={sz}
              active={settings.whisperModel === sz}
              label={sz.toUpperCase()}
              accent="#00FF88"
              onClick={() => updateSettings({ whisperModel: sz })}
            />
          ))}
        </GroupBox>
        <GroupBox>
          {['AUTO', 'EN', 'TR'].map((lg) => (
            <PillBtn
              key={lg}
              active={settings.subLang === lg}
              label={`LANG_${lg}`}
              onClick={() => updateSettings({ subLang: lg })}
            />
          ))}
        </GroupBox>
        <GroupBox>
          {['SRT', 'TXT', 'BOTH'].map((fmt) => (
            <PillBtn
              key={fmt}
              active={settings.subFormat === fmt}
              label={fmt}
              accent="#F205FF"
              onClick={() => updateSettings({ subFormat: fmt })}
            />
          ))}
        </GroupBox>
      </div>
    );
  }

  if (activeModule === 'VOICE_CLEANER') {
    return (
      <div className="flex items-center gap-3">
        <GroupBox>
          {['LIGHT', 'STUDIO', 'AGGRESSIVE'].map((st) => (
            <PillBtn
              key={st}
              active={settings.denoiseStrength === st}
              label={st}
              accent="#00FF88"
              onClick={() => updateSettings({ denoiseStrength: st })}
            />
          ))}
        </GroupBox>
        <GroupBox>
          <PillBtn
            active={!!settings.voiceBoost}
            label={settings.voiceBoost ? 'EQ_BOOST_ON' : 'EQ_BOOST_OFF'}
            accent="#00F3FF"
            onClick={() => updateSettings({ voiceBoost: !settings.voiceBoost })}
          />
        </GroupBox>
        <GroupBox>
          {['WAV', 'MP3', 'VIDEO_REMUX'].map((fmt) => (
            <PillBtn
              key={fmt}
              active={settings.voiceOutFormat === fmt}
              label={fmt}
              accent="#F205FF"
              onClick={() => updateSettings({ voiceOutFormat: fmt })}
            />
          ))}
        </GroupBox>
      </div>
    );
  }

  return null;
};
