import React, { useState } from "react";
import UploadForm from "./components/UploadForm.jsx";
import Results from "./components/Results.jsx";

export default function App() {
  const [results, setResults] = useState(null);
  const [error, setError] = useState("");

  return (
    <div className="app">
      <h1>AI-Adaptive Onboarding Engine (MVP)</h1>
      <UploadForm
        onSuccess={(data) => {
          setResults(data);
          setError("");
        }}
        onError={(msg) => {
          setError(msg);
        }}
      />

      {error ? <div className="error">Error: {error}</div> : null}
      {results ? <Results results={results} /> : null}
    </div>
  );
}

