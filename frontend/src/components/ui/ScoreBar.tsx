interface ScoreBarProps {
  score: number; // 0 - 100
}

export function ScoreBar({ score }: ScoreBarProps) {
  const clamped = Math.max(0, Math.min(100, score));
  let colorClass = 'bg-danger';
  if (clamped >= 80) colorClass = 'bg-ok';
  else if (clamped >= 50) colorClass = 'bg-warn';

  return (
    <div className="flex items-center space-x-2 w-full max-w-[120px]">
      <div className="h-2 flex-1 bg-surface-2 rounded-full overflow-hidden">
        <div 
          className={`h-full ${colorClass} transition-all duration-300`} 
          style={{ width: `${clamped}%` }} 
        />
      </div>
      <span className="text-xs font-data text-ink w-8 text-right">{clamped}%</span>
    </div>
  );
}
