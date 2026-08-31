const paths = {
  grid: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>,
  bolt: <path d="m13 2-9 12h7l-1 8 9-12h-7l1-8Z" />,
  file: <><path d="M6 2h9l4 4v16H6z" /><path d="M14 2v5h5M9 12h6M9 16h6" /></>,
  clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
  pipeline: <><circle cx="5" cy="5" r="2" /><circle cx="19" cy="12" r="2" /><circle cx="5" cy="19" r="2" /><path d="M7 5h3a3 3 0 0 1 3 3v1a3 3 0 0 0 3 3h1M7 19h3a3 3 0 0 0 3-3v-1" /></>,
  users: <><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M17 11a4 4 0 0 0 0-8M22 21v-2a4 4 0 0 0-3-3.87" /></>,
  building: <><path d="M4 22V5l8-3 8 3v17M2 22h20" /><path d="M8 8h1M15 8h1M8 12h1M15 12h1M8 16h1M15 16h1" /></>,
  shield: <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Zm0-13v4m0 4h.01" />,
  check: <><path d="m9 11 2 2 4-5" /><path d="M21 12a9 9 0 1 1-5.3-8.2" /></>,
  chart: <><path d="M3 3v18h18" /><path d="m7 16 4-5 3 2 5-7" /></>,
  report: <><path d="M5 3h14v18H5z" /><path d="M9 8h6M9 12h6M9 16h4" /></>,
  bell: <><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" /></>,
  settings: <><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06-2.83 2.83-.06-.06A1.7 1.7 0 0 0 15 19.4a1.7 1.7 0 0 0-1 .6 1.7 1.7 0 0 0-.4 1.1V21h-4v-.09A1.7 1.7 0 0 0 8.55 19.4a1.7 1.7 0 0 0-1.88.34l-.06.06-2.83-2.83.06-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-.6-1 1.7 1.7 0 0 0-1.1-.4H3v-4h.09A1.7 1.7 0 0 0 4.6 8.55a1.7 1.7 0 0 0-.34-1.88l-.06-.06 2.83-2.83.06.06A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-.6 1.7 1.7 0 0 0 .4-1.1V3h4v.09A1.7 1.7 0 0 0 15.45 4.6a1.7 1.7 0 0 0 1.88-.34l.06-.06 2.83 2.83-.06.06A1.7 1.7 0 0 0 19.4 9c.15.38.37.73.66 1 .3.28.68.42 1.1.4H21v4h-.09A1.7 1.7 0 0 0 19.4 15Z" /></>,
  menu: <path d="M4 7h16M4 12h16M4 17h16" />,
  search: <><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></>,
  close: <path d="m6 6 12 12M18 6 6 18" />,
  chevron: <path d="m9 18 6-6-6-6" />,
}

export function Icon({ name, size = 20 }) {
  return (
    <svg className="icon" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {paths[name]}
    </svg>
  )
}

