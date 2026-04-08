import type { AnalysisResponse } from "@/lib/types";

const TTL_MS = 1000 * 60 * 60 * 12;
const cache = new Map<number, AnalysisResponse>();

export function getCachedAnalysis(trackId: number): AnalysisResponse | null {
  const record = cache.get(trackId);

  if (!record) {
    return null;
  }

  const age = Date.now() - new Date(record.fetchedAt).getTime();
  if (age > TTL_MS) {
    cache.delete(trackId);
    return null;
  }

  return record;
}

export function setCachedAnalysis(trackId: number, analysis: AnalysisResponse) {
  cache.set(trackId, analysis);
}

