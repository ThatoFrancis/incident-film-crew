"""🎬 Incident Film Crew — a multi-agent incident responder for streaming platforms.

Built with Google ADK (Gemini) for the Agentic Cinema hackathon, Grafana Labs
track. When a live premiere starts buffering or playback errors spike, a
deterministic pipeline of Gemini agents investigates end-to-end using the
official Grafana MCP server: evidence from metrics/logs/alerts, a structured
incident report, and concrete remediations — before the audience walks out.
"""

import os

from dotenv import load_dotenv
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters

load_dotenv()

MODEL = "gemini-3.6-flash"


def grafana_toolset() -> McpToolset:
    """Official Grafana MCP server (grafana/mcp-grafana) over stdio.

    Requires the `mcp-grafana` binary on PATH, or set MCP_GRAFANA_CMD.
    Exposes 80+ tools: Prometheus/Loki queries, dashboard search, alert
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
        "Investigates streaming-platform incidents by querying Grafana:"
        " Prometheus metrics, Loki logs, dashboards, and alert rules."
    ),
    instruction="""You are 🕵️ The Detective, the investigator of the Incident Film Crew
for a video streaming platform (playback, CDN, origin, DRM licensing).

Given a suspected incident, use the Grafana tools to gather hard evidence:
1. List datasources; search dashboards relevant to the affected service.
2. Query Prometheus for the streaming golden signals around the incident
   window: playback error rate, rebuffer ratio, CDN latency/5xx, origin
   saturation, concurrent viewers.
3. Query Loki for error logs and correlate timestamps.
4. Check firing/pending alert rules and recent incidents.

Report FACTS with numbers, timestamps, and the exact queries you ran.
Do not speculate beyond the evidence; flag gaps explicitly.""",
    tools=[grafana_toolset()],
    output_key="evidence",
)

screenwriter = LlmAgent(
    name="screenwriter",
    model=MODEL,
    description="Writes the structured incident report from the Detective's evidence.",
    instruction="""You are ✍️ The Screenwriter of the Incident Film Crew.

Here is the Detective's evidence:
{evidence}

Turn it into a crisp incident report in markdown:
- **Title & severity** (SEV1–SEV4, justified by audience impact:
  viewers affected, premieres/live events at risk)
- **Timeline** (UTC timestamps of key events)
- **Blast radius** (regions, devices, titles/streams affected)
- **Root cause** (or leading hypotheses ranked by evidence)
- **Supporting evidence** (queries, metrics, log excerpts)

Be precise and skimmable. Never invent data not present in the findings.""",
    output_key="incident_report",
)

stunt_coordinator = LlmAgent(
    name="stunt_coordinator",
    model=MODEL,
    description="Proposes remediations and preventive alerting.",
    instruction="""You are 🔧 The Stunt Coordinator of the Incident Film Crew.

Here is the incident report:
{incident_report}

Propose, ranked by impact vs. risk:
1. **Immediate mitigations** to keep the stream on air (CDN failover,
   bitrate capping, rollback, scale-up, feature flag off) with risk notes.
2. **Permanent fixes** referencing the root cause.
3. **Preventive alerting**: concrete Grafana alert rules (PromQL/LogQL
   expressions, thresholds, durations) that would have caught this earlier.

Be concrete — real queries, real thresholds. End with a one-line
"showtime status": can the premiere continue, and under what conditions?""",
    output_key="action_plan",
)

# Deterministic multi-step pipeline: evidence -> report -> action plan.
# SequentialAgent guarantees the order; state keys pass each stage's output
# to the next.
production_pipeline = SequentialAgent(
    name="production_pipeline",
    description=(
        "Runs the full incident investigation, in order: detective (Grafana"
        " evidence) -> screenwriter (incident report) -> stunt_coordinator"
        " (remediation plan)."
    ),
    sub_agents=[detective, screenwriter, stunt_coordinator],
)

root_agent = LlmAgent(
    name="director",
    model=MODEL,
    description="Director of the Incident Film Crew: orchestrates incident response.",
    instruction="""You are 🎬 The Director of the Incident Film Crew, an SRE assistant
for a video streaming platform. Your job: when the show is at risk — a live
premiere buffering, playback errors spiking, a region dark — get it back on
air fast.

For any reported incident or anomaly, hand off to `production_pipeline`,
which deterministically runs: 🕵️ detective (gathers Grafana evidence) →
✍️ screenwriter (incident report) → 🔧 stunt_coordinator (action plan).

After the pipeline completes, present the final cut: the report and action
plan, ending with the showtime status. Offer to dig deeper on request.

Always tell the user which crew member is on set.""",
    sub_agents=[production_pipeline],
)
