/**
 * Figma only fully authored one Job Detail content example (qualifications,
 * required/preferred, responsibilities, benefits, company blurb — the "UX
 * Designer" example under Jobs 21). Header fields (title/company/match/tags)
 * come from each real job in data/jobs.ts; this body content is shared
 * across all three job detail pages since the design never varied it.
 */
export const sharedJobDetail = {
  jobDescription:
    'Job description Job description Job description Job description Job description Job description Job description Job description Job description Job description Job description Job description Job description Job description Job description Job description ',
  qualificationIntro:
    'Discover how your skills align with the requirements of this position. Below is a detailed list of the essential skills needed for the role.',
  qualificationTags: [
    'Accidental Death and Dismemberment (AD&D)',
    'Amazon Web Services (AWS)',
    'Analysis Skills',
    'DevOps',
    'Apache ActiveMQ',
    'Application Programming Interface (API)',
    'Call Center',
    'Change Control',
  ],
  required: [
    '3+ years of design experience',
    '3+ years of delivering design solutions as a UX designer or interaction designer experience',
    'Have an available online portfolio',
    'Experience prototyping (HTML, XHTML, JavaScript, CSS, Flash or Flash Catalyst, or Axure)',
  ],
  preferred: [
    '2+ years of mass-market consumer web / mobile products experience',
    'Experience working in a collaborative team and working directly with developers for implementation of designs',
  ],
  responsibilities: [
    'Collaborate and work closely with product management, engineering, sales, and research from design concept to design solution, setting UX guidelines and driving cross-team collaboration and sharing, as well as establish best practices for interaction models and user interface designs throughout the team.',
    'Work in a start-up style environment, where iteration is encouraged and design acumen is demonstrated through design end-to-end product ownership.',
    'Communicate complex, interactive design concepts clearly and persuasively across different audiences and varying levels of the organization through excellent communication, presentation, interpersonal and analytical skills.',
    'Earn trust with product managers to develop shared vision and use research and data to identify opportunities and inform decisions.',
  ],
  benefitsIntro:
    "We believe happy team members create amazing work. Here's what we offer to make that happen:",
  benefits: [
    "🏠 Remote Flexibility: Work from wherever you're most productive and happy.",
    '📈 Equity Options: Become a shareholder through our stock options plan after 6 months.',
    '💳 Meal Vouchers: Enjoy an €8/day meal voucher to make your lunch break even better.',
    '🍴 Lunch at the Office: If you’re in Bologna, we have lunch together at the office, and it is on us!',
    '⚕️ Health Coverage: Comprehensive support through the Metasalute Health Assistance Fund.',
    '🎂 Birthday Bliss: Celebrate your day with an extra day off, just for you.',
    '🧠 Mental Wellness: Free access to iFeel, our psychological support platform.',
    '🌎 International Environment: Grow your language skills while working with a diverse and global team.',
  ],
  company: {
    founded: 'Founded in 1979',
    location: 'Carlsbad, California, US',
    employees: '1001-5000 employees',
    description:
      "Kforce has a client that is seeking a UI/UX Developer in Madison, WI. Overview: In brief, we a handful of AI-powered tools for our workforce which could use a facelift to improve the overall user experience. In an ideal scenario, we would love to bring on someone that has the skills to work directly in our codebases (engineering skills) while they make improvements to the UI/UX based on their knowledge of best practices. We currently have three tools that users are interacting with; one is an Edge browser extension (JavaScript), one is using Streamlit web application (python currently but we'd be open to migrating this to some React/Angular/other framework), and the other is a basic React web application.",
  },
  fitAnalysis: {
    subScores: [
      { label: 'Education', score: 93 },
      { label: 'Skills', score: 93 },
      { label: 'Work Exp', score: 80 },
      { label: 'Exp. Level', score: 44 },
    ],
    verdicts: [
      {
        label: 'Relevant Experience',
        icon: '✅',
        body: 'You have substantial experience as a UI/UX Designer, Interaction Designer, and User Research Specialist. Your role at Sohu aligns with designing interaction elements relevant to user experience design for digital products.',
      },
      {
        label: 'Seniority',
        icon: '✅',
        body: 'You have amassed over eight years of relevant experience, meeting the mid-level seniority requirement for the role.',
      },
      {
        label: 'Education',
        icon: '⚠️',
        body: "While you hold a Master's degree from Politecnico di Milano in Digital and Interaction Design, it doesn't strictly align with the specified fields of Computer Science, Computer Engineering, or Information Science and Technology required by the job.",
      },
    ],
  },
}
