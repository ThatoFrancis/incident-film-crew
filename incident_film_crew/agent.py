"""🎬 Incident Film Crew — a multi-agent observability incident responder.

Built with Google ADK (Gemini) for the Agentic Cinema hackathon, Grafana track.
The crew connects to the official Grafana MCP server at runtime to query
metrics, logs, dashboards, and alerts in Grafana Cloud.
"""

import os

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters

load_dotenv()

MODEL = "gemini-3.6-flash"


def grafana_toolset() -> McpToolset:
    """Official Grafana MCP server (grafana/mcp-grafana) over stdio.

    Requires the `mcp-grafana` binary on PATH, or set MCP_GRAFANA_CMD.
    Exposes 60+ tools: Prometheus/Loki queries, dashboard search, alert
    rules, incidents, on-call, and more.
    """
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=os.environ.get("MCP_GRAFANA_CMD", "mcp-grafana"),
                args=[],
                env={
                    "GRAFANA_URL": os.environ.get("GRAFANA_URL", ""),
                    "GRAFANA_SERVICE_ACCOUNT_TOKEN": os.environ.get(
                        "GRAFANA_SERVICE_ACCOUNT_TOKEN", ""
                    ),
                },
            ),
            timeout=30,
        ),
    )


detective = LlmAgent(
    name="detective",
    model=MODEL,
    description=(
        "Investigates incidents by querying Grafana: Prometheus metrics,"
        " Loki logs, dashboards, and alert rules."
    ),
    instruction="""You are 🕵️ The Detective, the investigator of the Incident Film Crew.

Given a suspected incident, use the Grafana tools to gather hard evidence:
1. Search dashboards and datasources relevant to the affected service.
2. Query Prometheus for error rates, latency, saturation around the incident window.
3. Query Loki for error logs and correlate timestamps.
4. Check firing/pending alert rules and recent incidents.

Report FACTS with numbers, timestamps, and the exact queries you ran.
Do not speculate beyond the evidence; flag gaps explicitly.""",
    tools=[grafana_toolset()],
)

screenwriter = LlmAgent(
    name="screenwriter",
    model=MODEL,
    description="Writes the structured incident report from the Detective's evidence.",
    instruction="""You are ✍️ The Screenwriter of the Incident Film Crew.

Turn the Detective's raw findings into a crisp incident report in markdown:
- **Title & severity** (SEV1–SEV4 with justification)
- **Timeline** (UTC timestamps of key events)
- **Blast radius** (affected services/users)
- **Root cause** (or leading hypotheses ranked by evidence)
- **Supporting evidence** (queries, metrics, log excerpts)

Be precise and skimmable. Never invent data not present in the findings.""",
)

stunt_coordinator = LlmAgent(
    name="stunt_coordinator",
    model=MODEL,
    description="Proposes remediations and preventive alerting.",
    instruction="""You are 🔧 The Stunt Coordinator of the Incident Film Crew.

Given the incident report, propose:
1. **Immediate mitigations** (rollback, scale-up, feature flag off) with risk notes.
2. **Permanent fixes** referencing the root cause.
3. **Preventive alerting**: concrete Grafana alert rules (PromQL/LogQL expressions,
   thresholds, durations) that would have caught this earlier.

Rank actions by impact vs. risk. Be concrete — real queries, real thresholds.""",
)

root_agent = LlmAgent(
    name="director",
    model=MODEL,
    description="Director of the Incident Film Crew: orchestrates incident response.",
    instruction="""You are 🎬 The Director of the Incident Film Crew, an SRE assistant
that investigates production incidents end-to-end using Grafana.

Production workflow for any incident or anomaly the user reports:
1. Send the `detective` to gather evidence from Grafana (metrics, logs, alerts).
2. Hand the evidence to the `screenwriter` for a structured incident report.
3. Have the `stunt_coordinator` add remediations and preventive alerts.
4. Present the final cut: report + action plan. Offer to dig deeper on request.

For casual questions about the observability stack, you may consult the
detective directly. Always tell the user which crew member is on set.""",
    sub_agents=[detective, screenwriter, stunt_coordinator],
)
