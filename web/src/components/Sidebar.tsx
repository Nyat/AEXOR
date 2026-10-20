import React from 'react';
import { 
  Zap, 
  Layers, 
  RefreshCw, 
  Shrink, 
  Instagram, 
  Scaling,
  ScanText,
  Palette,
  FileSpreadsheet,
  Spline,
  Eraser,
  Globe,
  Film,
  Music,
  Sliders,
  Subtitles,
  Mic
} from 'lucide-react';

interface NavItemProps {
  icon: any;
  label: string;
  active?: boolean;
  accentColor?: string;
  onClick: () => void;
}

const NavItem = ({ icon: Icon, label, active = false, accentColor = '#00F3FF', onClick }: NavItemProps) => (
  <div 
    onClick={onClick}
    style={active ? {
      backgroundColor: `${accentColor}15`,
      color: accentColor,
      borderRightColor: accentColor
    } : undefined}
    className={`flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-all duration-300 group ${
      active ? 'border-r-2' : 'text-gray-400 hover:text-white hover:bg-white/5 font-medium'
    }`}
  >
    <Icon
      size={16}
      style={active ? { filter: `drop-shadow(0 0 8px ${accentColor}80)`, color: accentColor } : { color: `${accentColor}B0` }}
      className="transition-all duration-300 group-hover:scale-105 shrink-0"
    />
    <span className="font-anta text-[11px] tracking-widest uppercase truncate">{label}</span>
  </div>
);

interface CategoryGroup {
  id: string;
  title: string;
  color: string;
  modules: { id: string; label: string; icon: any }[];
}

export const MODULE_CATEGORIES: CategoryGroup[] = [
  {
    id: 'VISUAL_STUDIO',
    title: 'VISUAL_STUDIO',
    color: '#00F3FF',
    modules: [
      { id: 'AI_UPSCALER', label: 'AI_UPSCALER', icon: Zap },
      { id: 'BG_REMOVER', label: 'BG_REMOVER', icon: Layers },
      { id: 'FORMAT_CONVERTER', label: 'FORMAT_CONVERTER', icon: RefreshCw },
      { id: 'IMAGE_COMPRESSOR', label: 'IMAGE_COMPRESSOR', icon: Shrink },
      { id: 'NEURAL_OCR', label: 'NEURAL_OCR', icon: ScanText },
      { id: 'PALETTE_GENERATOR', label: 'PALETTE_GENERATOR', icon: Palette },
      { id: 'PDF_FORGE', label: 'PDF_FORGE', icon: FileSpreadsheet },
      { id: 'PHOTO_RESIZER', label: 'PHOTO_RESIZER', icon: Scaling },
      { id: 'VECTOR_TRACER', label: 'VECTOR_TRACER', icon: Spline },
      { id: 'WATERMARK_REMOVER', label: 'WATERMARK_REMOVER', icon: Eraser },
    ]
  },
  {
    id: 'NETWORK_UPLINK',
    title: 'NETWORK_UPLINK',
    color: '#F205FF',
    modules: [
      { id: 'INSTA_DOWNLOADER', label: 'INSTA_DOWNLOADER', icon: Instagram },
      { id: 'MEDIA_DOWNLOADER', label: 'MEDIA_DOWNLOADER', icon: Globe },
    ]
  },
  {
    id: 'VIDEO_ENGINE',
    title: 'VIDEO_ENGINE',
    color: '#FFAA00',
    modules: [
      { id: 'VIDEO_OPTIMIZER', label: 'VIDEO_OPTIMIZER', icon: Film },
    ]
  },
  {
    id: 'AUDIO_LAB',
    title: 'AUDIO_LAB',
    color: '#00FF88',
    modules: [
      { id: 'AUDIO_EXTRACTOR', label: 'AUDIO_EXTRACTOR', icon: Music },
      { id: 'AUDIO_SEPARATOR', label: 'AUDIO_SEPARATOR', icon: Sliders },
      { id: 'AUTO_SUBTITLER', label: 'AUTO_SUBTITLER', icon: Subtitles },
      { id: 'VOICE_CLEANER', label: 'VOICE_CLEANER', icon: Mic },
    ]
  }
];

interface SidebarProps {
  activeModule: string;
  setActiveModule: (module: string) => void;
  installedModules?: string[];
  children?: React.ReactNode; 
}

export const Sidebar = ({ activeModule, setActiveModule, installedModules = [], children }: SidebarProps) => {
  return (
    <div className="w-56 border-r border-white/5 flex flex-col h-full min-h-0 no-drag bg-black/40">
      <nav className="mt-3 flex-1 min-h-0 overflow-y-auto custom-scrollbar flex flex-col gap-0.5 pb-2">
        {installedModules.length === 0 && (
          <div className="px-4 py-4 text-center">
             <span className="font-oxanium text-xs tracking-widest text-[#00F3FF]/50 uppercase">No active links</span>
          </div>
        )}
        
        {MODULE_CATEGORIES.map((cat) => {
          const activeCatModules = cat.modules
            .filter(m => installedModules.includes(m.id))
            .sort((a, b) => a.label.localeCompare(b.label));

          if (activeCatModules.length === 0) return null;

          return (
            <div key={cat.id} className="flex flex-col mb-1.5">
              <div className="px-4 pt-2 pb-1 flex items-center gap-2">
                <span
                  className="w-1 h-1 rounded-full shrink-0"
                  style={{ backgroundColor: cat.color, boxShadow: `0 0 6px ${cat.color}` }}
                />
                <span
                  className="font-orbitron text-[8px] tracking-[0.22em] uppercase opacity-80 truncate"
                  style={{ color: cat.color }}
                >
                  {cat.title}
                </span>
                <div
                  className="flex-1 h-[1px] opacity-20"
                  style={{ backgroundColor: cat.color }}
                />
              </div>

              {activeCatModules.map(mod => (
                <NavItem 
                  key={mod.id}
                  icon={mod.icon} 
                  label={mod.label} 
                  accentColor={cat.color}
                  active={activeModule === mod.id} 
                  onClick={() => setActiveModule(mod.id)} 
                />
              ))}
            </div>
          );
        })}
      </nav>

      <div className="shrink-0">
        {children}
      </div>

      <div className="border-t border-white/5 shrink-0">
         <NavItem 
            icon={RefreshCw} 
            label="MODULE_MANAGER" 
            accentColor="#00F3FF"
            active={activeModule === 'MODULE_MANAGER'} 
            onClick={() => setActiveModule('MODULE_MANAGER')} 
         />
      </div>
    </div>
  );
};
