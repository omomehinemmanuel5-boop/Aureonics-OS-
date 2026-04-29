export type LexDiffChunk = {
  type: 'unchanged' | 'removed' | 'added';
  text: string;
};

export type LexResponse = {
  raw_output: string;
  governed_output: string;
  final_output: string;
  intervention: boolean;
  intervention_reason: string;
  semantic_diff_score: number;
  M: number;
  upgrade_required?: boolean;
  run_count?: number;
  remaining_free_runs?: number;
  usage_today?: number;
  error?: string;
  message?: string;
  metrics?: {
    entropy: number;
    meaning: number;
    predicted_risk: number;
    actual_intervention: number;
  };
  diff?: LexDiffChunk[];
};
