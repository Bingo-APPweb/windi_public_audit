#!/usr/bin/env python3
"""Test MARIA query flow to find the bug."""

import asyncio
import sys
sys.path.insert(0, "/opt/windi/nomad-bot")

from services import maria_client

async def test():
    print("=== Testing 'Onde fica creperia Paris?' ===\n")

    # 1. Get location
    print("1. Getting location...")
    location = await maria_client.get_location()
    print(f"   location: {location}\n")

    lat = location.get("lat") if location.get("detected") else None
    lng = location.get("lng") if location.get("detected") else None

    # 2. Detect intent
    msg = "Onde fica creperia Paris?"
    intent = maria_client.detect_intent_local(msg, "PT")
    print(f"2. Local intent: {intent}\n")

    # 3. Call MARIA
    print("3. Calling MARIA /plan...")
    response = await maria_client.plan(
        message=msg,
        wallet_id="test-debug",
        lang="PT",
        lat=lat,
        lng=lng,
        intent_type=intent
    )

    print(f"   error: {response.get('error')}")
    print(f"   intent_parsed: {response.get('intent_parsed', {}).get('type')}")
    print(f"   decision.name: {response.get('decision', {}).get('name')}")
    print(f"   decision.type: {response.get('decision', {}).get('type')}")
    print(f"   maria_voice.PT: '{response.get('maria_voice', {}).get('PT', '')[:50]}...'")
    print()

    # 4. Try formatting
    print("4. Testing format_place_for_telegram...")
    decision = response.get("decision", {})
    try:
        details = maria_client.format_place_for_telegram(decision, "PT")
        print(f"   Success: {details[:100]}...")
    except Exception as e:
        print(f"   ERROR: {e}")

    print("\n=== Done ===")

asyncio.run(test())
