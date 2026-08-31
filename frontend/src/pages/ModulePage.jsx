import { PagePlaceholder } from '../components/PagePlaceholder.jsx'

export function ModulePage({ content }) {
  return (
    <div className="page-stack">
      <header className="page-heading">
        <div>
          <p className="eyebrow">{content.eyebrow}</p>
          <h1>{content.title}</h1>
          <p className="page-description">{content.description}</p>
        </div>
        <div className="page-context">
          <span className="context-label">Reference period</span>
          <button className="context-button" type="button">31 Aug 2026 <span aria-hidden="true">⌄</span></button>
        </div>
      </header>
      <PagePlaceholder title={content.title} />
    </div>
  )
}

