import type { PrivacyProfile } from "@/lib/types";

function clampScore(score: number) {
  return Math.max(1, Math.min(10, score));
}

export function scorePrivacy(profile: PrivacyProfile) {
  let score = 10;
  const reasons: string[] = [];

  if (profile.dataNotCollected) {
    reasons.push("The app declares that it does not collect data.");
  }

  if (profile.tracking) {
    score -= 3;
    reasons.push("The App Store disclosure suggests data may be used to track the user.");
  }

  if (profile.linkedToUser.length > 0) {
    score -= 2;
    reasons.push(`Data linked to the user: ${profile.linkedToUser.join(", ")}.`);
  }

  if (profile.categories.includes("Location")) {
    score -= 2;
    reasons.push("Location data appears in the disclosure.");
  }

  if (profile.categories.includes("Financial Info")) {
    score -= 2;
    reasons.push("Financial information appears in the disclosure.");
  }

  if (profile.categories.includes("Health & Fitness")) {
    score -= 2;
    reasons.push("Health and fitness data appears in the disclosure.");
  }

  if (profile.categories.includes("Contacts")) {
    score -= 2;
    reasons.push("Contacts data appears in the disclosure.");
  }

  if (profile.categories.includes("Browsing History")) {
    score -= 2;
    reasons.push("Browsing history appears in the disclosure.");
  }

  if (profile.categories.includes("Search History")) {
    score -= 2;
    reasons.push("Search history appears in the disclosure.");
  }

  if (profile.categories.includes("Identifiers")) {
    score -= 1;
    reasons.push("Identifiers appear in the disclosure.");
  }

  if (profile.categories.includes("Purchases")) {
    score -= 1;
    reasons.push("Purchase-related data appears in the disclosure.");
  }

  if (profile.categories.includes("Usage Data")) {
    score -= 1;
    reasons.push("Usage data appears in the disclosure.");
  }

  if (profile.categories.includes("Diagnostics")) {
    score -= 1;
    reasons.push("Diagnostics data appears in the disclosure.");
  }

  if (profile.dataNotCollected && !profile.tracking && profile.categories.length === 0) {
    score += 1;
    reasons.push("The disclosure is minimal and does not indicate tracking.");
  }

  const finalScore = clampScore(score);

  return {
    score: finalScore,
    reasons,
    summary:
      finalScore >= 8
        ? "Low declared data collection"
        : finalScore >= 5
          ? "Moderate declared data collection"
          : "High declared data collection"
  };
}

