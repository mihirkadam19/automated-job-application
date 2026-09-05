import refreshIcon from '../../assets/icons/refresh.svg'
import searchWindow from '../../assets/icons/search-window.svg'
import { Button } from '../ui/Button'

export function SortRow() {
  return (
    <div className="flex items-center justify-between gap-4">
      <Button variant="purple" leftIcon={refreshIcon} className="px-6">
        Change Job Reference
      </Button>
      <Button
        variant="white"
        leftIcon={searchWindow}
        rightIcon={searchWindow}
        className="px-6"
      >
        Top matched
      </Button>
    </div>
  )
}
