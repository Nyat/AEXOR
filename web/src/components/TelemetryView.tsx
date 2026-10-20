import { RotateCcw } from 'lucide-react';

interface TelemetryItemProps {
  label: string;
  value: string | number;
  unit?: string;
}

const TelemetryItem = ({ label, value, unit = "%" }: TelemetryItemProps) => (
  <div className="flex flex-col gap-1">
    <div className="text-[10px] font-orbitron text-gray-400 tracking-[0.2em] uppercase font-bold">{label}</div>
    <div className="text-sm font-orbitron text-white tracking-widest drop-shadow-sm">{value}{unit}</div>
  </div>
);

interface TelemetryData {
  cpu: number;
  gpu: number;
  ram: number;
  vram_mb: number;
}

interface TelemetryViewProps {
  telemetry: TelemetryData;
  onPurgeMemory?: () => void;
  isPurging?: boolean;
  disabled?: boolean;
}

export const TelemetryView = ({ telemetry, onPurgeMemory, isPurging = false, disabled = false }: TelemetryViewProps) => {
  return (
    <div className="p-6 px-8 border-t border-white/5 bg-black/20">
      <div className="space-y-4">
        <TelemetryItem label="CPU_LOAD" value={telemetry.cpu} />
        <TelemetryItem label="GPU_VRAM_UTIL" value={`${telemetry.gpu}% / ${telemetry.vram_mb} MB`} unit="" />
        <TelemetryItem label="RAM_ALLOC" value={telemetry.ram} />
      </div>
      {onPurgeMemory && (
        <button
          type="button"
          disabled={disabled || isPurging}
          onClick={onPurgeMemory}
          title="Release VRAM & RAM held exclusively by Aexor neural engines"
          className={`mt-4 w-full py-1.5 px-3 rounded border font-orbitron text-[9px] tracking-[0.2em] uppercase flex items-center justify-center gap-2 transition-all cursor-pointer ${
            disabled || isPurging
              ? 'border-white/5 bg-white/5 text-gray-600 cursor-not-allowed opacity-50'
              : 'border-[#00F3FF]/30 bg-[#00F3FF]/5 text-[#00F3FF] hover:bg-[#00F3FF]/15 hover:border-[#00F3FF] hover:shadow-[0_0_12px_rgba(0,243,255,0.25)] active:scale-95'
          }`}
        >
          <RotateCcw size={11} className={isPurging ? 'animate-spin' : ''} />
          <span>{isPurging ? 'PURGING...' : 'PURGE_MEMORY'}</span>
        </button>
      )}
    </div>
  );
};

