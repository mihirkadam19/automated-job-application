export type Job = {
  id: string
  title: string
  company: string
  matchScore: number
  location: string
  workMode: string
  employmentType: string
  levelTag: string
  experienceTag: string
  seniority: string
  salaryRange: string
  salaryMin: number
  postedAt: string
  postedHoursAgo: number
  applicants: number
}

export const jobs: Job[] = [
  {
    id: 'backd-web-application-developer',
    title: 'Web Application Developer',
    company: 'Backd Business Funding',
    matchScore: 64,
    location: 'Austin, Texas Metropolitan Area',
    workMode: 'On-site',
    employmentType: 'Full time',
    levelTag: 'Internship',
    experienceTag: '0 of 3 skills match',
    seniority: 'Mid Level',
    salaryRange: '$65/yr - $70/yr',
    salaryMin: 65,
    postedAt: '1 hours ago',
    postedHoursAgo: 1,
    applicants: 25,
  },
  {
    id: 'cursor-ai-network-infrastructure',
    title: 'Software Engineer, Network Infrastructure',
    company: 'Cursor AI',
    matchScore: 93,
    location: 'Sunnyvale, CA',
    workMode: 'On-site',
    employmentType: 'Full time',
    levelTag: 'Internship',
    experienceTag: '5+ years exp',
    seniority: 'Mid Level',
    salaryRange: '$161K/yr - $239K/yr',
    salaryMin: 161000,
    postedAt: '2 hours ago',
    postedHoursAgo: 2,
    applicants: 25,
  },
  {
    id: 'simons-foundation-full-stack-engineer',
    title: 'Full-Stack Software Engineer (Web Developer)',
    company: 'Simons Foundation',
    matchScore: 82,
    location: 'New York , NY',
    workMode: 'On-site',
    employmentType: 'Full time',
    levelTag: 'Internship',
    experienceTag: '5+ years exp',
    seniority: 'Mid Level',
    salaryRange: '$125K/yr - $140K/yr',
    salaryMin: 125000,
    postedAt: '2 hours ago',
    postedHoursAgo: 2,
    applicants: 25,
  },
]

export const defaultLikedIds = ['cursor-ai-network-infrastructure']
export const defaultAppliedIds = ['simons-foundation-full-stack-engineer']
