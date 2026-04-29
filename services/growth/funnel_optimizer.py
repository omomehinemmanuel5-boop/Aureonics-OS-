class FunnelOptimizer:
    def optimize(self, analytics: dict, current_hook: str) -> str:
        if analytics.get("reply_rate", 0) < 0.15:
            return current_hook + " | variant: tighter pain hypothesis"
        if analytics.get("positive_reply_rate", 0) < 0.25:
            return current_hook + " | variant: stronger risk-reduction proof"
        return current_hook + " | keep"
