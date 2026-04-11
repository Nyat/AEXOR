import React, { useState, useEffect } from 'react';
import { 
  Zap, 
  Layers, 
  RefreshCw, 
  Shrink, 
  Instagram, 
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

export const Dashboard = () => {
  const [activeModule, setActiveModule] = React.useState('AI_UPSCALER');
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
  const [processType, setProcessType] = useState('');
  const [processLabel, setProcessLabel] = useState('');
  const [processIndex, setProcessIndex] = useState(0);
  const [batchProgress, setBatchProgress] = useState<Record<string, number>>({});
  const [filePreviews, setFilePreviews] = React.useState<{[key: string]: string}>({});
  const logContainerRef = React.useRef<HTMLDivElement>(null);
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

  const getProcessDisplayLabel = (type: string, upscale: number) => {
    switch (type) {
      case 'AI_UPSCALER': return `UPSCALING_X${upscale}_NEURAL`;
      case 'BG_REMOVER': return 'NEURAL_ALPHA_EXTRACTION';
      case 'FORMAT_CONVERTER': return 'BATCH_FORMAT_TRANSCODE';
      case 'IMAGE_COMPRESSOR': return 'LOSSLESS_NEURAL_COMPRESS';
      case 'INSTA_DOWNLOADER': return 'INSTA_MEDIA_UPLINK';
      case 'PHOTO_RESIZER': return 'DYNAMIC_RESAMPLING_PASS';
      default: return 'NEURAL_EXECUTION_ACTIVE';
    }
  };

  const getEstimatedPeakTFLOPS = (name: string) => {
    const gpu = name.toUpperCase();
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
      setProcessType(activeModule);
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
        
        const outputName = `${baseName}${suffix}.${finalExt}`;
        const outputPath = `${targetDir}/${outputName}`;

        setProcessLabel(fileName);
        addLog(`PROCESSING [${completedCount + 1}/${filesToProcess.length}]: ${fileName}`, 'info');

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
            session_id: settings.instaSessionId
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
        <Sidebar activeModule={activeModule} setActiveModule={setActiveModule}>
          <TelemetryView telemetry={telemetry} />
        </Sidebar>

        <main className="flex-1 flex flex-col bg-[radial-gradient(circle_at_top_right,rgba(0,243,255,0.03),transparent_40%)] no-drag">
          <div className="p-8 pb-0">
            <div className="flex justify-between items-end mb-6">
              <div>
                <h1 className="text-3xl font-anta tracking-[0.2em] text-white mb-2 uppercase">{activeModule}</h1>
                <p className="text-gray-500 font-oxanium text-xs tracking-wider">
                  {activeModule === 'AI_UPSCALER' && "Neural super-resolution [JPG, PNG, WEBP, HEIC]. Enhances detail using ESRGAN."}
                  {activeModule === 'BG_REMOVER' && "Alpha-mask extraction [JPG, PNG, WEBP, HEIC]. Outputs transparent PNG."}
                  {activeModule === 'FORMAT_CONVERTER' && "Lightning fast batch image format conversion [All formats supported]."}
                  {activeModule === 'IMAGE_COMPRESSOR' && "Lossless/Lossy compression for optimized storage [JPG, PNG, WEBP, HEIC]."}
                  {activeModule === 'INSTA_DOWNLOADER' && "Extract high-quality media from Instagram links."}
                  {activeModule === 'PHOTO_RESIZER' && "Standardized 1000x1000 white-canvas centering (800px bounds) [.webp output]."}
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
                className={`flex-1 border-2 border-dashed h-44 flex flex-col items-center justify-center transition-all duration-300 relative overflow-hidden group mb-4 ${isDragging ? 'border-[#00F3FF] bg-[#00F3FF]/5' : 'border-white/5 hover:border-white/10'} ${isTaskRunning ? 'pointer-events-none' : 'cursor-pointer'}`}
                onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop} onClick={handleSelectFile}
              >
                  <div className="absolute inset-0 neural-grid opacity-20 group-hover:opacity-30 transition-opacity"></div>
                  {isTaskRunning && (
                    <div className="absolute inset-0 bg-black/80 flex flex-col items-center justify-center z-20 backdrop-blur-md">
                        <div className="absolute top-0 left-0 h-[2px] bg-[#00F3FF] transition-all duration-300 shadow-[0_0_15px_rgba(0,243,255,0.8)]" style={{ width: `${visibleProgress}%` }}></div>
                        <div className="flex flex-col items-center gap-6">
                           <div className="flex flex-col items-center">
                              <span className="font-anta text-[10px] tracking-[0.4em] text-[#00F3FF] mb-2 uppercase animate-pulse">PROCESSING_UPLINK</span>
                              <span className="font-orbitron text-4xl font-black text-white tracking-widest drop-shadow-[0_0_15px_rgba(255,255,255,0.3)]">{Math.floor(visibleProgress)}<span className="text-[#00F3FF] text-xl opacity-50 ml-1">%</span></span>
                           </div>
                           <div className="flex flex-col items-center">
                              <span className="font-oxanium text-[9px] text-gray-500 uppercase tracking-[0.2em] mb-1">active_module</span>
                              <span className="px-3 py-1 bg-white/5 border border-white/10 font-anta text-[10px] tracking-[0.2em] text-[#00FF00]">{getProcessDisplayLabel(processType, settings.upscale)}</span>
                           </div>
                           {selectedFiles.length > 1 && (
                             <div className="flex flex-col items-center mt-2">
                                <span className="font-oxanium text-[9px] text-gray-400 uppercase tracking-widest mb-2">batch_status [{processIndex + 1}/{selectedFiles.length}]</span>
                                <div className="flex gap-1.5 h-1">
                                   {selectedFiles.map((_, idx) => ( <div key={idx} className={`w-6 rounded-full transition-all duration-500 ${idx === processIndex ? 'bg-[#00F3FF] w-12 shadow-[0_0_8px_#00F3FF]' : (idx < processIndex ? 'bg-[#00FF00]' : 'bg-white/10')}`}></div> ))}
                                </div>
                             </div>
                           )}
                           <div className="flex items-center gap-2 mt-4">
                              <div className="w-1.5 h-1.5 rounded-full bg-[#00FF00] animate-pulse"></div>
                              <span className="font-mono text-[9px] text-[#00FF00] tracking-widest opacity-80 truncate max-w-[200px]">{processLabel}</span>
                           </div>
                        </div>
                    </div>
                  )}
                  {isTaskRunning && <div className="absolute inset-0 animate-neural-sweep z-10"></div>}
                  {!isTaskRunning && (
                    <>
                      <div className="scanline-overlay"></div>
                      <div className={`w-12 h-12 rounded-full bg-white/5 flex items-center justify-center mb-6 group-hover:scale-110 group-hover:bg-[#00F3FF]/10 group-hover:shadow-[0_0_20px_rgba(0,243,255,0.3)] transition-all duration-500 mt-12 ${selectedFiles.length > 0 ? 'text-[#00F3FF]' : 'text-gray-600'}`}>
                        <div className={selectedFiles.length > 0 ? 'animate-glow-pulse' : ''}>
                          {activeModule === 'AI_UPSCALER' && <Zap size={24} />}
                          {activeModule === 'BG_REMOVER' && <Layers size={24} />}
                          {activeModule === 'FORMAT_CONVERTER' && <RefreshCw size={24} />}
                          {activeModule === 'IMAGE_COMPRESSOR' && <Shrink size={24} />}
                          {activeModule === 'INSTA_DOWNLOADER' && <Instagram size={24} />}
                          {activeModule === 'PHOTO_RESIZER' && <Scaling size={24} />}
                        </div>
                      </div>
                      <div className={`font-anta text-xl tracking-[0.2em] mb-2 uppercase text-center text-white/40 mb-6`}><span>{selectedFiles.length > 0 ? "ASSETS_LINK_ESTABLISHED" : "DROP ASSETS OR CLICK TO UPLINK"}</span></div>
                      <div className="font-oxanium text-xs text-gray-500 max-w-md text-center truncate px-10">{selectedFiles.length > 0 ? `${selectedFiles.length} files selected` : "Waiting for secure uplink..."}</div>
                    </>
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
                  </div>
                  <button disabled={isTaskRunning} onClick={runActiveTask} className={`px-8 py-3 font-orbitron text-xs tracking-[0.3em] transition-all rounded shadow-[0_0_20px_rgba(0,243,255,0.2)] active:scale-95 border-none outline-none cursor-pointer ${isTaskRunning ? 'bg-gray-700 text-gray-400 cursor-not-allowed shadow-none' : 'bg-[#00F3FF] text-black hover:bg-[#00F3FF]/80'}`}>
                    {isTaskRunning ? 'RUNNING...' : 'INITIATE'}
                  </button>
               </div>
            </div>
          </div>
          <SystemLog logs={logs} isTaskRunning={isTaskRunning} activeModule={activeModule} dots={dots} />
        </main>
      </div>
    </div>
  );
};
