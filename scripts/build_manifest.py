#!/usr/bin/env python3
"""Generate manifest.json from catalog.json + whatever content has been produced.

The catalog is the source of truth for the full intended scope. A subtopic goes
"live" the moment its reviewed content file exists with enough items; themes and
tracks derive their status from their subtopics. This lets generation run for
days while the site always reflects exactly what is ready — no manual flipping.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
MIN_LIVE_ITEMS = 12  # a subtopic needs at least this many to go live


def main():
    catalog = json.loads((CONTENT / "catalog.json").read_text())
    have = {}
    for f in (CONTENT / "subtopics").glob("*.json"):
        try:
            n = len(json.loads(f.read_text()).get("items", []))
        except Exception:
            n = 0
        have[f.stem] = n

    subtopics = []
    for s in catalog["subtopics"]:
        n = have.get(s["id"], 0)
        subtopics.append({
            "id": s["id"], "title": s["title"], "theme": s["theme"],
            "status": "live" if n >= MIN_LIVE_ITEMS else "soon", "count": n,
        })
    live_ids = {s["id"] for s in subtopics if s["status"] == "live"}

    # themes: live if any subtopic live
    theme_live = {t["id"]: False for t in catalog["themes"]}
    for s in subtopics:
        if s["status"] == "live":
            theme_live[s["theme"]] = True
    themes = [{**t, "status": "live" if theme_live[t["id"]] else "soon"} for t in catalog["themes"]]

    # tracks: status by how many subtopics are ready
    tracks = []
    for t in catalog["tracks"]:
        ready = [sid for sid in t["subtopics"] if sid in live_ids]
        status = "live" if len(ready) == len(t["subtopics"]) else "partial" if ready else "soon"
        tracks.append({**t, "status": status, "ready": len(ready), "total": len(t["subtopics"])})

    manifest = {
        "version": catalog["version"],
        "themes": themes,
        "tracks": tracks,
        "certs": catalog["certs"],
        "subtopics": [{"id": s["id"], "title": s["title"], "theme": s["theme"],
                       "track": next((t["id"] for t in catalog["tracks"] if s["id"] in t["subtopics"]), None),
                       "status": s["status"]} for s in subtopics],
    }
    (CONTENT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1))

    live_subs = len(live_ids)
    live_tracks = sum(1 for t in tracks if t["status"] == "live")
    part_tracks = sum(1 for t in tracks if t["status"] == "partial")
    total_items = sum(have.values())
    print(f"manifest: {live_subs}/{len(subtopics)} subtopics live · "
          f"{live_tracks} tracks live, {part_tracks} partial · "
          f"{sum(1 for t in themes if t['status']=='live')}/{len(themes)} themes live · "
          f"{total_items} total items")


if __name__ == "__main__":
    main()
