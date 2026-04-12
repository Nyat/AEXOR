import { useState, useEffect } from 'react';
import { Download, Trash2, Search, Terminal, Activity, ShieldCheck, Cpu, MonitorSpeaker, Package, X, Check, Loader2 } from 'lucide-react';
import fallbackManifest from '../../public/modules.json';
import * as Icons from 'lucide-react';

/* ── Type Definitions ── */
export interface Dep {
  id: string;
  label: string;
  type: 'compute' | 'lib';
  packages: string[];
  size: string;
  extra_index?: string;
  force_reinstall?: boolean;
  requires_nvidia?: boolean;
}

export interface Module {
  id: string;
  name: string;
  description: string;
  icon?: string;
  size: string;
  version: string;
  url: string;
  deps: Dep[];
}

interface ModuleManagerProps {
  installedModules: string[];
  installedDeps: Record<string, string[]>;
  installQueue: string[];
  installProgress: number;
  installPhase: string;
  depInstallQueue: string[];
  hasNvidia: boolean;
  onInstall: (mod: Module) => void;
  onUninstall: (id: string) => void;
  onInstallDep: (moduleId: string, dep: Dep) => void;
  onUninstallDep: (moduleId: string, dep: Dep) => void;
}

/* ── Dep Button Component ── */
const DepButton = ({
  dep, moduleId, isInstalled, isInstalling, hasNvidia,
  onInstall, onUninstall
}: {
  dep: Dep;
  moduleId: string;
  isInstalled: boolean;
  isInstalling: boolean;
  hasNvidia: boolean;
  onInstall: (moduleId: string, dep: Dep) => void;
  onUninstall: (moduleId: string, dep: Dep) => void;
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const isGpuDisabled = dep.requires_nvidia && !hasNvidia;
  const isCompute = dep.type === 'compute';
  const IconComponent = isCompute
    ? (dep.id === 'gpu_engine' ? MonitorSpeaker : Cpu)
    : Package;

  if (isInstalling) {
    return (
      <div className="relative group/dep px-3 py-1.5 rounded-md border border-[#F205FF]/30 bg-[#F205FF]/5 flex items-center gap-2 cursor-wait">
        <Loader2 size={12} className="text-[#F205FF] animate-spin" />
        <span className="font-orbitron text-[8px] tracking-[0.15em] text-[#F205FF] uppercase">{dep.label}</span>
        <div className="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-black/90 border border-[#F205FF]/30 rounded text-[8px] text-[#F205FF] font-oxanium whitespace-nowrap opacity-0 group-hover/dep:opacity-100 transition-opacity z-50">
          ESTABLISHING...
        </div>
      </div>
    );
  }

  if (isGpuDisabled) {
    return (
      <div className="relative group/dep px-3 py-1.5 rounded-md border border-white/5 bg-white/[0.02] flex items-center gap-2 cursor-not-allowed opacity-40">
        <IconComponent size={12} className="text-gray-600" />
        <span className="font-orbitron text-[8px] tracking-[0.15em] text-gray-600 uppercase">{dep.label}</span>
        <div className="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-black/90 border border-red-500/30 rounded text-[8px] text-red-400 font-oxanium whitespace-nowrap opacity-0 group-hover/dep:opacity-100 transition-opacity z-50">
          NVIDIA GPU REQUIRED
        </div>
      </div>
    );
  }

  if (isInstalled) {
    return (
      <button
        onClick={() => onUninstall(moduleId, dep)}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        className={`relative group/dep px-3 py-1.5 rounded-md border flex items-center gap-2 transition-all duration-300 ${
          isHovered
            ? 'border-red-500/40 bg-red-500/10 text-red-400'
            : 'border-[#00FF00]/20 bg-[#00FF00]/5 text-[#00FF00]'
        }`}
      >
        {isHovered ? <X size={12} /> : <Check size={12} />}
        <span className="font-orbitron text-[8px] tracking-[0.15em] uppercase">{dep.label}</span>
        <span className="font-oxanium text-[7px] tracking-wider opacity-60">{dep.size}</span>
        <div className={`absolute -top-10 left-1/2 -translate-x-1/2 px-2 py-1 bg-black/90 border rounded text-[8px] font-oxanium whitespace-nowrap opacity-0 group-hover/dep:opacity-100 transition-opacity z-50 max-w-[200px] text-center ${
          isHovered ? 'border-red-500/30 text-red-400' : 'border-[#00FF00]/30 text-[#00FF00]'
        }`}>
          {isHovered ? 'TERMINATE: İlgili özellikler devre dışı kalır' : 'ACTIVE'}
        </div>
      </button>
    );
  }

  return (
    <button
      onClick={() => onInstall(moduleId, dep)}
      className="relative group/dep px-3 py-1.5 rounded-md border border-white/10 bg-white/[0.03] flex items-center gap-2 transition-all duration-300 hover:border-[#00F3FF]/30 hover:bg-[#00F3FF]/5 text-gray-500 hover:text-[#00F3FF]"
    >
      <Download size={12} />
      <span className="font-orbitron text-[8px] tracking-[0.15em] uppercase">{dep.label}</span>
      <span className="font-oxanium text-[7px] tracking-wider opacity-60">{dep.size}</span>
      <div className="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-black/90 border border-[#00F3FF]/30 rounded text-[8px] text-[#00F3FF] font-oxanium whitespace-nowrap opacity-0 group-hover/dep:opacity-100 transition-opacity z-50">
        UPLINK: Kurmak için tıklayın
      </div>
    </button>
  );
};


/* ── Main Component ── */
export const ModuleManager = ({
  installedModules, installedDeps, installQueue, installProgress, installPhase,
  depInstallQueue, hasNvidia, onInstall, onUninstall, onInstallDep, onUninstallDep
}: ModuleManagerProps) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [availableModules, setAvailableModules] = useState<Module[]>([]);

  useEffect(() => {
    fetch(`https://raw.githubusercontent.com/Nyat/AEXOR/main/modules/modules.json?t=${Date.now()}`)
      .then(res => res.ok ? res.json() : Promise.reject('GitHub error'))
      .then(data => setAvailableModules(data.modules))
      .catch(() => {
        console.log("GitHub unavailable, falling back to local.");
        setAvailableModules((fallbackManifest as any).modules);
      });
  }, []);

  const filteredModules = availableModules.filter(mod =>
    mod.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    mod.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="flex-1 flex flex-col p-8 bg-[radial-gradient(circle_at_top_right,rgba(0,243,255,0.03),transparent_40%)] min-h-0 overflow-hidden no-drag">

      {/* Terminal Header */}
      <div className="mb-8 border border-white/5 bg-black/40 p-6 rounded-xl relative overflow-hidden group">
         <div className="absolute top-0 left-0 w-1 h-full bg-[#00F3FF]/40"></div>
         <div className="scanline-overlay opacity-5"></div>

         <div className="flex flex-col md:flex-row justify-between gap-6 relative z-10">
            <div>
               <div className="flex items-center gap-3 mb-2">
                 <Terminal size={16} className="text-[#00F3FF]" />
                 <h1 className="text-3xl font-anta tracking-[0.2em] text-white uppercase">MODULE_MANAGER</h1>
               </div>
               <div className="flex items-center gap-6 mt-1 overflow-x-auto no-scrollbar">
                  <div className="flex items-center gap-2">
                     <span className="w-1.5 h-1.5 rounded-full bg-[#00FF00] animate-pulse"></span>
                     <span className="font-oxanium text-[9px] text-gray-500 uppercase tracking-widest whitespace-nowrap">STATUS: SECURE_LINK_ACTIVE</span>
                  </div>
                  <div className="flex items-center gap-2">
                     <Activity size={10} className="text-gray-600" />
                     <span className="font-oxanium text-[9px] text-gray-500 uppercase tracking-widest whitespace-nowrap">ID: {Math.random().toString(16).slice(2, 10).toUpperCase()}</span>
                  </div>
                  <div className="flex items-center gap-2">
                     <ShieldCheck size={10} className="text-gray-600" />
                     <span className="font-oxanium text-[9px] text-gray-500 uppercase tracking-widest whitespace-nowrap">UPLINK: ENCRYPTED_8-BIT</span>
                  </div>
               </div>
            </div>

            <div className="flex items-center gap-4">
               <div className="relative group/search">
                  <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within/search:text-[#00F3FF] transition-colors" />
                  <input
                    type="text"
                    placeholder="QUERY_NEURAL_DATABASE..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="bg-black/60 border border-white/10 rounded-lg pl-10 pr-4 py-2 text-[10px] font-oxanium tracking-widest text-[#00F3FF] outline-none focus:border-[#00F3FF]/50 focus:shadow-[0_0_15px_rgba(0,243,255,0.1)] transition-all w-64 md:w-80"
                  />
               </div>
            </div>
         </div>
      </div>

      <div className="flex-1 pb-4 custom-scrollbar overflow-y-auto w-full pr-4 grid grid-cols-1 xl:grid-cols-2 gap-4 auto-rows-max min-h-0">
        {filteredModules.map((mod) => {
          const isInstalled = installedModules.includes(mod.id);
          const isInstalling = installQueue.includes(mod.id);
          const isCurrentInstalling = installQueue[0] === mod.id;
          const Icon = (Icons as any)[mod.icon || 'HelpCircle'] || Icons.HelpCircle;
          const moduleDeps = installedDeps[mod.id] || [];
          const computeDeps = (mod.deps || []).filter(d => d.type === 'compute');
          const libDeps = (mod.deps || []).filter(d => d.type === 'lib');

          return (
            <div key={mod.id} className="bg-black/20 backdrop-blur-md border border-white/5 rounded-xl p-6 flex flex-col gap-4 relative overflow-hidden group hover:border-[#00F3FF]/20 hover:bg-black/40 transition-all duration-500 shadow-xl">

              {/* Glass background effects */}
              <div className="absolute top-0 right-0 w-32 h-32 bg-[#00F3FF]/[0.02] rounded-full blur-3xl -mr-16 -mt-16 group-hover:bg-[#00F3FF]/[0.05] transition-colors"></div>

              {isCurrentInstalling && (
                <div className="absolute bottom-0 left-0 h-[2px] bg-[#F205FF] transition-all duration-300 shadow-[0_0_15px_#F205FF] z-20" style={{ width: `${installProgress}%` }}></div>
              )}

              <div className="flex flex-col gap-5 z-10 relative">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-5 w-3/4">
                    <div className={`w-14 h-14 rounded-xl flex items-center justify-center border transition-all duration-500 ${
                      isInstalled
                        ? 'border-[#00F3FF]/30 bg-[#00F3FF]/5 text-[#00F3FF] shadow-[0_0_20px_rgba(0,243,255,0.15)]'
                        : (isInstalling ? 'border-[#F205FF]/30 bg-[#F205FF]/5 text-[#F205FF] animate-pulse' : 'border-white/5 bg-white/5 text-gray-500')
                    } group-hover:scale-105`}>
                      <Icon size={24} />
                    </div>

                    <div className="min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-anta text-base tracking-[0.1em] text-white uppercase truncate">{mod.name}</h3>
                        {isInstalled && (
                          <div className="flex items-center gap-1.5 px-2 py-0.5 bg-[#00FF00]/5 border border-[#00FF00]/20 rounded text-[#00FF00] font-orbitron text-[8px] tracking-[0.2em] shadow-[0_0_10px_rgba(0,255,0,0.1)]">
                            <span className="w-1 h-1 rounded-full bg-[#00FF00]"></span>
                            SECURED
                          </div>
                        )}
                        {isInstalling && (
                          <div className="flex items-center gap-1.5 px-2 py-0.5 bg-[#F205FF]/5 border border-[#F205FF]/20 rounded text-[#F205FF] font-orbitron text-[8px] tracking-[0.2em] animate-pulse">
                            SYNCING
                          </div>
                        )}
                      </div>

                      <div className="flex items-center gap-3">
                        <div className="flex items-center gap-1.5">
                          <span className="text-[9px] font-oxanium text-gray-600 uppercase tracking-widest">VER:</span>
                          <span className="font-orbitron text-[9px] tracking-widest text-gray-400">{mod.version}</span>
                        </div>
                        <div className="w-[1px] h-2 bg-white/10"></div>
                        <div className="flex items-center gap-1.5">
                          <span className="text-[9px] font-oxanium text-gray-600 uppercase tracking-widest">MASS:</span>
                          <span className="font-orbitron text-[9px] tracking-widest text-gray-400">{mod.size}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {isInstalled ? (
                    <button
                      onClick={() => onUninstall(mod.id)}
                      className="w-10 h-10 flex items-center justify-center text-gray-600 hover:text-white hover:bg-red-500 rounded-lg transition-all border border-transparent hover:border-red-400/50"
                      title="TERMINATE_UPLINK"
                    >
                      <Trash2 size={18} />
                    </button>
                  ) : (
                    <button
                      disabled={isInstalling}
                      onClick={() => onInstall(mod)}
                      className={`h-10 px-6 rounded-lg font-orbitron text-[10px] tracking-[0.2em] transition-all flex items-center gap-3 border shadow-lg ${
                        isInstalling
                          ? 'bg-black/60 border-[#F205FF]/40 text-[#F205FF] cursor-wait'
                          : 'bg-[#00F3FF] border-[#00F3FF] text-black hover:bg-black hover:text-[#00F3FF] hover:shadow-[0_0_20px_rgba(0,243,255,0.35)]'
                      }`}
                    >
                      {isInstalling ? (
                        <div className="flex items-center gap-3 uppercase">
                          <Download size={14} className="animate-bounce" />
                          Uplinking
                        </div>
                      ) : (
                        <> <Download size={14} /> ESTABLISH </>
                      )}
                    </button>
                  )}
                </div>

                <p className="font-oxanium text-xs text-gray-500 leading-relaxed tracking-wide group-hover:text-gray-400 transition-colors">
                   {mod.description}
                </p>

                {/* ── Dependency Buttons Panel ── */}
                {isInstalled && mod.deps && mod.deps.length > 0 && (
                  <div className="flex flex-col gap-3 p-3 bg-black/30 border border-white/5 rounded-lg">
                    <div className="flex flex-wrap gap-2">
                      {/* Compute deps first */}
                      {computeDeps.length > 0 && (
                        <>
                          <span className="font-oxanium text-[8px] text-gray-600 uppercase tracking-[0.2em] self-center mr-1">COMPUTE:</span>
                          {computeDeps.map(dep => (
                            <DepButton
                              key={dep.id}
                              dep={dep}
                              moduleId={mod.id}
                              isInstalled={moduleDeps.includes(dep.id)}
                              isInstalling={depInstallQueue.includes(`${mod.id}::${dep.id}`)}
                              hasNvidia={hasNvidia}
                              onInstall={onInstallDep}
                              onUninstall={onUninstallDep}
                            />
                          ))}
                        </>
                      )}

                      {/* Separator */}
                      {computeDeps.length > 0 && libDeps.length > 0 && (
                        <div className="w-[1px] h-6 bg-white/10 self-center mx-1"></div>
                      )}

                      {/* Library deps */}
                      {libDeps.length > 0 && (
                        <>
                          <span className="font-oxanium text-[8px] text-gray-600 uppercase tracking-[0.2em] self-center mr-1">LIBS:</span>
                          {libDeps.map(dep => (
                            <DepButton
                              key={dep.id}
                              dep={dep}
                              moduleId={mod.id}
                              isInstalled={moduleDeps.includes(dep.id)}
                              isInstalling={depInstallQueue.includes(`${mod.id}::${dep.id}`)}
                              hasNvidia={hasNvidia}
                              onInstall={onInstallDep}
                              onUninstall={onUninstallDep}
                            />
                          ))}
                        </>
                      )}
                    </div>
                  </div>
                )}

                {isCurrentInstalling && (
                  <div className="flex flex-col gap-2 p-3 bg-black/40 border border-[#F205FF]/20 rounded-lg">
                    <div className="flex items-center justify-between">
                       <span className="font-anta text-[9px] tracking-[0.2em] text-[#F205FF] animate-pulse uppercase">{installPhase}</span>
                       <span className="font-orbitron text-[9px] text-[#F205FF]">{Math.floor(installProgress)}%</span>
                    </div>
                    <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden">
                       <div className="h-full bg-[#F205FF] transition-all duration-300" style={{ width: `${installProgress}%` }}></div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
