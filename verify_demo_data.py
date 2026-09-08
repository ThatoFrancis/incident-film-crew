"""Quick verification that seeded demo data is visible through the Grafana MCP."""

import asyncio

from incident_film_crew.agent import grafana_toolset


async def main():
    ts = grafana_toolset()
    tools = {t.name: t for t in await ts.get_tools()}
    r = await tools["query_prometheus"].run_async(
        args={
            "datasourceUid": "grafanacloud-prom",
            "expr": "popcornflix_playback_error_rate",
            "queryType": "instant",
            "startTime": "now",
            "endTime": "now",
        },
        tool_context=None,
    )
    print("METRICS:", str(r)[:800])
    r = await tools["query_loki_logs"].run_async(
        args={
            "datasourceUid": "grafanacloud-logs",
            "logql": '{platform="popcornflix", level="error"}',
            "limit": 3,
        },
        tool_context=None,
    )
    print("LOGS:", str(r)[:600])
    await ts.close()


if __name__ == "__main__":
    asyncio.run(main())
