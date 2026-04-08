import type { SearchResult } from "@/lib/types";

type ItunesSearchResponse = {
  results: SearchResult[];
};

export async function searchApps(query: string): Promise<SearchResult[]> {
  const url = new URL("https://itunes.apple.com/search");
  url.searchParams.set("term", query);
  url.searchParams.set("entity", "software");
  url.searchParams.set("country", "us");
  url.searchParams.set("limit", "10");

  const response = await fetch(url, {
    headers: {
      "User-Agent": "MobileAppPrivacy/0.1"
    },
    next: { revalidate: 3600 }
  });

  if (!response.ok) {
    throw new Error(`iTunes search failed with status ${response.status}.`);
  }

  const data = (await response.json()) as ItunesSearchResponse;
  return data.results ?? [];
}

export async function lookupApp(trackId: number): Promise<SearchResult> {
  const url = new URL("https://itunes.apple.com/lookup");
  url.searchParams.set("id", String(trackId));
  url.searchParams.set("country", "us");
  url.searchParams.set("entity", "software");

  const response = await fetch(url, {
    headers: {
      "User-Agent": "MobileAppPrivacy/0.1"
    },
    next: { revalidate: 3600 }
  });

  if (!response.ok) {
    throw new Error(`App lookup failed with status ${response.status}.`);
  }

  const data = (await response.json()) as ItunesSearchResponse;
  const app = data.results?.[0];

  if (!app) {
    throw new Error("App not found in iTunes lookup.");
  }

  return app;
}

