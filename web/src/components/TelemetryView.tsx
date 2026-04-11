

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
}

export const TelemetryView = ({ telemetry }: TelemetryViewProps) => {
  return (
    <div className="p-8 border-t border-white/5 bg-black/20">
      <div className="space-y-4">
        <TelemetryItem label="CPU_LOAD" value={telemetry.cpu} />
        <TelemetryItem label="GPU_VRAM_UTIL" value={`${telemetry.gpu}% / ${telemetry.vram_mb} MB`} unit="" />
        <TelemetryItem label="RAM_ALLOC" value={telemetry.ram} />
      </div>
    </div>
  );
};
