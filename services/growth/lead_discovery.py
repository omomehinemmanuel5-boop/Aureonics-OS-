from services.integrations.x_api import XApiClient


class LeadDiscovery:
    def __init__(self) -> None:
        self.x_client = XApiClient()

    def discover(self) -> list:
        # Hooks for GitHub/ProductHunt/LinkedIn can be attached here.
        return self.x_client.fetch_ai_leads()
