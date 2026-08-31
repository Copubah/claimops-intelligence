export const navigation = [
  { label: 'Overview', path: '/', icon: 'grid' },
  { label: 'Action Center', path: '/actions', icon: 'bolt', badge: '23' },
  { label: 'Claims', path: '/claims', icon: 'file' },
  { label: 'SLA Control Tower', path: '/sla', icon: 'clock' },
  { label: 'Pipeline', path: '/pipeline', icon: 'pipeline' },
  { label: 'Agents', path: '/agents', icon: 'users' },
  { label: 'Partners', path: '/partners', icon: 'building' },
  { label: 'Risk Review', path: '/risk', icon: 'shield', badge: '4' },
  { label: 'QA', path: '/qa', icon: 'check' },
  { label: 'Analytics', path: '/analytics', icon: 'chart' },
  { label: 'Reports', path: '/reports', icon: 'report' },
  { label: 'Alerts', path: '/alerts', icon: 'bell', badge: '6' },
  { label: 'Settings', path: '/settings', icon: 'settings' },
]

export const pageContent = {
  '/': {
    eyebrow: 'Operations command center',
    title: 'Overview',
    description: 'A unified view of claim throughput, service levels, and work requiring attention.',
  },
  '/actions': {
    eyebrow: 'Prioritized work queue',
    title: 'Action Center',
    description: 'Review urgent operational issues and take authorized action on individual claims.',
  },
  '/claims': {
    eyebrow: 'Claims workspace',
    title: 'Claims',
    description: 'Search, filter, inspect, and manage fictional claim records throughout their lifecycle.',
  },
  '/sla': {
    eyebrow: 'Service-level monitoring',
    title: 'SLA Control Tower',
    description: 'Monitor healthy, watch, at-risk, and breached claims with stage-level context.',
  },
  '/pipeline': {
    eyebrow: 'Flow and bottlenecks',
    title: 'Claims Pipeline',
    description: 'Understand queue movement and identify abnormal growth across processing stages.',
  },
  '/agents': {
    eyebrow: 'Capacity and coaching',
    title: 'Agent Workload',
    description: 'Compare workload, SLA exposure, throughput, and quality without reducing performance to a leaderboard.',
  },
  '/partners': {
    eyebrow: 'Portfolio relationships',
    title: 'Partner Performance',
    description: 'Compare fictional partner volumes, service levels, documentation quality, and operating trends.',
  },
  '/risk': {
    eyebrow: 'Explainable signals',
    title: 'Risk Review',
    description: 'Review rule-based signals that indicate claims requiring additional manual attention.',
  },
  '/qa': {
    eyebrow: 'Decision quality',
    title: 'Quality Assurance',
    description: 'Track review outcomes, process issues, error categories, and coaching opportunities.',
  },
  '/analytics': {
    eyebrow: 'Historical performance',
    title: 'Analytics',
    description: 'Investigate operational trends across volume, turnaround time, backlog, aging, and outcomes.',
  },
  '/reports': {
    eyebrow: 'Scheduled intelligence',
    title: 'Reporting Center',
    description: 'Generate, schedule, archive, and distribute recurring operations reports.',
  },
  '/alerts': {
    eyebrow: 'Operational notifications',
    title: 'Alerts',
    description: 'Review state transitions, failures, and other conditions that require acknowledgement.',
  },
  '/settings': {
    eyebrow: 'Platform administration',
    title: 'Settings',
    description: 'Manage operational thresholds, report preferences, and platform configuration.',
  },
}

