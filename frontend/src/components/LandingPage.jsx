const TEAM = [
  {
    name: 'Kunal Keshav Singh Sahni',
    initials: 'KS',
  },
  {
    name: 'Dan Lam',
    initials: 'DL',
  },
  {
    name: 'Dhruv Verma',
    initials: 'DV',
  },
];

const PILLARS = [
  {
    icon: '⚡',
    title: 'Intake & Enrichment',
    body: 'Every order is enriched in real-time with warehouse stock, driver availability, and zone performance data — all fetched concurrently from the ERP in a single pass.',
  },
  {
    icon: '📐',
    title: 'Optimizer Agent',
    body: 'A deterministic reward function scores every viable warehouse-driver pair on timeliness, cost efficiency, proximity, and zone risk — returning a ranked shortlist in milliseconds.',
  },
  {
    icon: '🧠',
    title: 'Reasoner Agent',
    body: 'A streaming LLM audits the optimizer\'s top choice across five deliberation areas: signal dominance, borderline ranking, geographic fairness, structural blind spots, and a final verdict.',
  },
  {
    icon: '⚖️',
    title: 'Resolution Layer',
    body: 'The two agents are compared. If they agree, the decision is confirmed. If the LLM flags a risk, it qualifies. If it disagrees, it overrides — with a full audit trail either way.',
  },
];

export default function LandingPage({ onLaunch }) {
  return (
    <div className="lp-root">
      {/* ── Navbar ─────────────────────────────────────────────────── */}
      <nav className="lp-nav">
        <div className="lp-nav-inner">
          <div className="lp-nav-brand">
            <span className="lp-nav-dot" />
            <span className="lp-nav-wordmark">ALRO</span>
          </div>
          <div className="lp-nav-links">
            <a className="lp-nav-link" href="#what">What it is</a>
            <a className="lp-nav-link" href="#architecture">Architecture</a>
            <a className="lp-nav-link" href="#novelty">Why it's novel</a>
            <a className="lp-nav-link" href="#team">Team</a>
          </div>
          <button className="lp-launch-sm" onClick={onLaunch} type="button">
            Launch App →
          </button>
        </div>
      </nav>

      {/* ── Hero ───────────────────────────────────────────────────── */}
      <section className="lp-hero" id="hero">
        <div className="lp-hero-grid" aria-hidden="true" />
        <div className="lp-hero-glow" aria-hidden="true" />

        <div className="lp-hero-inner">
          <div className="lp-hero-badge">
            <span className="lp-hero-badge-dot" />
            Dual-Agent AI · Last-Mile Logistics
          </div>

          <h1 className="lp-hero-title">
            <span className="lp-hero-acronym">ALRO</span>
            <br />
            <span className="lp-hero-subtitle-line">
              Autonomous Logistics<br className="lp-hero-br" /> and Routing Optimizer
            </span>
          </h1>

          <p className="lp-hero-desc">
            A two-agent system where a fast deterministic optimizer proposes a route
            and a streaming LLM reasoner audits it live — producing transparent,
            accountable last-mile delivery decisions.
          </p>

          <button className="lp-launch-btn" onClick={onLaunch} type="button">
            <span>Launch</span>
            <svg className="lp-launch-arrow" width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M3 9h12M10 4l5 5-5 5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>

          <div className="lp-hero-tags">
            <span className="lp-tag">Optimizer</span>
            <span className="lp-tag-sep">·</span>
            <span className="lp-tag">LLM Reasoner</span>
            <span className="lp-tag-sep">·</span>
            <span className="lp-tag">Resolution Layer</span>
            <span className="lp-tag-sep">·</span>
            <span className="lp-tag">SSE Streaming</span>
          </div>
        </div>
      </section>

      {/* ── What it is ─────────────────────────────────────────────── */}
      <section className="lp-section" id="what">
        <div className="lp-section-inner">
          <p className="lp-section-overline">What it is</p>
          <h2 className="lp-section-heading">
            Two agents. One decision.<br />Full accountability.
          </h2>
          <p className="lp-section-body">
            ALRO connects a logistics ERP to a pipeline of three autonomous
            agents. The <strong>Intake Agent</strong> pulls live warehouse stock,
            driver locations, and zone analytics. The <strong>Optimizer
            Agent</strong> scores every viable route in milliseconds using a
            reward function weighted by priority tier. The <strong>Reasoner
            Agent</strong> — powered by a large language model — then streams
            a chain-of-thought deliberation that checks the optimizer's
            recommendation for risks it cannot encode in numbers.
          </p>
          <p className="lp-section-body">
            The result is surfaced as one of three resolution states:{' '}
            <span className="lp-inline-green">Convergence</span> when both
            agents agree,{' '}
            <span className="lp-inline-amber">Qualification</span> when the
            LLM flags a condition, or{' '}
            <span className="lp-inline-red">Override</span> when it recommends
            a different route entirely — all with a complete audit trail.
          </p>
        </div>
      </section>

      {/* ── Pillars ─────────────────────────────────────────────────── */}
      <section className="lp-pillars-section" id="architecture">
        <div className="lp-section-inner">
          <p className="lp-section-overline">Architecture</p>
          <h2 className="lp-section-heading">Four layers, one pipeline</h2>
          <div className="lp-pillars-grid">
            {PILLARS.map((p) => (
              <div className="lp-pillar-card" key={p.title}>
                <div className="lp-pillar-icon">{p.icon}</div>
                <h3 className="lp-pillar-title">{p.title}</h3>
                <p className="lp-pillar-body">{p.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Novelty ─────────────────────────────────────────────────── */}
      <section className="lp-novelty-section" id="novelty">
        <div className="lp-section-inner lp-novelty-inner">
          <div className="lp-novelty-text">
            <p className="lp-section-overline">Why it's novel</p>
            <h2 className="lp-section-heading lp-novelty-heading">
              Reward functions are blind.<br />ALRO gives logistics a conscience.
            </h2>
            <p className="lp-section-body">
              Every routing engine in production today optimises a single
              objective — cost, speed, or utilisation. They cannot reason about
              what they cannot measure.
            </p>
            <p className="lp-section-body">
              ALRO introduces a <strong>deliberation layer</strong> that runs
              in parallel with the optimizer and audits five structural blind
              spots: signal dominance, ranking confidence, geographic fairness,
              driver zone familiarity, and cargo-specific risk. When a zone has
              an 83% delivery success rate and the optimizer sends its cheapest
              driver who has never operated there, ALRO flags it — or overrides
              it outright.
            </p>
            <p className="lp-section-body lp-novelty-callout">
              This is the first system to treat route selection as a
              dual-agent deliberation problem where the LLM is not a
              chatbot — it is an auditor with a structured output contract
              and the authority to veto.
            </p>
          </div>

          <div className="lp-novelty-pills">
            {[
              { label: 'Geographic Fairness', color: 'amber' },
              { label: 'Structural Blind Spots', color: 'blue' },
              { label: 'Borderline Detection', color: 'blue' },
              { label: 'Driver Zone Familiarity', color: 'green' },
              { label: 'Cargo Risk Audit', color: 'green' },
              { label: 'Override Authority', color: 'red' },
            ].map((pill) => (
              <div className={`lp-novelty-pill lp-pill-${pill.color}`} key={pill.label}>
                {pill.label}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Team ────────────────────────────────────────────────────── */}
      <section className="lp-team-section" id="team">
        <div className="lp-section-inner">
          <p className="lp-section-overline">Built by</p>
          <h2 className="lp-section-heading">The Team</h2>
          <div className="lp-team-grid">
            {TEAM.map((member) => (
              <div className="lp-team-card" key={member.name}>
                <div className="lp-team-avatar">
                  {member.initials}
                </div>
                <div className="lp-team-name">{member.name}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ─────────────────────────────────────────────────────── */}
      <section className="lp-cta-section">
        <div className="lp-section-inner lp-cta-inner">
          <h2 className="lp-cta-heading">See it reason in real time.</h2>
          <p className="lp-cta-sub">
            Pick a scenario and watch the two agents deliberate live.
          </p>
          <button className="lp-launch-btn" onClick={onLaunch} type="button">
            <span>Launch ALRO</span>
            <svg className="lp-launch-arrow" width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M3 9h12M10 4l5 5-5 5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────────────── */}
      <footer className="lp-footer">
        <div className="lp-footer-inner">
          <div className="lp-nav-brand">
            <span className="lp-nav-dot" />
            <span className="lp-nav-wordmark">ALRO</span>
          </div>
          <span className="lp-footer-copy">
            Autonomous Logistics and Routing Optimizer
          </span>
        </div>
      </footer>
    </div>
  );
}
