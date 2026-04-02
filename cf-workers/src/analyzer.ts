export interface PlayerAnalysisReport {
  player_summary: string;
  content_focus: "offensive" | "defensive" | "balanced";
  dimensions: {
    offense: DimensionResult;
    defense: DimensionResult;
  };
  improvements: string[];
}

interface DimensionResult {
  score: number | null;
  observability: "full" | "partial" | "none";
  notes: string;
  highlights: { timestamp: string; description: string }[];
}
