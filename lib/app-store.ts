import { lookupApp } from "@/lib/itunes";

export async function lookupAppById(trackId: number) {
  return lookupApp(trackId);
}

export async function fetchAppStorePage(trackViewUrl: string): Promise<string> {
  const response = await fetch(trackViewUrl, {
    headers: {
      "User-Agent": "Mozilla/5.0 (compatible; MobileAppPrivacy/0.1)"
    },
    next: { revalidate: 3600 }
  });

  if (!response.ok) {
    throw new Error(`App Store page fetch failed with status ${response.status}.`);
  }

  return response.text();
}

