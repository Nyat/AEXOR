import React, { useState, useEffect } from 'react';
import { 
  Zap, 
  Layers, 
  Scaling,
  HardDrive,
  Minus,
  X
} from 'lucide-react';
import { Sidebar } from './Sidebar';
import { TelemetryView } from './TelemetryView';
import { SystemLog } from './SystemLog';
import { UpscalerSettings } from './ModulePanels/UpscalerSettings';
import { CompressorSettings } from './ModulePanels/CompressorSettings';
import { ConverterSettings } from './ModulePanels/ConverterSettings';
import { InstaSettings } from './ModulePanels/InstaSettings';
import { ResizerSettings } from './ModulePanels/ResizerSettings';
import { ModuleManager } from './ModuleManager';

export const Dashboard = () => {

  const [installedModules, setInstalledModules] = React.useState<string[]>(() => {
    try {
      const stored = localStorage.getItem('aexor-hub-modules');
      return stored ? JSON.parse(stored) : [];
    } catch { return []; }
  });
  const [installQueue, setInstallQueue] = React.useState<string[]>([]);
  const [installProgress, setInstallProgress] = React.useState<number>(0);
  const [installPhase, setInstallPhase] = React.useState<string>('');
  const [activeModule, setActiveModule] = React.useState(() => installedModules.length > 0 ? installedModules[0] : 'MODULE_MANAGER');
  const [telemetry, setTelemetry] = React.useState({ cpu: 0, ram: 0, ram_mb: 0, gpu: 0, vram_mb: 0, gpu_name: '' });

  const [selectedFiles, setSelectedFiles] = React.useState<string[]>([]);
  const [targetDir, setTargetDir] = React.useState(() => {
    return localStorage.getItem('aexor-hub-target-dir') || 'E:/AntiGravity/Aexor-Hub/output';
  });
  const [isDragging, setIsDragging] = React.useState(false);
  const [logs, setLogs] = React.useState<{ text: string, type: 'info' | 'success' | 'error' | 'progress' }[]>([]);
  const [isTaskRunning, setIsTaskRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [visibleProgress, setVisibleProgress] = useState(0);
  const [processLabel, setProcessLabel] = useState('');
  const [processIndex, setProcessIndex] = useState(0);
  const [batchProgress, setBatchProgress] = useState<Record<string, number>>({});
  const [_filePreviews, setFilePreviews] = React.useState<{[key: string]: string}>({});
  const [mousePos, setMousePos] = React.useState({ x: 0, y: 0 });
  const [isHovering, setIsHovering] = React.useState(false);
  const [device, setDevice] = React.useState<'cuda' | 'cpu'>(() => {
    return (localStorage.getItem('aexor-hub-device') as 'cuda' | 'cpu') || 'cuda';
  });
  const [settings, setSettings] = React.useState<any>({
    quality: 80,
    format: 'WEBP',
    upscale: 2,
    instaUrl: '',
    instaSessionId: localStorage.getItem('aexor-hub-insta-session') || '',
    resizerResolution: 'HD',
    resizerMode: 'FIT',
    resizerBg: 'BLACK'
  });

  const [dotCount, setDotCount] = React.useState(1);

  React.useEffect(() => {
    const interval = setInterval(() => {
      setDotCount(prev => (prev >= 3 ? 1 : prev + 1));
    }, 600);

    const handleMouseMove = (e: MouseEvent) => {
      setMousePos({ x: e.clientX, y: e.clientY });
      const target = e.target as HTMLElement;
      const isClickable = window.getComputedStyle(target).cursor === 'pointer' ||
                         target.tagName === 'BUTTON' ||
                         target.tagName === 'A' ||
                         target.closest('button') ||
                         target.closest('.cursor-pointer');
      setIsHovering(!!isClickable);
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => {
      clearInterval(interval);
      window.removeEventListener('mousemove', handleMouseMove);
    };
  }, []);

  React.useEffect(() => {
    localStorage.setItem('aexor-hub-modules', JSON.stringify(installedModules));
  }, [installedModules]);

  const handleInstallModule = (mod: any) => {
    if (!mod || !mod.id) return;
    if (installQueue.includes(mod.id) || installedModules.includes(mod.id)) return;
    
    setInstallQueue(prev => [...prev, mod.id]);
    setInstallPhase('ESTABLISHING_SECURE_CONNECTION...');
    setInstallProgress(25);
    addLog(`INITIATING_SECURE_UPLINK: ${mod.id}`, 'info');

    // @ts-ignore
    window.electronAPI?.runTask({
       action: 'INSTALL_MODULE',
       payload: {
           id: mod.id,
           url: mod.url,
           requirements: mod.requirements,
           token: ''
       }
    }).then((res: any) => {
       if (res && res.status === 'SUCCESS') {
          setInstallProgress(100);
          setInstallPhase('FINALIZING_ENVIRONMENT...');
          setTimeout(() => {
             setInstalledModules(prev => [...prev, mod.id].sort());
             setInstallQueue(prev => prev.filter(id => id !== mod.id));
             setInstallProgress(0);
             setInstallPhase('');
             addLog(`MODULE_SECURED: ${mod.id} READY FOR EXECUTION`, 'success');
          }, 800);
       } else {
          setInstallQueue(prev => prev.filter(id => id !== mod.id));
          addLog(`MODULE_INSTALL_FAILED: ${res?.message}`, 'error');
          setInstallProgress(0);
          setInstallPhase('');
       }
    }).catch((e: any) => {
        setInstallQueue(prev => prev.filter(id => id !== mod.id));
        addLog(`IPC_ERROR: ${e?.message || e}`, 'error');
        setInstallProgress(0);
        setInstallPhase('');
    });
  };

  const handleUninstallModule = async (id: string, reqs: string[] = []) => {
    addLog(`INITIATING_MODULE_PURGE: ${id}`, 'info');
    try {
        // @ts-ignore
        const checkRes = await window.electronAPI?.runTask({
            action: 'CHECK_DEPS',
            payload: { target_reqs: reqs, all_other_reqs: [] } // Basic cleanup bypass
        });
        const isolated = checkRes?.isolated || [];
        
        // @ts-ignore
        await window.electronAPI?.runTask({
            action: 'UNINSTALL_MODULE',
            payload: { id, isolated_deps: isolated }
        });
        
        setInstalledModules(prev => prev.filter(m => m !== id));
        if (activeModule === id) setActiveModule('MODULE_MANAGER');
        addLog(`MODULE_UNLINKED: ${id} REMOVED FROM WORKSPACE`, 'error');
    } catch (e: any) {
        addLog(`UNINSTALL_FAIL: ${e?.message || e}`, 'error');
    }
  };

  const addLog = (text: string, type: 'info' | 'success' | 'error' | 'progress' = 'info') => {

    const timestamp = new Date().toLocaleTimeString('en-GB', { hour12: false });
    setLogs(prev => [{ text: `[${timestamp}] ${text}`, type }, ...prev]);
  };

  React.useEffect(() => {
    // @ts-ignore
    if (window.electronAPI?.onTelemetry) {
      // @ts-ignore
      window.electronAPI.onTelemetry((data: any) => {
        if (data.type === 'log') {
          const progressMatch = data.text.match(/\[PROGRESS:\s*(\d+)\]/i);
          if (progressMatch) {
            const val = parseInt(progressMatch[1]);
            if (data.path) {
              setBatchProgress(prev => ({ ...prev, [data.path]: val }));
            } else {
              setProgress(val);
            }
          } else {
            addLog(data.text, data.level === 'error' ? 'error' : 'info');
          }
        } else if (data.type === 'telemetry') {
          setTelemetry({
            cpu: data.cpu || 0,
            ram: data.ram || 0,
            ram_mb: data.ram_mb || 0,
            gpu: data.gpu || 0,
            vram_mb: data.vram_mb || 0,
            gpu_name: data.gpu_name || ''
          });
        }
      });
    } else {
      const interval = setInterval(() => {
        setTelemetry(prev => ({
          ...prev,
          cpu: Math.floor(Math.random() * 10 + 5),
          ram: Math.floor(Math.random() * 5 + 40),
          ram_mb: 4096 + Math.floor(Math.random() * 512),
          gpu: Math.floor(Math.random() * 15)
        }));
      }, 2000);
      return () => clearInterval(interval);
    }
  }, []);

  React.useEffect(() => {
    localStorage.setItem('aexor-hub-device', device);
  }, [device]);


  const getEstimatedPeakTFLOPS = (name: string) => {
    const gpu = name.toUpperCase() || '';
    if (gpu.includes('4090')) return 330.8;
    if (gpu.includes('4080')) return 197.8;
    if (gpu.includes('4070')) return 116.6;
    if (gpu.includes('3090')) return 142.1;
    if (gpu.includes('3080')) return 119.7;
    if (gpu.includes('3070')) return 81.3;
    if (gpu.includes('A100')) return 312.0;
    if (gpu.includes('H100')) return 1513.0;
    if (gpu.includes('RTX')) return 102.4; 
    return 64.0; 
  };

  const handleSelectFile = async () => {
    // @ts-ignore
    const paths: string[] = await window.electronAPI?.selectFile();
    if (paths && paths.length > 0) {
      const newFiles = paths.filter(p => !selectedFiles.includes(p));

      if (newFiles.length > 0) {
        setSelectedFiles(prev => [...prev, ...newFiles]);
        addLog(`PAYLOAD_READY: ${newFiles.length} ASSETS_QUEUED`, 'progress');

        const thumbResults = await Promise.all(newFiles.map(async (path) => {
          // @ts-ignore
          const thumb = await window.electronAPI?.getThumbnail(path);
          return { path, thumb };
        }));

        const newPreviews: Record<string, string> = {};
        thumbResults.forEach(res => {
          if (res.thumb) newPreviews[res.path] = res.thumb;
        });

        setFilePreviews(prev => ({ ...prev, ...newPreviews }));
      }
    }
  };

  const handleSelectDir = async () => {
    // @ts-ignore
    const dir = await window.electronAPI?.selectDirectory();
    if (dir) {
      setTargetDir(dir);
      localStorage.setItem('aexor-hub-target-dir', dir);
      addLog(`TARGET_DIR_UPDATED: ${dir}`, 'info');
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const currentFile = selectedFiles[processIndex];
  const currentFileProgress = currentFile ? (batchProgress[currentFile] || 0) : progress;
  
  const totalTargetPercent = selectedFiles.length > 0 
    ? ((processIndex * 100) + currentFileProgress) / selectedFiles.length 
    : progress;

  // Predictive Timing Simulation
  useEffect(() => {
    if (isTaskRunning && currentFile) {
      const currentVal = batchProgress[currentFile] || 0;
      const gpuPower = getEstimatedPeakTFLOPS(telemetry.gpu_name);
      
      if (currentVal < 15) {
        const timer = setInterval(() => {
          setBatchProgress(prev => {
            const val = prev[currentFile] || 0;
            if (val >= 15) return prev;
            const boost = gpuPower > 100 ? 1.8 : 0.8;
            return { ...prev, [currentFile]: Math.min(15, val + boost) };
          });
        }, 150);
        return () => clearInterval(timer);
      }
      
      if (currentVal >= 15 && currentVal < 90) {
        const timer = setInterval(() => {
          setBatchProgress(prev => {
            const val = prev[currentFile] || 0;
            if (val >= 90) return prev;
            const isHeavy = activeModule === 'AI_UPSCALER';
            const baseK = isHeavy ? 0.012 : 0.04;
            const hardwareBoost = Math.sqrt(gpuPower / 64); 
            const k = baseK * hardwareBoost;
            const nextVal = val + (92 - val) * k;
            return { ...prev, [currentFile]: nextVal };
          });
        }, 250);
        return () => clearInterval(timer);
      }
    }
  }, [isTaskRunning, processIndex, !!currentFile, Math.floor(batchProgress[currentFile] || 0), activeModule, telemetry.gpu_name]);

  useEffect(() => {
    if (isTaskRunning && visibleProgress < totalTargetPercent) {
      const timer = setTimeout(() => {
        const diff = totalTargetPercent - visibleProgress;
        if (diff < 0.01) return setVisibleProgress(totalTargetPercent);
        const step = Math.max(diff * 0.25, 0.1); 
        setVisibleProgress(prev => Math.min(prev + step, totalTargetPercent));
      }, 16); 
      return () => clearTimeout(timer);
    } else if (!isTaskRunning && visibleProgress !== 0) {
      const timer = setTimeout(() => setVisibleProgress(0), 1000);
      return () => clearTimeout(timer);
    }
  }, [isTaskRunning, visibleProgress, totalTargetPercent]);

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      const paths = Array.from(files).map(f => (f as any).path).filter(p => !!p);
      const newFiles = paths.filter(p => !selectedFiles.includes(p));

      if (newFiles.length > 0) {
        setSelectedFiles(prev => [...prev, ...newFiles]);
        addLog(`PAYLOAD_READY: ${newFiles.length} ASSETS_QUEUED`, 'progress');

        const thumbResults = await Promise.all(newFiles.map(async (path) => {
          // @ts-ignore
          const thumb = await window.electronAPI?.getThumbnail(path);
          return { path, thumb };
        }));

        const newPreviews: Record<string, string> = {};
        thumbResults.forEach(res => {
          if (res.thumb) newPreviews[res.path] = res.thumb;
        });

        setFilePreviews(prev => ({ ...prev, ...newPreviews }));
      }
    }
  };

  const runActiveTask = async () => {
    const isInsta = activeModule === 'INSTA_DOWNLOADER';
    if (selectedFiles.length === 0 && !isInsta) return;
    if (isInsta && !settings.instaUrl) return;

    try {
      setIsTaskRunning(true);
      setBatchProgress({});
      setProgress(0); 
      setVisibleProgress(0); 
      addLog(`INITIATING_${activeModule}_BATCH_SEQUENCE...`, 'progress');

      const filesToProcess = isInsta ? [null] : selectedFiles;
      let completedCount = 0;

      for (let i = 0; i < filesToProcess.length; i++) {
        const file = filesToProcess[i];
        setProcessIndex(i);
        if (!file && !isInsta) continue;

        const fileName = file?.split(/[\\/]/).pop() || (isInsta ? 'media' : 'unknown');
        const nameParts = fileName.split('.');
        const ext = (nameParts.length > 1 ? nameParts.pop() : 'png') || 'png';
        const baseName = nameParts.join('.');

        let suffix = '';
        if (activeModule === 'AI_UPSCALER') suffix = `-x${settings.upscale}`;
        else if (activeModule === 'BG_REMOVER') suffix = '-nonBG';
        else if (activeModule === 'IMAGE_COMPRESSOR') suffix = '-compressed';
        else if (activeModule === 'PHOTO_RESIZER') suffix = '-resized';
        else if (activeModule === 'FORMAT_CONVERTER') suffix = '-converted';

        let finalExt = activeModule === 'FORMAT_CONVERTER' ? settings.format.toLowerCase() : ext;
        const sourceExt = ext.toLowerCase();
        if ((sourceExt === 'heic' || sourceExt === 'heif') && activeModule !== 'FORMAT_CONVERTER' && activeModule !== 'IMAGE_COMPRESSOR') {
           finalExt = 'webp';
        }
        if (activeModule === 'PHOTO_RESIZER' || activeModule === 'VIZYON_RESIZER') {
           finalExt = 'webp';
        }
        
        const outputName = `${baseName}${suffix}.${finalExt}`;

        const outputPath = `${targetDir}/${outputName}`;

        setProcessLabel(fileName);
        addLog(`PROCESSING [${completedCount + 1}/${filesToProcess.length}]: ${fileName}`, 'info');

        let rW = 1280; let rH = 720;
        if (settings.resizerResolution === 'FHD') { rW = 1920; rH = 1080; }
        if (settings.resizerResolution === 'QHD') { rW = 2560; rH = 1440; }
        if (settings.resizerResolution === '4K') { rW = 3840; rH = 2160; }

        // @ts-ignore
        const res: any = await window.electronAPI?.runTask({
          action: activeModule,
          payload: {
            input_path: file,
            output_path: outputPath,
            url: settings.instaUrl,
            quality: settings.quality,
            format: settings.format,
            upscale: settings.upscale,
            device: device,
            output_dir: targetDir,
            session_id: settings.instaSessionId,
            width: rW,
            height: rH,
            resize_mode: settings.resizerMode,
            bg_color: settings.resizerBg
          }
        });


        if (res && res.status === 'SUCCESS') {
          setBatchProgress(prev => ({ ...prev, [file as string]: 100 }));
          addLog(res.message || `COMPLETE: ${fileName}`, 'success');
          completedCount++;
        } else {
          setBatchProgress(prev => ({ ...prev, [file as string]: 0 }));
          addLog(`FAILED: ${fileName} - ${res?.message || 'UNKNOWN_ERROR'}`, 'error');
        }
      }

      addLog(`BATCH_SEQUENCE_COMPLETED: ${completedCount}/${filesToProcess.length} SUCCESSFUL`, 'success');
    } catch (e: any) {
      addLog(`IPC_CRITICAL_ERROR: ${e.message}`, 'error');
    } finally {
      setIsTaskRunning(false);
      setProgress(0);
      setSelectedFiles([]);
    }
  };

  const handleWindowAction = (type: 'minimize' | 'close') => {
    // @ts-ignore
    if (type === 'minimize') window.electronAPI?.minimize();
    // @ts-ignore
    if (type === 'close') window.electronAPI?.close();
  };

  const dots = Array.from({length: dotCount}).map(() => '.').join('');

  return (
    <div className="flex-1 flex flex-col h-screen bg-[#0A0A0B] overflow-hidden text-white font-oxanium">
      <style>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.05); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(0, 243, 255, 0.2); }
        @keyframes glow-pulse {
          0% { filter: drop-shadow(0 0 5px rgba(0, 243, 255, 0.2)); transform: scale(1); }
          50% { filter: drop-shadow(0 0 15px rgba(0, 243, 255, 0.5)); transform: scale(1.05); }
          100% { filter: drop-shadow(0 0 5px rgba(0, 243, 255, 0.2)); transform: scale(1); }
        }
        .animate-glow-pulse { animation: glow-pulse 3s infinite ease-in-out; }
        @keyframes neural-sweep {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
        .animate-neural-sweep {
          background: linear-gradient(90deg, transparent, rgba(0, 243, 255, 0.4), transparent);
          background-size: 200% 100%;
          animation: neural-sweep 10s infinite linear;
          opacity: 0.6;
        }
        @keyframes scanline-roll {
          0% { transform: translateY(-100%); }
          100% { transform: translateY(100%); }
        }
        .scanline-overlay {
          position: absolute; top: 0; left: 0; width: 100%; height: 2px;
          background: rgba(0, 243, 255, 0.05); box-shadow: 0 0 10px rgba(0, 243, 255, 0.1);
          animation: scanline-roll 8s infinite linear; pointer-events: none; z-index: 5;
        }
        .neural-grid {
          background-image: linear-gradient(rgba(255,255,255,0.01) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.01) 1px, transparent 1px);
          background-size: 20px 20px;
        }
        * { cursor: none !important; }
      `}</style>

      {/* Custom Cursor */}
      <div
        className="fixed w-3.5 h-3.5 z-[9999] pointer-events-none flex items-center justify-center mix-blend-difference transition-transform duration-100 ease-out"
        style={{ left: mousePos.x, top: mousePos.y, transform: `translate(-50%, -50%) scale(${isHovering ? 1.15 : 1})` }}
      >
        <div className="absolute w-[1.5px] h-full bg-white"></div>
        <div className="absolute h-[1.5px] w-full bg-white"></div>
      </div>

      {/* Title Bar */}
      <div
        className="h-10 w-full flex items-center justify-between pl-3.5 pr-0 border-b border-white/5 bg-black/20 title-bar no-drag"
        onMouseDown={(e) => {
          if (e.button === 0 && !(e.target as HTMLElement).closest('button')) {
            const startX = e.clientX; const startY = e.clientY;
            const onMouseMove = () => {
              // @ts-ignore
              window.electronAPI?.windowMove({ x: startX, y: startY });
            };
            const onMouseUp = () => {
              window.removeEventListener('mousemove', onMouseMove);
              window.removeEventListener('mouseup', onMouseUp);
            };
            window.addEventListener('mousemove', onMouseMove);
            window.addEventListener('mouseup', onMouseUp);
          }
        }}
      >
        <span className="text-[#00F3FF] font-orbitron text-[10px] tracking-[0.2em] pointer-events-none">
          AEXOR_HUB // <span className="text-white">V0.18.9-GUARDIAN // BETA</span>
        </span>
        <div className="flex items-center h-full">
          <button onClick={() => handleWindowAction('minimize')} className="h-full px-3.5 hover:bg-white/10 transition-colors text-gray-500 hover:text-white flex items-center justify-center"><Minus size={14} /></button>
          <button onClick={() => handleWindowAction('close')} className="h-full px-3.5 hover:bg-red-500/20 transition-colors text-gray-500 hover:text-red-500 flex items-center justify-center"><X size={14} /></button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        <Sidebar activeModule={activeModule} setActiveModule={setActiveModule} installedModules={installedModules}>
          <TelemetryView telemetry={telemetry} />
        </Sidebar>

        <div className="flex-1 flex flex-col min-h-0 overflow-hidden relative">
          <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
            {activeModule === 'MODULE_MANAGER' ? (
               <ModuleManager 
                 installedModules={installedModules}
                 installQueue={installQueue}
                 installProgress={installProgress}
                 installPhase={installPhase}
                 onInstall={handleInstallModule}
                 onUninstall={handleUninstallModule}
               />
            ) : (
               <main className="flex-1 flex flex-col bg-[radial-gradient(circle_at_top_right,rgba(0,243,255,0.03),transparent_40%)] no-drag overflow-hidden">
            <div className="p-8 pb-0 flex-1 flex flex-col min-h-0">

            <div className="flex justify-between items-end mb-6">
              <div>
                <h1 className="text-3xl font-anta tracking-[0.2em] text-white mb-2 uppercase">{activeModule}</h1>
                <p className="text-gray-500 font-oxanium text-xs tracking-wider">
                  {activeModule === 'AI_UPSCALER' && "Neural super-resolution [JPG, PNG, WEBP, HEIC]. Enhances detail using ESRGAN."}
                  {activeModule === 'BG_REMOVER' && "Alpha-mask extraction [JPG, PNG, WEBP, HEIC]. Outputs transparent PNG."}
                  {activeModule === 'FORMAT_CONVERTER' && "Lightning fast batch image format conversion [All formats supported]."}
                  {activeModule === 'IMAGE_COMPRESSOR' && "Lossless/Lossy compression for optimized storage [JPG, PNG, WEBP, HEIC]."}
                  {activeModule === 'INSTA_DOWNLOADER' && "Extract high-quality media from Instagram links."}
                  {activeModule === 'PHOTO_RESIZER' && "Dynamic professional canvas resampling (HD to 4K / FIT / FILL)."}
                  {activeModule === 'VIZYON_RESIZER' && "Personal Git-Ignored workspace for Vizyon standards (1000x1000 bounds)."}
                </p>

              </div>

              <div className="flex items-center gap-2 mb-2 p-1 bg-black/60 border border-white/10 rounded-lg group/hw transition-all shadow-xl">
                 <button onClick={() => setDevice('cpu')} className={`px-4 py-1.5 font-orbitron text-[9px] tracking-[0.2em] rounded-md transition-all ${device === 'cpu' ? 'bg-[#F205FF] text-black font-bold' : 'text-white/60 hover:text-white hover:bg-white/5 border border-white/5'}`}>CPU_SEQUENTIAL</button>
                 <button onClick={() => setDevice('cuda')} className={`px-4 py-1.5 font-orbitron text-[9px] tracking-[0.2em] rounded-md transition-all ${device === 'cuda' ? 'bg-[#00F3FF] text-black font-bold' : 'text-white/60 hover:text-white hover:bg-white/5 border border-white/5'}`}>GPU_ACCEL</button>
              </div>
            </div>

            {activeModule === 'INSTA_DOWNLOADER' ? (
                <InstaSettings instaUrl={settings.instaUrl} setInstaUrl={(val) => setSettings({...settings, instaUrl: val})} instaSessionId={settings.instaSessionId} setInstaSessionId={(val) => { setSettings({...settings, instaSessionId: val}); localStorage.setItem('aexor-hub-insta-session', val); }} />
            ) : (
              <div 
                className={`flex-1 border-2 border-dashed flex flex-col items-center justify-center transition-all duration-300 relative overflow-hidden group mb-4 ${isDragging ? 'border-[#00F3FF] bg-[#00F3FF]/5' : 'border-white/5 hover:border-white/10'} ${isTaskRunning ? 'pointer-events-none' : 'cursor-pointer'}`}
                onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop} onClick={handleSelectFile}
              >
                  <div className="absolute inset-0 neural-grid opacity-20 group-hover:opacity-30 transition-opacity"></div>
                  
                  {isTaskRunning && (
                    <div className="absolute inset-0 bg-[#0A0A0B]/80 flex flex-col items-center justify-center z-50 backdrop-blur-xl">
                        <div className="absolute top-0 left-0 h-[2px] bg-[#00F3FF] transition-all duration-300 shadow-[0_0_15px_rgba(0,243,255,1)]" style={{ width: `${visibleProgress}%` }}></div>
                        <div className="scanline-overlay opacity-20"></div>
                        
                        <div className="flex flex-col items-center gap-6 relative">
                           <div className="flex flex-col items-center">
                              <span className="font-anta text-[10px] tracking-[0.6em] text-[#00F3FF] mb-3 uppercase animate-pulse">EXECUTING_NEURAL_SEQUENCE</span>
                              <div className="relative">
                                <span className="font-orbitron text-6xl font-black text-white tracking-widest drop-shadow-[0_0_20px_rgba(255,255,255,0.4)]">{Math.floor(visibleProgress)}<span className="text-[#00F3FF] text-xl opacity-50 ml-1">%</span></span>
                              </div>
                           </div>

                           <div className="flex gap-8 mt-2 opacity-60">
                              <div className="flex flex-col items-center">
                                 <span className="font-oxanium text-[8px] text-gray-500 uppercase tracking-widest mb-1">PROCESSED_LINK</span>
                                 <span className="px-3 py-1 bg-white/5 border border-white/10 font-anta text-[9px] tracking-widest text-[#00FF00] uppercase">{activeModule}</span>
                              </div>
                              <div className="flex flex-col items-center">
                                 <span className="font-oxanium text-[8px] text-gray-500 uppercase tracking-widest mb-1">HARDWARE_UPLINK</span>
                                 <span className="px-3 py-1 bg-white/5 border border-white/10 font-anta text-[9px] tracking-widest text-[#F205FF] uppercase">{device === 'cuda' ? 'GPU_ACCEL' : 'CPU_SEQUENTIAL'}</span>
                              </div>
                           </div>

                           {selectedFiles.length > 1 && (
                             <div className="flex flex-col items-center mt-2 w-64">
                                <span className="font-oxanium text-[8px] text-gray-400 uppercase tracking-widest mb-3">BATCH_QUEUE_PROGRESS [{processIndex + 1}/{selectedFiles.length}]</span>
                                <div className="flex gap-1 w-full h-[3px]">
                                   {selectedFiles.map((_, idx) => ( 
                                      <div key={idx} className={`flex-1 rounded-full transition-all duration-500 ${idx === processIndex ? 'bg-[#00F3FF] shadow-[0_0_10px_#00F3FF] scale-y-150' : (idx < processIndex ? 'bg-[#00FF00]/40' : 'bg-white/5')}`}></div> 
                                   ))}
                                </div>
                             </div>
                           )}

                           <div className="flex items-center gap-3 mt-4 bg-black/40 px-4 py-2 border border-white/5 rounded-full">
                              <div className="w-1.5 h-1.5 rounded-full bg-[#00FF00] animate-pulse shadow-[0_0_5px_#00FF00]"></div>
                              <span className="font-mono text-[9px] text-[#00FF00] tracking-widest opacity-80 truncate max-w-[300px]">{processLabel || 'Initializing neural buffers...'}</span>
                           </div>
                        </div>
                    </div>
                  )}

                  {!isTaskRunning && selectedFiles.length === 0 && (
                    <>
                      <div className="scanline-overlay"></div>
                      <div className="flex flex-col items-center justify-center py-12">
                        <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-6 group-hover:scale-110 group-hover:bg-[#00F3FF]/10 group-hover:shadow-[0_0_30px_rgba(0,243,255,0.2)] transition-all duration-500 border border-white/5">
                          <Layers className="text-gray-600 group-hover:text-[#00F3FF] transition-colors" size={28} />
                        </div>
                        <div className="font-anta text-xl tracking-[0.3em] mb-2 uppercase text-white/50 group-hover:text-white transition-colors">DROP ASSETS OR CLICK TO UPLINK</div>
                        <div className="font-oxanium text-[10px] text-gray-600 tracking-[0.2em] uppercase">SECURE_NEURAL_UPLINK_READY</div>
                      </div>
                    </>
                  )}

                  {!isTaskRunning && selectedFiles.length > 0 && (
                    <div className="absolute inset-0 p-4 overflow-y-auto no-drag custom-scrollbar">
                       <div className="grid grid-cols-6 gap-3">
                          {selectedFiles.map((path, idx) => (
                             <div key={path} className="aspect-square relative group/item animate-fade-in" style={{ animationDelay: `${idx * 0.05}s` }}>
                                <div className="absolute inset-0 bg-black/40 rounded-lg overflow-hidden border border-white/10 group-hover/item:border-[#00F3FF]/30 transition-all flex items-center justify-center">
                                   {_filePreviews[path] ? (
                                      <img src={_filePreviews[path]} className="w-full h-full object-cover opacity-60 group-hover/item:opacity-100 transition-opacity" alt="" />
                                   ) : (
                                      <div className="text-white/10"><Scaling size={20} /></div>
                                   )}
                                   <div className="absolute bottom-1 right-1 opacity-0 group-hover/item:opacity-100 transition-opacity">
                                      <div className="bg-[#FF0055] p-1 rounded-md cursor-pointer hover:bg-red-600" onClick={(e) => {
                                         e.stopPropagation();
                                         setSelectedFiles(prev => prev.filter(p => p !== path));
                                      }}>
                                         <X size={10} className="text-white" />
                                      </div>
                                   </div>
                                </div>
                             </div>
                          ))}
                          <div className="aspect-square border border-dashed border-white/10 rounded-lg flex items-center justify-center hover:bg-white/5 transition-all text-white/20 hover:text-[#00F3FF] cursor-pointer" onClick={(e) => { e.stopPropagation(); handleSelectFile(); }}>
                             <Zap size={20} />
                          </div>
                       </div>
                    </div>
                  )}
              </div>
            )}

            <div className="flex items-center justify-between mt-2 mb-6">
              <div className="flex items-center gap-3 px-4 py-2 bg-white/5 border border-white/5 rounded cursor-pointer hover:bg-white/10 transition-colors" onClick={handleSelectDir}>
                  <HardDrive size={14} className="text-[#00F3FF]" />
                  <span className="text-[10px] font-oxanium text-gray-500 uppercase tracking-widest leading-none">TARGET_DIRECTORY: <span className="text-white lowercase">{targetDir}</span></span>
               </div>
               <div className="flex items-center gap-6">
                  <div className="flex items-center gap-4">
                      {activeModule === 'AI_UPSCALER' && <UpscalerSettings upscale={settings.upscale} setUpscale={(val) => setSettings({...settings, upscale: val})} />}
                      {activeModule === 'FORMAT_CONVERTER' && <ConverterSettings format={settings.format} setFormat={(val) => setSettings({...settings, format: val})} />}
                      {activeModule === 'IMAGE_COMPRESSOR' && <CompressorSettings quality={settings.quality} setQuality={(val) => setSettings({...settings, quality: val})} />}
                      {activeModule === 'PHOTO_RESIZER' && <ResizerSettings 
                         resolutionLabel={settings.resizerResolution} setResolutionLabel={(v) => setSettings({...settings, resizerResolution: v})}
                         resizeMode={settings.resizerMode} setResizeMode={(v) => setSettings({...settings, resizerMode: v})}
                         bgColor={settings.resizerBg} setBgColor={(v) => setSettings({...settings, resizerBg: v})}
                      />}
                  </div>

                  <button disabled={isTaskRunning} onClick={runActiveTask} className={`px-8 py-3 font-orbitron text-xs tracking-[0.3em] transition-all rounded shadow-[0_0_20px_rgba(0,243,255,0.2)] active:scale-95 border-none outline-none cursor-pointer ${isTaskRunning ? 'bg-gray-700 text-gray-400 cursor-not-allowed shadow-none' : 'bg-[#00F3FF] text-black hover:bg-[#00F3FF]/80'}`}>
                    {isTaskRunning ? 'RUNNING...' : 'INITIATE'}
                  </button>
               </div>
            </div>
            <div className="h-[200px] w-full flex-shrink-0"></div>
            </div>
            </main>
          )}
          </div>
          <SystemLog logs={logs} isTaskRunning={isTaskRunning} activeModule={activeModule} dots={dots} />
        </div>
      </div>
    </div>
  );
};

