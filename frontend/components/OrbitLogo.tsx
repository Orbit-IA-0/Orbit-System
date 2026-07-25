export function OrbitLogo({ size = 28 }: { size?: number }) {
  return (
    <div className="flex items-center gap-2">
      <svg width={size} height={size} viewBox="0 0 40 40" fill="none">
        <circle cx="20" cy="20" r="7" fill="url(#orbit-core)" />
        <ellipse cx="20" cy="20" rx="18" ry="7" stroke="url(#orbit-ring)" strokeWidth="2" fill="none" />
        <ellipse
          cx="20" cy="20" rx="18" ry="7" stroke="url(#orbit-ring)" strokeWidth="2" fill="none"
          transform="rotate(60 20 20)"
        />
        <defs>
          <linearGradient id="orbit-core" x1="0" y1="0" x2="1" y2="1">
            <stop stopColor="#3b82f6" />
            <stop offset="1" stopColor="#8b5cf6" />
          </linearGradient>
          <linearGradient id="orbit-ring" x1="0" y1="0" x2="1" y2="1">
            <stop stopColor="#8b5cf6" />
            <stop offset="1" stopColor="#3b82f6" />
          </linearGradient>
        </defs>
      </svg>
      <span className="font-display font-semibold text-lg tracking-tight">
        Orbit <span className="bg-orbit-accent bg-clip-text text-transparent">IA</span>
      </span>
    </div>
  );
}
