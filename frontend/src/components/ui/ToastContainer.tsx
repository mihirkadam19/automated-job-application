import { useToast } from '../../context/ToastContext'

export function ToastContainer() {
  const { toasts } = useToast()

  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-6 z-70 flex flex-col items-center gap-2 px-4">
      {toasts.map((t) => (
        <div
          key={t.id}
          role="status"
          className="pointer-events-auto animate-toast-in rounded-pill bg-ink px-4 py-2.5 text-sm font-medium text-white shadow-lg"
        >
          {t.message}
        </div>
      ))}
    </div>
  )
}
