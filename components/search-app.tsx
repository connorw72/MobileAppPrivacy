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

      <section className="section">
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

          {!searchPending && results.length === 0 ? (
            <p className="message">Search for an app to see results.</p>
          ) : null}
        </div>
      </section>

      <section className="section">
        <h2>Privacy score</h2>
        <p>{analysisPending ? "Analyzing..." : "Ready"}</p>

        {analysis ? (
          <div className="scoreBox">
            <p className="scoreNumber">{analysis.score}/10</p>
            <p>{analysis.summary}</p>
          </div>
        ) : (
          <p className="message">Select an app to view its score.</p>
        )}
      </section>
    </main>
  );
}
