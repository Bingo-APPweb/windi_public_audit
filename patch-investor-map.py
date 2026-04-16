#!/usr/bin/env python3
"""Add Bayern Süd Map to /investor/ page"""

FILE = "/var/www/investor/index.html"

OLD = '''<div class="system-item">
                    <div class="system-dot"></div>
                    <div>
                        <a href="https://windi-domain.com/enterprise/" target="_blank">W-Enterprise</a>
                        <span class="desc">AI Compliance Dashboard &middot; EU AI Act Art.14</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- 9 Invariants -->'''

NEW = '''<div class="system-item">
                    <div class="system-dot"></div>
                    <div>
                        <a href="https://windi-domain.com/enterprise/" target="_blank">W-Enterprise</a>
                        <span class="desc">AI Compliance Dashboard &middot; EU AI Act Art.14</span>
                    </div>
                </div>
                <div class="system-item">
                    <div class="system-dot"></div>
                    <div>
                        <a href="https://windi-domain.com/travel/map/berlin-pitch" target="_blank">Bayern Süd Map</a>
                        <span class="desc">Berlin Pitch &middot; Trilingual &middot; Ledger LIVE</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- 9 Invariants -->'''

with open(FILE) as f:
    content = f.read()

if "Bayern Süd Map" in content:
    print("Already patched.")
else:
    content = content.replace(OLD, NEW)
    with open(FILE, "w") as f:
        f.write(content)
    print("Patched! Bayern Süd Map added to /investor/")
