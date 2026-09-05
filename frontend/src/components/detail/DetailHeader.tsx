import { useNavigate } from 'react-router-dom'
import arrowLeft from '../../assets/icons/arrow-left.svg'
import externalLink from '../../assets/icons/external-link.svg'
import heartIcon from '../../assets/icons/heart.svg'
import searchWindowWhite from '../../assets/icons/search-window-white.svg'
import { Button } from '../ui/Button'

export function DetailHeader({
  applicants,
  applied,
  onApply,
  liked,
  onToggleLike,
}: {
  applicants: number
  applied: boolean
  onApply: () => void
  liked: boolean
  onToggleLike: () => void
}) {
  const navigate = useNavigate()

  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={() => navigate(-1)}
          aria-label="Back to job list"
          className="flex size-[35px] items-center justify-center rounded-pill bg-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
        >
          <img src={arrowLeft} alt="" className="size-5" />
        </button>
        <span className="rounded-pill bg-primary px-4 py-2 text-sm font-medium text-white">
          {applicants} applicants
        </span>
      </div>

      <div className="flex items-center gap-4">
        <img src={externalLink} alt="" aria-hidden="true" className="size-[19px] opacity-70" />
        <button
          type="button"
          onClick={onToggleLike}
          aria-label={liked ? 'Remove from liked jobs' : 'Save to liked jobs'}
          aria-pressed={liked}
          className={`rounded-full p-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 ${liked ? 'bg-primary/10' : ''}`}
        >
          <img src={heartIcon} alt="" className="size-[19px]" />
        </button>
        <Button
          variant="dark"
          leftIcon={searchWindowWhite}
          rightIcon={searchWindowWhite}
          disabled={applied}
          onClick={onApply}
        >
          {applied ? 'Applied' : 'Apply Now'}
        </Button>
      </div>
    </div>
  )
}
