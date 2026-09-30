#!/usr/bin/env python3
"""Move large hash lists out of their page's iframe URL.

A hash list page used to carry the whole list in its iframe's #fragment.
Chrome refuses a URL over 2 MB and shows a white page, and even under that
limit a large URL costs seconds before the list appears (measured 2026-09-30
in Chrome: +0.4 s at 500 KB, +3.7 s at 1 MB, +8 s at 2 MB).

For each root `<id>.html` over --min-bytes whose iframe points at
https://debridmediamanager.com/hashlist#<list>, this moves the page unchanged
to `lists/<id>.txt` (a rename, so git stores no second copy) and writes a new
`<id>.html` whose iframe points at hashlist#id=<id>. DMM's hashlist page reads
the list back out of the moved page. Links keep their address.

Pages it does not recognise are left alone and reported. Already-moved lists
are skipped, so it can be rerun. Stages the changes; commit them yourself.

    ./move-large-lists.py [--min-bytes N] [--only ID[,ID...]] [--dry-run]
"""

import argparse
import os
import re
import subprocess
import sys

APP = "https://debridmediamanager.com/hashlist"
HEAD = (
    "<!doctype html>\n<html>\n<head>\n<meta charset=UTF-8>\n"
    "<title>Debrid Media Manager Hash List</title>\n"
    "<style>iframe{border:none;position:absolute;top:0;left:0;width:100%;height:100%}</style>\n"
    '</head>\n<body>\n<iframe src="'
)
TAIL = '"></iframe>\n</body>\n</html>'
PAGE = re.compile(
    re.escape(HEAD) + re.escape(APP) + r"#[A-Za-z0-9+\-$]+" + re.escape(TAIL) + r"\Z"
)
ID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z")


def page(src):
    return HEAD + src + TAIL


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-bytes", type=int, default=512 * 1024)
    parser.add_argument("--only", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    only = set(filter(None, args.only.split(",")))

    moved, skipped = [], []
    for name in sorted(os.listdir(".")):
        if not name.endswith(".html") or not ID.match(name[:-5]):
            continue
        list_id = name[:-5]
        if only and list_id not in only:
            continue
        if os.path.getsize(name) <= args.min_bytes:
            continue
        target = os.path.join("lists", f"{list_id}.txt")
        if os.path.exists(target):
            skipped.append((name, "already moved"))
            continue
        with open(name, encoding="utf-8") as f:
            text = f.read()
        if not PAGE.match(text):
            skipped.append((name, "not a debridmediamanager.com hash list page"))
            continue
        moved.append(list_id)
        if args.dry_run:
            continue
        os.makedirs("lists", exist_ok=True)
        subprocess.run(["git", "mv", name, target], check=True)
        with open(name, "w", encoding="utf-8") as f:
            f.write(page(f"{APP}#id={list_id}"))
        subprocess.run(["git", "add", name], check=True)

    for name, why in skipped:
        print(f"skip {name}: {why}", file=sys.stderr)
    print(f"{'would move' if args.dry_run else 'moved'} {len(moved)}, skipped {len(skipped)}")


if __name__ == "__main__":
    main()
