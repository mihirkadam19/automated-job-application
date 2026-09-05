export function matchRingColor(score: number): string {
  return score >= 75 ? 'var(--color-lime)' : 'var(--color-yellow)'
}
