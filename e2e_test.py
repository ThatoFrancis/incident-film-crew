"""End-to-end test: run the full Incident Film Crew pipeline against live data."""

import asyncio
import sys

sys.stdout.reconfigure(encoding="utf-8")

from google.adk.runners import InMemoryRunner
from google.genai import types

from incident_film_crew.agent import root_agent


async def main():
    runner = InMemoryRunner(agent=root_agent, app_name="incident_film_crew")
    session = await runner.session_service.create_session(
        app_name="incident_film_crew", user_id="e2e"
    )
    msg = types.Content(
        role="user",
        parts=[
            types.Part(
                text=(
                    "Viewers are reporting buffering and playback failures during "
                    "the Meridian Falls live premiere. Investigate now."
                )
            )
        ],
    )
    async for event in runner.run_async(
        user_id="e2e", session_id=session.id, new_message=msg
    ):
        author = getattr(event, "author", "?")
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"\n===== [{author}] =====\n{part.text}")
                elif part.function_call:
                    print(f"[{author}] -> tool: {part.function_call.name}")


if __name__ == "__main__":
    asyncio.run(main())
