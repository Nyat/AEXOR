import React from 'react';
import { 
  Zap, 
  Layers, 
  RefreshCw, 
  Shrink, 
  Instagram, 
  Scaling 
} from 'lucide-react';

interface NavItemProps {
  icon: any;
  label: string;
  active?: boolean;
  onClick: () => void;
}

const NavItem = ({ icon: Icon, label, active = false, onClick }: NavItemProps) => (
  <div 
    onClick={onClick}
    className={`flex items-center gap-3 px-4 py-3 cursor-pointer transition-all duration-300 group ${
      active ? 'bg-[#00F3FF]/10 text-[#00F3FF] border-r-2 border-[#00F3FF]' : 'text-gray-300 hover:text-white hover:bg-white/5 font-medium'
    }`}
  >
    <Icon size={18} className={active ? 'drop-shadow-[0_0_8px_rgba(0,243,255,0.5)]' : ''} />
    <span className="font-anta text-[13px] tracking-widest uppercase">{label}</span>
  </div>
);

const AVAILABLE_MODULES = [
  { id: 'AI_UPSCALER', label: 'AI_UPSCALER', icon: Zap },
  { id: 'BG_REMOVER', label: 'BG_REMOVER', icon: Layers },
  { id: 'FORMAT_CONVERTER', label: 'FORMAT_CONVERTER', icon: RefreshCw },
  { id: 'IMAGE_COMPRESSOR', label: 'IMAGE_COMPRESSOR', icon: Shrink },
  { id: 'INSTA_DOWNLOADER', label: 'INSTA_DOWNLOADER', icon: Instagram },
  { id: 'PHOTO_RESIZER', label: 'PHOTO_RESIZER', icon: Scaling },
  { id: 'VIZYON_RESIZER', label: 'VIZYON_RESIZER', icon: Scaling }
];

interface SidebarProps {
  activeModule: string;
  setActiveModule: (module: string) => void;
  installedModules?: string[];
  children?: React.ReactNode; 
}

export const Sidebar = ({ activeModule, setActiveModule, installedModules = [], children }: SidebarProps) => {
  return (
    <div className="w-56 border-r border-white/5 flex flex-col no-drag bg-black/40">
      <nav className="mt-6 flex flex-col gap-1">
        {installedModules.length === 0 && (
          <div className="px-4 py-4 text-center">
             <span className="font-oxanium text-xs tracking-widest text-[#00F3FF]/50 uppercase">No active links</span>
          </div>
        )}
        
        {AVAILABLE_MODULES.filter(m => installedModules.includes(m.id)).map(mod => (
          <NavItem 
            key={mod.id}
            icon={mod.icon} 
            label={mod.label} 
            active={activeModule === mod.id} 
            onClick={() => setActiveModule(mod.id)} 
          />
        ))}
      </nav>

      <div className="flex-1" />

      <div className="border-t border-white/5 mt-4">
         <NavItem 
            icon={RefreshCw} 
            label="MODULE_MANAGER" 
            active={activeModule === 'MODULE_MANAGER'} 
            onClick={() => setActiveModule('MODULE_MANAGER')} 
         />
      </div>

      {children}
    </div>
  );
};

