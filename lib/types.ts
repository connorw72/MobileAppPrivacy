export type SearchResult = {
  trackId: number;
  trackName: string;
  sellerName: string;
  primaryGenreName: string;
  trackViewUrl: string;
  artworkUrl100: string;
  formattedPrice?: string;
  price?: number;
};

export type PrivacyProfile = {
  dataNotCollected: boolean;
  tracking: boolean;
  linkedToUser: string[];
  notLinkedToUser: string[];
  categories: string[];
  sensitiveCategories: string[];
  rawText: string;
};

export type AnalysisResponse = {
  app: SearchResult;
  privacy: PrivacyProfile;
  score: number;
  reasons: string[];
  summary: string;
  sourceNote: string;
  fetchedAt: string;
};

