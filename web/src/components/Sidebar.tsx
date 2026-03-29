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

interface SidebarProps {
  activeModule: string;
  setActiveModule: (module: string) => void;
  children?: React.ReactNode; // For Telemetry or other bottom content
}

export const Sidebar = ({ activeModule, setActiveModule, children }: SidebarProps) => {
  return (
    <div className="w-56 border-r border-white/5 flex flex-col no-drag bg-black/40">
      <nav className="mt-6">
        <NavItem 
          icon={Zap} 
          label="AI_UPSCALER" 
          active={activeModule === 'AI_UPSCALER'} 
          onClick={() => setActiveModule('AI_UPSCALER')} 
        />
        <NavItem 
          icon={Layers} 
          label="BG_REMOVER" 
          active={activeModule === 'BG_REMOVER'} 
          onClick={() => setActiveModule('BG_REMOVER')} 
        />
        <NavItem 
          icon={RefreshCw} 
          label="FORMAT_CONVERTER" 
          active={activeModule === 'FORMAT_CONVERTER'} 
          onClick={() => setActiveModule('FORMAT_CONVERTER')} 
        />
        <NavItem 
          icon={Shrink} 
          label="IMAGE_COMPRESSOR" 
          active={activeModule === 'IMAGE_COMPRESSOR'} 
          onClick={() => setActiveModule('IMAGE_COMPRESSOR')} 
        />
        <NavItem 
          icon={Instagram} 
          label="INSTA_DOWNLOADER" 
          active={activeModule === 'INSTA_DOWNLOADER'} 
          onClick={() => setActiveModule('INSTA_DOWNLOADER')} 
        />
        <NavItem 
          icon={Scaling} 
          label="PHOTO_RESIZER" 
          active={activeModule === 'PHOTO_RESIZER'} 
          onClick={() => setActiveModule('PHOTO_RESIZER')} 
        />
      </nav>

      {/* Spacer to push children to bottom */}
      <div className="flex-1" />

      {children}
    </div>
  );
};
