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
};
