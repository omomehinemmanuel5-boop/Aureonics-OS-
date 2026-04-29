from pathlib import Path

TEMPLATES = {
    "product_overview": "Product Overview for {account}\nCapabilities: {capabilities}\n",
    "technical_architecture": "Architecture for {account}\nComponents: {components}\n",
    "security_whitepaper": "Security Whitepaper\nControls: {controls}\n",
    "soc2_readiness": "SOC2 Readiness\nEvidence: {evidence}\n",
    "proposal_draft": "Proposal\nScope: {scope}\n",
    "roi_summary": "ROI Summary\nAssumptions: {assumptions}\n",
}


def generate_documents(output_dir: str, account: str) -> list[str]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    rendered = []
    for name, template in TEMPLATES.items():
        content = template.format(
            account=account,
            capabilities="autonomous orchestration",
            components="orchestrator, guardrails, integrations",
            controls="SOC2 CC6.1/CC7.2/CC8.1",
            evidence="audit log + RBAC + policy checks",
            scope="enterprise rollout",
            assumptions="time savings and conversion uplift",
        )
        file = out / f"{name}.md"
        file.write_text(content)
        rendered.append(str(file))
    return rendered
