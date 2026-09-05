import { matchRingColor } from '../../lib/matchColor'

export function MatchRing({
  score,
  size = 108,
}: {
  score: number
  size?: number
}) {
  const thickness = size * 0.15
  const radius = size / 2 - thickness / 2
  const circumference = 2 * Math.PI * radius
  const dash = (score / 100) * circumference

  return (
    <div
      className="relative flex shrink-0 items-center justify-center"
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#f3f3f4"
          strokeWidth={thickness}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={matchRingColor(score)}
          strokeWidth={thickness}
          strokeLinecap="round"
          strokeDasharray={`${dash} ${circumference - dash}`}
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center text-ink-2">
        <span
          className="font-semibold leading-none"
          style={{ fontSize: size * 0.222 }}
        >
          {score}%
        </span>
        <span
          className="mt-1 leading-none opacity-90"
          style={{ fontSize: size * 0.155 }}
        >
          Match
        </span>
      </div>
    </div>
  )
}
