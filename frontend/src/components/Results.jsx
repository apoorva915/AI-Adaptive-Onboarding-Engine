import React from "react";
import LearningPathGraph from "./LearningPathGraph.jsx";

function EmptyState({ text }) {
  return <div className="empty">{text}</div>;
}

function SkillTags({ items, getLabel }) {
  if (!items || items.length === 0) return <EmptyState text="None" />;
  return (
    <div className="skill-tags">
      {items.map((item, idx) => (
        <span key={`${getLabel(item)}-${idx}`} className="skill-tag">
          {getLabel(item)}
        </span>
      ))}
    </div>
  );
}

export default function Results({ results }) {
  const candidateSkills = results?.candidate_skills || [];
  const requiredSkills = results?.required_skills || [];
  const gap = results?.skill_gap || {};
  const learningPath = results?.learning_path || [];
  const learningPathGraph = results?.learning_path_graph || null;

  const missing = gap.missing_skills || [];
  const matched = gap.matched_skills || [];

  return (
    <div className="results">
      <div className="top-skill-grid">
        <section className="results-section">
          <h2 className="section-title">Candidate Skills</h2>
          {candidateSkills.length === 0 ? (
            <EmptyState text="No candidate skills extracted." />
          ) : (
            <SkillTags items={candidateSkills} getLabel={(s) => s.skill_name} />
          )}
        </section>

        <section className="results-section">
          <h2 className="section-title">Required Skills</h2>
          {requiredSkills.length === 0 ? (
            <EmptyState text="No required skills extracted." />
          ) : (
            <SkillTags items={requiredSkills} getLabel={(s) => s.skill_name} />
          )}
        </section>
      </div>

      <section className="results-section">
        <h2 className="section-title">Skill Gap</h2>

        <div className="subsection">
          <h3>Missing Skills</h3>
          <SkillTags items={missing} getLabel={(name) => name} />
        </div>

        <div className="subsection">
          <h3>Matched Skills</h3>
          <SkillTags items={matched} getLabel={(name) => name} />
        </div>
      </section>

      <section className="results-section graph-section">
        <h2 className="section-title">Adaptive Learning Path Graph</h2>
        {learningPathGraph ? (
          <LearningPathGraph graph={learningPathGraph} />
        ) : (
          <EmptyState text="No learning graph generated." />
        )}
      </section>

      <section className="results-section">
        <h2 className="section-title">Adaptive Learning Path Steps</h2>
        {learningPath.length === 0 ? (
          <EmptyState text="No learning path generated." />
        ) : (
          <div className="steps-list">
            {learningPath.map((step) => (
              <div key={`${step.step}-${step.skill || step.topic}`} className="step-card">
                <div className="skill-name">
                  Step {step.step} - {step.skill || step.topic}
                </div>
                {step.link ? (
                  <div className="skill-meta">
                    <a href={step.link} target="_blank" rel="noreferrer">
                      Link: Open module
                    </a>
                  </div>
                ) : (
                  <div className="skill-meta">Link: N/A</div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

