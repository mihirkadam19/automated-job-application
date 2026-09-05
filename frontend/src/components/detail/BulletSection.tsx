export function BulletSection({
  title,
  items,
}: {
  title: string
  items: string[]
}) {
  return (
    <section>
      <h2 className="text-xl font-semibold text-black">{title}</h2>
      <ul className="mt-4 flex flex-col gap-2.5">
        {items.map((item) => (
          <li
            key={item}
            className="flex gap-2.5 text-sm leading-relaxed text-black/80"
          >
            <span className="mt-2 size-1.5 shrink-0 rounded-full bg-ink-2/50" />
            {item}
          </li>
        ))}
      </ul>
    </section>
  )
}
