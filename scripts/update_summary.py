import re
from pathlib import Path

START, END = "<!-- TRADES:START -->", "<!-- TRADES:END -->"
TRADE_RE = re.compile(r"^\|\s*Direction\s*\|\s*(Long|Short)\s*\|", re.I | re.M)
RESULT_RE = re.compile(r"^###\s*(\S+)\s*Trade Result", re.M)
KEYS = ("trades", "win", "loss", "be")


def natural_key(path: Path):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", path.name)]


def analyse(readme: Path):
    text = readme.read_text(encoding="utf-8")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)  # ignore commented-out parts
    icons = RESULT_RE.findall(text)
    return {
        "trades": len(TRADE_RE.findall(text)),
        "win": sum(i.startswith("✅") for i in icons),
        "loss": sum(i.startswith("❌") for i in icons),
        "be": sum(i.startswith("➖") for i in icons),
    }


def analyse_folder(folder: Path) -> tuple[dict[str, int], bool]:
    total: dict[str, int] = {k: 0 for k in KEYS}
    found = False
    for readme in folder.rglob("README.md"):
        found = True
        for k, v in analyse(readme).items():
            total[k] += v
    return total, found


def build_summary(parent: Path, label: str) -> str:
    rows, grand = [], dict.fromkeys(KEYS, 0)
    for child in sorted((d for d in parent.iterdir() if d.is_dir()), key=natural_key):
        s, found = analyse_folder(child)
        if not found:  # skips charts/ and other non-journal folders
            continue
        for k in KEYS:
            grand[k] += s[k]
        link = f"[{child.name}](./{child.name}/README.md)"
        rows.append(f"| {link} | {s['trades']} | {s['win']} | {s['loss']} | {s['be']} |")

    closed = grand["win"] + grand["loss"]
    win_rate = f"{grand['win'] / closed * 100:.0f}%" if closed else "-"
    return "\n".join([
        f"| {label} | Trades | ✅ Win | ❌ Loss | ➖ BE |",
        "|---|---|---|---|---|",
        *rows,
        f"| **Total** | **{grand['trades']}** | **{grand['win']}** | **{grand['loss']}** | **{grand['be']}** |",
        "",
        f"**Win rate (excl. BE):** {win_rate}",
    ])


def main():
    for readme in Path(".").rglob("README.md"):
        text = readme.read_text(encoding="utf-8")
        if START not in text or END not in text:
            continue

        # a README whose subfolders are week folders is a monthly one
        has_weeks = any(
            d.is_dir() and d.name.lower().startswith("week")
            for d in readme.parent.iterdir()
        )
        label = "Week" if has_weeks else "Day"

        summary = build_summary(readme.parent, label)
        new = re.sub(
            re.escape(START) + r".*?" + re.escape(END),
            lambda _: f"{START}\n{summary}\n{END}",
            text,
            flags=re.S,
        )
        if new != text:
            readme.write_text(new, encoding="utf-8")
            print(f"Updated {readme}")


if __name__ == "__main__":
    main()