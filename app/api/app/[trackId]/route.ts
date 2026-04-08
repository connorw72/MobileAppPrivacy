import { NextResponse } from "next/server";
import { getCachedAnalysis, setCachedAnalysis } from "@/lib/cache";
import { fetchAppStorePage, lookupAppById } from "@/lib/app-store";
import { parsePrivacyDetails } from "@/lib/privacy-parser";
import { scorePrivacy } from "@/lib/privacy-score";

export async function GET(
  _request: Request,
  context: { params: Promise<{ trackId: string }> }
) {
  const params = await context.params;
  const trackId = Number(params.trackId);

  if (Number.isNaN(trackId)) {
    return NextResponse.json({ error: "Invalid trackId." }, { status: 400 });
  }

  const cached = getCachedAnalysis(trackId);
  if (cached) {
    return NextResponse.json(cached);
  }

  try {
    const app = await lookupAppById(trackId);
    const html = await fetchAppStorePage(app.trackViewUrl);
    const privacy = parsePrivacyDetails(html);
    const scored = scorePrivacy(privacy);

    const response = {
      app,
      privacy,
      score: scored.score,
      reasons: scored.reasons,
      summary: scored.summary,
      sourceNote:
        "Derived from developer-provided App Store privacy disclosures. Apple notes these disclosures are not independently verified.",
      fetchedAt: new Date().toISOString()
    };

    setCachedAnalysis(trackId, response);

    return NextResponse.json(response);
  } catch (error) {
    const message = error instanceof Error ? error.message : "App analysis failed.";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

