"""Seed demo telemetry for the Incident Film Crew demo.

Simulates "PopcornFlix", a video streaming platform, during the live premiere
of "Meridian Falls". A CDN edge degradation in eu-west drives playback errors
and rebuffering up while concurrent viewers climb.

Pushes metrics to Grafana Cloud (Influx line-protocol endpoint -> Mimir) and
logs to Grafana Cloud Loki. Backfills ~10 minutes of healthy baseline, then
emits live incident samples every 15s until Ctrl+C.

Required env vars (see .env.example):
  GC_METRICS_URL, GC_METRICS_USER, GC_LOGS_URL, GC_LOGS_USER, GC_WRITE_TOKEN
"""

import math
import os
import random
import time

import requests
from dotenv import load_dotenv

load_dotenv()

METRICS_URL = os.environ["GC_METRICS_URL"]
METRICS_USER = os.environ["GC_METRICS_USER"]
LOGS_URL = os.environ["GC_LOGS_URL"]
LOGS_USER = os.environ["GC_LOGS_USER"]
TOKEN = os.environ["GC_WRITE_TOKEN"]

REGIONS = ["eu-west", "us-east", "af-south"]
BAD_REGION = "eu-west"
STEP_SECONDS = 15
BACKFILL_MINUTES = 10

session = requests.Session()


def severity(elapsed_s: float) -> float:
    """0.0 (healthy) -> 1.0 (full incident), ramping over 4 minutes."""
    if elapsed_s <= 0:
        return 0.0
    return min(1.0, elapsed_s / 240.0)


def sample_metrics(ts_s: float, sev: float) -> list[str]:
    """One scrape interval of metrics as influx line-protocol lines."""
    ns = int(ts_s * 1e9)
    lines = []
    for region in REGIONS:
        bad = sev if region == BAD_REGION else 0.0
        viewers = 40000 + 25000 * math.sin(ts_s / 900) + random.uniform(-800, 800)
        if region == BAD_REGION:
            viewers *= 1.4  # premiere audience concentrated in eu-west
        err_rate = 0.2 + 14.0 * bad + random.uniform(-0.05, 0.05)
        rebuffer = 0.008 + 0.11 * bad + random.uniform(-0.001, 0.001)
        cdn_p99_ms = 180 + 2400 * bad + random.uniform(-15, 15)
        cdn_5xx = 0.1 + 9.0 * bad + random.uniform(-0.05, 0.05)
        origin_cpu = 0.35 + 0.5 * bad + random.uniform(-0.02, 0.02)
        tags = f"region={region},platform=popcornflix,event=meridian_falls_premiere"
        lines += [
            f"popcornflix,{tags} concurrent_viewers={max(viewers, 0):.0f} {ns}",
            f"popcornflix,{tags} playback_error_rate={max(err_rate, 0):.3f} {ns}",
            f"popcornflix,{tags} rebuffer_ratio={max(rebuffer, 0):.4f} {ns}",
            f"popcornflix,{tags} cdn_request_duration_p99_ms={max(cdn_p99_ms, 1):.0f} {ns}",
            f"popcornflix,{tags} cdn_5xx_rate={max(cdn_5xx, 0):.3f} {ns}",
            f"popcornflix,{tags} origin_cpu_utilization={min(max(origin_cpu, 0), 1):.3f} {ns}",
        ]
    return lines


def sample_logs(ts_s: float, sev: float) -> list[dict]:
    """Loki streams for one interval."""
    ns = int(ts_s * 1e9)
    streams = []
    info = [
        "manifest served title=meridian_falls bitrate=auto",
        "session started device=smart_tv drm=widevine",
        "segment served cache=HIT ttfb_ms=42",
    ]
    streams.append(
        {
            "stream": {
                "service": "cdn-edge",
                "region": "us-east",
                "level": "info",
                "platform": "popcornflix",
            },
            "values": [[str(ns), random.choice(info)]],
        }
    )
    if sev > 0.1:
        errors = [
            "upstream connect timeout origin=origin-eu-1 after=5000ms",
            "TLS handshake timeout pop=lhr-edge-07",
            "cache MISS storm shield=eu-west segment=meridian_falls_1080p",
            'HTTP 504 route=/segment/meridian_falls_4k err="origin unreachable"',
            "config drift detected: edge-cache-policy v2.4.1 rolled out to eu-west pops",
        ]
        n_err = 1 + int(sev * 4)
        for _ in range(n_err):
            streams.append(
                {
                    "stream": {
                        "service": "cdn-edge",
                        "region": BAD_REGION,
                        "level": "error",
                        "platform": "popcornflix",
                    },
                    "values": [[str(ns), random.choice(errors)]],
                }
            )
        streams.append(
            {
                "stream": {
                    "service": "playback-api",
                    "region": BAD_REGION,
                    "level": "error",
                    "platform": "popcornflix",
                },
                "values": [
                    [
                        str(ns),
                        f"playback failure title=meridian_falls code=MEDIA_ERR_NETWORK "
                        f"affected_sessions={int(200 * sev)}",
                    ]
                ],
            }
        )
    return streams


def push_metrics(lines: list[str]) -> None:
    r = session.post(
        METRICS_URL,
        data="\n".join(lines),
        auth=(METRICS_USER, TOKEN),
        headers={"Content-Type": "text/plain"},
        timeout=15,
    )
    r.raise_for_status()


def push_logs(streams: list[dict]) -> None:
    if not streams:
        return
    r = session.post(
        LOGS_URL,
        json={"streams": streams},
        auth=(LOGS_USER, TOKEN),
        timeout=15,
    )
    r.raise_for_status()


def main() -> None:
    now = time.time()
    incident_start = now  # incident begins the moment the seeder starts

    print(f"Backfilling {BACKFILL_MINUTES} min of healthy baseline...")
    ts = now - BACKFILL_MINUTES * 60
    while ts < now:
        push_metrics(sample_metrics(ts, 0.0))
        push_logs(sample_logs(ts, 0.0))
        ts += STEP_SECONDS
    print("Baseline done. Incident is now unfolding — Ctrl+C to stop.")

    while True:
        t = time.time()
        sev = severity(t - incident_start)
        push_metrics(sample_metrics(t, sev))
        push_logs(sample_logs(t, sev))
        print(f"pushed sev={sev:.2f}", flush=True)
        time.sleep(STEP_SECONDS)


if __name__ == "__main__":
    main()
