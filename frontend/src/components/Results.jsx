import React from "react";

function EmptyState({ text }) {
  return <div className="empty">{text}</div>;
}

export default function Results({ results }) {
  const candidateSkills = results?.candidate_skills || [];
  const requiredSkills = results?.required_skills || [];
  const gap = results?.skill_gap || {};

  const missing = gap.missing_skills || [];
  const matched = gap.matched_skills || [];

  return (
    <div className="results">
      <section className="results-section">
        <h2>Candidate Skills</h2>
        {candidateSkills.length === 0 ? (
          <EmptyState text="No candidate skills extracted." />
        ) : (
          <ul className="list">
            {candidateSkills.map((s, idx) => (
              <li key={`${s.skill_name}-${idx}`} className="list-item">
                <div className="skill-name">{s.skill_name}</div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="results-section">
        <h2>Required Skills</h2>
        {requiredSkills.length === 0 ? (
          <EmptyState text="No required skills extracted." />
        ) : (
          <ul className="list">
            {requiredSkills.map((s, idx) => (
              <li key={`${s.skill_name}-${idx}`} className="list-item">
                <div className="skill-name">{s.skill_name}</div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="results-section">
        <h2>Skill Gap</h2>

        <div className="subsection">
          <h3>Missing Skills</h3>
          {missing.length === 0 ? <EmptyState text="None" /> : null}
          {missing.length > 0 ? (
            <ul className="list">
              {missing.map((name, idx) => (
                <li key={`${name}-${idx}`}>{name}</li>
              ))}
            </ul>
          ) : null}
        </div>

        <div className="subsection">
          <h3>Matched Skills</h3>
          {matched.length === 0 ? <EmptyState text="None" /> : null}
          {matched.length > 0 ? (
            <ul className="list">
              {matched.map((name, idx) => (
                <li key={`${name}-${idx}`}>{name}</li>
              ))}
            </ul>
          ) : null}
        </div>
      </section>
    </div>
  );
}

