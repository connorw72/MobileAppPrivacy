"use client";

import Image from "next/image";
import { FormEvent, useState, useTransition } from "react";
import type { AnalysisResponse, SearchResult } from "@/lib/types";

export function SearchApp() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [searchPending, startSearch] = useTransition();
  const [analysisPending, startAnalysis] = useTransition();

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    startSearch(async () => {
      setError(null);
      setAnalysis(null);
      setSelectedId(null);

      try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = (await response.json()) as { results?: SearchResult[]; error?: string };

        if (!response.ok) {
          throw new Error(data.error ?? "Search failed.");
        }

        setResults(data.results ?? []);
      } catch (searchError) {
        setResults([]);
        setError(searchError instanceof Error ? searchError.message : "Search failed.");
      }
    });
  }

  function handleAnalyze(trackId: number) {
    setSelectedId(trackId);

    startAnalysis(async () => {
      setError(null);

      try {
        const response = await fetch(`/api/app/${trackId}`);
        const data = (await response.json()) as AnalysisResponse & { error?: string };

        if (!response.ok) {
          throw new Error(data.error ?? "Analysis failed.");
        }

        setAnalysis(data);
      } catch (analysisError) {
        setAnalysis(null);
        setError(analysisError instanceof Error ? analysisError.message : "Analysis failed.");
      }
    });
  }

  const scoreColor =
    analysis === null
      ? "#888"
      : analysis.score >= 80
        ? "#22c55e"
        : analysis.score >= 50
          ? "#f59e0b"
          : "#ef4444";

  return (
    <main className="page">
      <section className="section">
        <h1>Mobile App Privacy</h1>
        <p>Search for an iOS app and view a privacy score.</p>

        <form className="searchForm" onSubmit={handleSearch}>
          <input
            aria-label="App name"
            className="textInput"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search for an iOS app"
            value={query}
          />
          <button className="button" disabled={searchPending || !query.trim()} type="submit">
            {searchPending ? "Searching..." : "Search"}
          </button>
        </form>
      </section>

      {error ? <p className="message error">{error}</p> : null}

      {/* Two-column layout once results exist */}
      <div className={`contentLayout ${results.length > 0 ? "hasResults" : ""}`}>

        {/* Left column: results list */}
        {results.length > 0 && (
          <section className="section resultsColumn">
            <h2>Results</h2>
            <div className="results">
              {results.map((result) => (
                <button
                  className={`resultButton ${selectedId === result.trackId ? "selected" : ""}`}
                  key={result.trackId}
                  onClick={() => handleAnalyze(result.trackId)}
                  type="button"
                >
                  <Image
                    alt={`${result.trackName} icon`}
                    className="icon"
                    height={60}
                    src={result.artworkUrl100}
                    width={60}
                  />
                  <span className="resultText">
                    <strong>{result.trackName}</strong>
                    <span>{result.sellerName}</span>
                  </span>
                </button>
              ))}
            </div>
          </section>
        )}

        {/* Right column: score panel — only shown after an app is clicked */}
        {selectedId !== null && (
          <section className="section scoreColumn">
            <h2>Privacy Score</h2>

            {analysisPending ? (
              <p className="message">Analyzing...</p>
            ) : analysis ? (
              <div className="scorePanel">
                {/* Score ring / number */}
                <div className="scoreRing" style={{ "--score-color": scoreColor } as React.CSSProperties}>
                  <span className="scoreNumber" style={{ color: scoreColor }}>
                    {analysis.score}
                  </span>
                  <span className="scoreOutOf">/100</span>
                </div>

                <p className="scoreSummary">{analysis.summary}</p>

                {/* Reasons list */}
                {analysis.reasons.length > 0 && (
                  <div className="reasonsList">
                    <h3>Why this score?</h3>
                    <ul>
                      {analysis.reasons.map((reason, index) => (
                        <li key={index}>{reason}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <p className="sourceNote">{analysis.sourceNote}</p>
              </div>
            ) : (
              <p className="message">Select an app to view its score.</p>
            )}
          </section>
        )}
      </div>

      {/* Empty state before any search */}
      {results.length === 0 && !searchPending && (
        <section className="section">
          <p className="message">Search for an app to see results.</p>
        </section>
      )}
    </main>
  );
}
