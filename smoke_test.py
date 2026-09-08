"""Smoke test: verify the Grafana MCP server connects and tools work."""

import asyncio

from incident_film_crew.agent import grafana_toolset


async def main():
    ts = grafana_toolset()
    tools = await ts.get_tools()
    print(f"Connected. {len(tools)} Grafana MCP tools available.")
    print("Sample:", ", ".join(t.name for t in tools[:8]))
    ds = next(t for t in tools if t.name == "list_datasources")
    result = await ds.run_async(args={}, tool_context=None)
    print("Datasources:", str(result)[:500])
    await ts.close()


if __name__ == "__main__":
    asyncio.run(main())
