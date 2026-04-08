import type { PrivacyProfile } from "@/lib/types";

const CATEGORY_LABELS = [
  "Contact Info",
  "Health & Fitness",
  "Financial Info",
  "Location",
  "Sensitive Info",
  "Contacts",
  "User Content",
  "Browsing History",
  "Search History",
  "Identifiers",
  "Purchases",
  "Usage Data",
  "Diagnostics",
  "Surroundings",
  "Other Data"
];

const SENSITIVE_LABELS = [
  "Health & Fitness",
  "Financial Info",
  "Location",
  "Sensitive Info",
  "Contacts",
  "Browsing History",
  "Search History"
];

function normalizeWhitespace(value: string): string {
  return value
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function includesPhrase(text: string, phrase: string): boolean {
  return text.toLowerCase().includes(phrase.toLowerCase());
}

function unique(items: string[]) {
  return [...new Set(items)];
}

function collectCategories(text: string): string[] {
  return CATEGORY_LABELS.filter((label) => includesPhrase(text, label));
}

export function parsePrivacyDetails(html: string): PrivacyProfile {
  const text = normalizeWhitespace(html);

  const dataNotCollected = includesPhrase(text, "Data Not Collected");
  const tracking =
    includesPhrase(text, "Data Used to Track You") || includesPhrase(text, "tracking");

  const linkedToUserSection =
    text.match(/Data Linked to You([\s\S]*?)(Data Not Linked to You|Data Used to Track You|Accessibility|Information)/i)?.[1] ??
    "";
  const notLinkedToUserSection =
    text.match(/Data Not Linked to You([\s\S]*?)(Data Linked to You|Data Used to Track You|Accessibility|Information)/i)?.[1] ??
    "";

  const linkedToUser = collectCategories(linkedToUserSection);
  const notLinkedToUser = collectCategories(notLinkedToUserSection);
  const categories = unique([
    ...collectCategories(text),
    ...linkedToUser,
    ...notLinkedToUser
  ]);
  const sensitiveCategories = categories.filter((category) => SENSITIVE_LABELS.includes(category));

  return {
    dataNotCollected,
    tracking,
    linkedToUser,
    notLinkedToUser,
    categories,
    sensitiveCategories,
    rawText: text
  };
}

