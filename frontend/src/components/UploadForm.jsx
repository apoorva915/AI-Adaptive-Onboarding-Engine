import React, { useState } from "react";
import { analyzeSkills } from "../api.js";

export default function UploadForm({ onSuccess, onError }) {
  const [resumeFile, setResumeFile] = useState(null);
  const [jdFile, setJdFile] = useState(null);
  const [resumeText, setResumeText] = useState("");
  const [jdText, setJdText] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    onError("");

    try {
      const formData = new FormData();

      if (resumeFile) formData.append("resume_file", resumeFile);
      if (jdFile) formData.append("jd_file", jdFile);

      const rt = (resumeText || "").trim();
      const jt = (jdText || "").trim();
      if (rt) formData.append("resume_text", rt);
      if (jt) formData.append("jd_text", jt);

      const data = await analyzeSkills(formData);
      onSuccess(data);
    } catch (err) {
      onError(err?.message || "Failed to analyze skills");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="form" onSubmit={handleSubmit}>
      <div className="section">
        <h2>Resume</h2>
        <label>
          Resume PDF/DOCX:
          <input
            type="file"
            accept=".pdf,.docx"
            onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
          />
        </label>

        <label>
          OR Paste Resume Text:
          <textarea
            rows={6}
            value={resumeText}
            onChange={(e) => setResumeText(e.target.value)}
            placeholder="Paste resume content here..."
          />
        </label>
      </div>

      <div className="section">
        <h2>Job Description / Requirements</h2>
        <label>
          JD PDF/DOCX:
          <input
            type="file"
            accept=".pdf,.docx"
            onChange={(e) => setJdFile(e.target.files?.[0] || null)}
          />
        </label>

        <label>
          OR Paste JD Text:
          <textarea
            rows={6}
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            placeholder="Paste job description or requirements here..."
          />
        </label>
      </div>

      <button className="button" type="submit" disabled={loading}>
        {loading ? "Analyzing..." : "Analyze Skills"}
      </button>
    </form>
  );
}

