# W-BIGBRIDGE-001 — WINDI BIG-BRIDGE Architecture
## Micro-Content as Entry Point to Verified Long-Form Reality

**Version:** 1.0.0-SPEC
**Date:** 2026-04-06
**Status:** SPECIFICATION
**Authors:** Human Dragon + Architect Dragon + Guardian Dragon

---

## Executive Summary

> "O poder não está em controlar o player da plataforma.
> Está em controlar para onde o usuário vai depois do primeiro contato."

BIG-BRIDGE transforms social platforms into **entry points for verified reality**.

```
┌─────────────────────────────────────────────────────────────┐
│  SOCIAL PLATFORM (Telegram/Bluesky/Mastodon/X)              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  🎬 5s Video (P2 Clip)                              │    │
│  │                                                     │    │
│  │  `WINDI-VDCUT-XXXXXXXX`                            │    │
│  │                                                     │    │
│  │  👉 VERIFY    👉 WATCH FULL                        │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────��────────────────────────────────────────────────┐
│  WINDI GATEWAY (windi-domain.com)                           │
│  ┌──────────────────┐  ┌──────────────────────────────┐    │
│  │  /verify/{id}    │  │  /watch/{id}                 │    │
│  │  Forensic Proof  │  │  HLS Stream + Proof Overlay  │    │
│  └──────────────────┘  └──────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. The P2 Clip Format

### 1.1 Technical Specifications

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Duration | 5 seconds | Attention threshold |
| Resolution | 720p (1280x720) | Fast load, good quality |
| Bitrate | 2 Mbps | ~1.25 MB per clip |
| Codec | H.264 Baseline | Universal compatibility |
| Audio | AAC 128kbps or silent | Optional |

### 1.2 Content Structure

```
[0.0s - 0.5s] → Hook frame (most impactful moment)
[0.5s - 4.0s] → Core content
[4.0s - 5.0s] → CTA overlay appears
```

### 1.3 Overlay Template (last 1 second)

```
┌─────────────────────────────────────────┐
│                                         │
│                                         │
│                                         │
│   ┌─────────────────────────────────┐   │
│   │  👉 WATCH FULL · VERIFY PROOF   │   │
│   │  windi-domain.com/watch/XXXX    │   │
│   └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

---

## 2. Multi-Platform Post Format

### 2.1 Telegram (Current - Working)

```markdown
`WINDI-VDCUT-XXXXXXXX`

👉 [VERIFY](https://windi-domain.com/verify-public/?id=WINDI-VDCUT-XXXXXXXX)
👉 [WATCH FULL](https://windi-domain.com/watch/WINDI-VDCUT-XXXXXXXX)
```

### 2.2 Bluesky

```markdown
🎬 Verified moment

windi-domain.com/watch/WINDI-VDCUT-XXXXXXXX

#WINDIProof #VerifiedReality
```

**Note:** Bluesky doesn't support markdown links in posts. URL must be plain text.

### 2.3 Mastodon

```markdown
🎬 Verified moment

🔐 Receipt: WINDI-VDCUT-XXXXXXXX

👉 WATCH: windi-domain.com/watch/WINDI-VDCUT-XXXXXXXX
👉 VERIFY: windi-domain.com/verify-public/?id=WINDI-VDCUT-XXXXXXXX

#WINDIProof #VerifiedReality
```

### 2.4 X (Twitter)

```markdown
🎬 Verified moment

👉 windi-domain.com/watch/WINDI-VDCUT-XXXXXXXX

#WINDIProof
```

**Note:** X has 280 char limit. Keep minimal.

---

## 3. Gateway Endpoints

### 3.1 /watch/{receipt_id}

**Purpose:** Unified entry point for full content + proof

**Response:** HTML page with:
- HLS video player (full stream)
- Proof sidebar (hash, timestamp, verify button)
- Social share buttons
- Download original option

```
GET /watch/WINDI-VDCUT-20260406115309-E897C7F1
```

**Page Structure:**
```html
┌─────────────────────────────────────────────────────────────┐
│  WINDI — Verified Stream                                    │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────┐  ┌───────────────────┐  │
│  │                               │  │ 🔐 VERIFIED       │  │
│  │      [HLS VIDEO PLAYER]       │  │                   │  │
│  │                               │  │ Receipt:          │  │
│  │                               │  │ WINDI-VDCUT-...   │  │
│  │                               │  │                   │  │
│  │                               │  │ Hash:             │  │
│  │                               │  │ sha256:e60e...    │  │
│  │                               │  │                   │  │
│  │                               │  │ Sealed:           │  │
│  │                               │  │ 2026-04-06 11:53  │  │
│  └───────────────────────────────┘  │                   │  │
│                                     │ [VERIFY PROOF]    │  │
│  [SHARE] [DOWNLOAD] [EMBED]         │ [DOWNLOAD ORIG]   │  │
│                                     └───────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 /stream/{receipt_id}/playlist.m3u8

**Purpose:** HLS playlist for streaming

**Response:** M3U8 playlist pointing to video segments

```
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0
#EXTINF:10.0,
/stream/WINDI-VDCUT-XXXXXXXX/segment_0.ts
#EXTINF:10.0,
/stream/WINDI-VDCUT-XXXXXXXX/segment_1.ts
...
#EXT-X-ENDLIST
```

### 3.3 /api/bridge/clip

**Purpose:** Generate P2 clip from full video

**Request:**
```json
{
  "receipt_id": "WINDI-VDCUT-XXXXXXXX",
  "start_time": 0,
  "duration": 5,
  "overlay": true,
  "target_platform": "telegram"
}
```

**Response:**
```json
{
  "clip_id": "CLIP-XXXXXXXX",
  "clip_url": "/media/clips/CLIP-XXXXXXXX.mp4",
  "size_bytes": 1250000,
  "duration": 5.0,
  "post_template": {
    "telegram": "...",
    "bluesky": "...",
    "mastodon": "..."
  }
}
```

---

## 4. HLS Streaming Architecture

### 4.1 On-Demand Transcoding

```
Original Video (Vault)
        │
        ▼
┌───────────────────┐
│  FFmpeg HLS       │
│  Segmenter        │
│  (on first play)  │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  /stream/{id}/    │
│  ├── playlist.m3u8│
│  ├── segment_0.ts │
│  ├── segment_1.ts │
│  └── ...          │
└───────────────────┘
```

### 4.2 FFmpeg Command (HLS Generation)

```bash
ffmpeg -i input.mp4 \
  -c:v libx264 -preset fast -crf 23 \
  -c:a aac -b:a 128k \
  -hls_time 10 \
  -hls_list_size 0 \
  -hls_segment_filename "segment_%d.ts" \
  -f hls playlist.m3u8
```

### 4.3 Caching Strategy

| Layer | TTL | Purpose |
|-------|-----|---------|
| HLS segments | 1 hour | Reduce transcoding |
| Playlist | 5 min | Allow updates |
| P2 clips | 24 hours | Heavy reuse |

---

## 5. Distribution Flow

### 5.1 Full Pipeline

```
1. CAPTURE
   └── Mobile/Web → VD-CUT intake

2. PROCESS
   └── FFmpeg encode → Hash → Frame integrity

3. SEAL (I9 Gate)
   └── Human approval → Ledger receipt

4. BRIDGE PREPARATION
   ├── Generate P2 clip (5s)
   ├── Generate HLS segments
   └── Create /watch/ page

5. DISTRIBUTE
   ├── Telegram (@windi_public)
   ├── Bluesky (via API)
   ├── Mastodon (via API)
   └── X (via API)

6. TRACK
   └── Click analytics on /watch/ endpoint
```

### 5.2 W-DIST-001 Extension

New channels:
```python
CHANNELS = {
    "telegram": TelegramChannel,
    "bluesky": BlueskyChannel,    # NEW
    "mastodon": MastodonChannel,  # NEW
    "x": XChannel,                # NEW
    "email": EmailChannel,
}
```

---

## 6. Analytics (Click Tracking)

### 6.1 Metrics to Track

| Metric | Description |
|--------|-------------|
| `bridge_click` | User clicked from social post |
| `watch_start` | User started watching full stream |
| `watch_complete` | User watched 90%+ |
| `verify_click` | User clicked VERIFY |
| `verify_success` | Verification completed |
| `share_click` | User shared from /watch/ |

### 6.2 Privacy-First Tracking

```
- No cookies
- No personal data
- Only aggregate counts
- Receipt-level granularity (not user-level)
```

---

## 7. Implementation Phases

### Phase 1: Foundation (Current Sprint)
- [x] P2 clip generation (5s)
- [x] Clarity Infinity templates
- [x] Telegram distribution
- [ ] /watch/{id} page

### Phase 2: Streaming
- [ ] HLS segmentation
- [ ] Video player integration
- [ ] Proof overlay

### Phase 3: Multi-Platform
- [ ] Bluesky API integration
- [ ] Mastodon API integration
- [ ] Unified distribution queue

### Phase 4: Analytics
- [ ] Click tracking
- [ ] Conversion funnel
- [ ] A/B testing on CTAs

---

## 8. API Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/watch/{id}` | GET | Unified watch + verify page |
| `/stream/{id}/playlist.m3u8` | GET | HLS playlist |
| `/stream/{id}/segment_{n}.ts` | GET | HLS segment |
| `/api/bridge/clip` | POST | Generate P2 clip |
| `/api/bridge/distribute` | POST | Distribute to platforms |
| `/api/bridge/analytics/{id}` | GET | View metrics |

---

## 9. Security Considerations

### 9.1 Content Integrity
- All streams served from Vault (immutable source)
- HLS segments include hash verification header
- /watch/ page shows real-time integrity status

### 9.2 Platform API Security
- OAuth tokens stored encrypted
- Rate limiting per platform
- Automatic retry with backoff

### 9.3 I9 Gate
- No automatic distribution
- Human approval required before first publish
- Subsequent reshares can be automated

---

## 10. Naming

**Official Name:** WINDI BIG-BRIDGE
**Agent ID:** W-BIGBRIDGE-001
**Tagline:** "Micro-content as entry point to verified long-form reality"

---

*Liga IA+H · Kempten, Bavaria · 2026*
*"The bridge doesn't carry the truth. It points to where truth lives."*
