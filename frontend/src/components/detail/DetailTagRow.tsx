import tagEmployment from '../../assets/icons/tag-employment.svg'
import tagExperience from '../../assets/icons/tag-experience.svg'
import tagLevel from '../../assets/icons/tag-level.svg'
import tagLocation from '../../assets/icons/tag-location.svg'
import tagSalary from '../../assets/icons/tag-salary.svg'
import airplay from '../../assets/icons/airplay.svg'

function Tag({ icon, label }: { icon: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5 text-sm text-muted-2">
      <img src={icon} alt="" className="size-[18px] opacity-70" />
      {label}
    </span>
  )
}

export function DetailTagRow({
  levelTag,
  workMode,
  experienceTag,
  salaryRange,
  seniority,
}: {
  levelTag: string
  workMode: string
  experienceTag: string
  salaryRange: string
  seniority: string
}) {
  return (
    <div className="flex flex-wrap items-center gap-x-10 gap-y-2">
      <Tag icon={tagLocation} label="United States" />
      <Tag icon={tagEmployment} label={levelTag} />
      <Tag icon={airplay} label={workMode} />
      <Tag icon={tagExperience} label={experienceTag} />
      <Tag icon={tagSalary} label={salaryRange} />
      <Tag icon={tagLevel} label={seniority} />
    </div>
  )
}
