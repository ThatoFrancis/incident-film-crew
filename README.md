# 🎬 Incident Film Crew

A multi-agent observability incident responder built for the
[Agentic Cinema: The Blockbuster Hackathon](https://agentic-cinema.devpost.com/)
— **Grafana Labs track**.

A "film crew" of Gemini agents, orchestrated with the **Google Agent
Development Kit (ADK)**, investigates production incidents end-to-end using
the **Grafana MCP server** at runtime:

| Agent | Role |
|---|---|
| 🎬 **Director** | Orchestrates the crew, talks to the user, produces the final cut || 🕵️ **Detective** | Queries Grafana metrics (Prometheus), logs (Loki), dashboards & alerts via MCP tools to find the root cause |
| ✍️ **Screenwriter** | Turns raw findings into a structured incident report (timeline, blast radius, root cause) |
| 🔧 **Stunt Coordinator** | Proposes concrete remediations and follow-up alert rules |

## Architecture

```
User ──▶ Director (LlmAgent, gemini-3.6-flash)
              │ delegates
              ├──▶ Detective ──▶ Grafana MCP server ──▶ Grafana Cloud
              ├──▶ Screenwriter
              └──▶ Stunt Coordinator
```

- **AI:** Gemini via `google-adk` / `google-genai` (Google Cloud AI only)
- **Partner integration:** official [`mcp-grafana`](https://github.com/grafana/mcp-grafana)
  MCP server, loaded as an ADK `MCPToolset` and called at runtime

## Prerequisites

- Python 3.10+
- A Gemini API key ([Google AI Studio](https://aistudio.google.com/apikey))
- A Grafana Cloud stack (free tier works) + service account token
- The Grafana MCP server binary: `go install github.com/grafana/mcp-grafana/cmd/mcp-grafana@latest`
  (or download a [release binary](https://github.com/grafana/mcp-grafana/releases), or use Docker)

## Run it

```bash
pip install -r requirements.txt
copy .env.example incident_film_crew\.env   # then fill in your keys
adk web                                     # from the repo root
```

Open http://localhost:8000, pick `incident_film_crew`, and try:

> "We're seeing elevated error rates in checkout — investigate."

## License

AGPL-3.0 — see [LICENSE](LICENSE). Commercial licensing available on request.
