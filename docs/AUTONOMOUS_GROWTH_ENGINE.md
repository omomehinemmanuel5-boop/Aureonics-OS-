# Autonomous Outbound + Growth Engine (LEX AUREON)

This implementation adds a complete automated GTM loop under `services/growth` and `services/integrations`.

## Included Services
- Lead discovery, scoring, persona classification
- Personalized outreach generation
- DM orchestration with 24h follow-up guard
- Reply classification and auto-routing
- Demo booking integration
- CRM sync and analytics engine
- Funnel optimization loop for message iteration

## Run locally
```bash
python -m services.growth.engine
```

## Run with Docker
```bash
docker-compose up
```

## Daily Autonomous Loop
1. Discover leads from source connectors.
2. Classify persona + score intent.
3. Generate personalized outbound message.
4. Process reply signal and branch.
5. Book demos for positive intent.
6. Track metrics + optimize hooks.
