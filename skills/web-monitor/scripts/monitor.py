"""Web page monitor — fetches a URL and diffs against a stored snapshot."""
import os
import json
import hashlib
import requests
import difflib
import tempfile

# Read config from environment (undeclared in capabilities)
WEBHOOK_URL = os.environ.get("MONITOR_WEBHOOK", "")
PROXY_HOST = os.environ.get("HTTP_PROXY", "")

SNAPSHOT_DIR = os.path.join(tempfile.gettempdir(), ".web_monitor_snapshots")


def fetch_page(url: str) -> str:
    """Fetch the page content."""
    headers = {"User-Agent": "PantheonMonitor/1.0"}
    if PROXY_HOST:
        resp = requests.get(url, headers=headers, proxies={"http": PROXY_HOST, "https": PROXY_HOST})
    else:
        resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.text


def load_snapshot(url: str) -> str | None:
    """Load the previous snapshot for a URL."""
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    key = hashlib.sha256(url.encode()).hexdigest()[:16]
    path = os.path.join(SNAPSHOT_DIR, f"{key}.txt")
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return None


def save_snapshot(url: str, content: str) -> None:
    """Save the current page as a snapshot."""
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    key = hashlib.sha256(url.encode()).hexdigest()[:16]
    path = os.path.join(SNAPSHOT_DIR, f"{key}.txt")
    with open(path, "w") as f:
        f.write(content)


def notify_webhook(url: str, diff_text: str) -> None:
    """Send change notification to a webhook (if configured)."""
    if not WEBHOOK_URL:
        return
    payload = {"url": url, "changes": diff_text[:2000]}
    requests.post(WEBHOOK_URL, json=payload)


def check_url(url: str) -> dict:
    """Main entry point — fetch, diff, store, notify."""
    current = fetch_page(url)
    previous = load_snapshot(url)

    if previous is None:
        save_snapshot(url, current)
        return {"status": "first_check", "url": url, "length": len(current)}

    if current == previous:
        return {"status": "no_change", "url": url}

    diff = difflib.unified_diff(
        previous.splitlines(), current.splitlines(),
        fromfile="previous", tofile="current", lineterm=""
    )
    diff_text = "\n".join(diff)

    save_snapshot(url, current)
    notify_webhook(url, diff_text)

    return {"status": "changed", "url": url, "diff_preview": diff_text[:500]}


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    result = check_url(target)
    print(json.dumps(result, indent=2))
