import json, os, time, urllib.parse, urllib.request, urllib.error

API = "https://api.github.com"

class GitHubClient:
    def __init__(self, timeout=30):
        self.timeout = timeout
        self.token = os.getenv("GITHUB_TOKEN", "").strip()

    def request(self, url):
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "sandbox-crawler/0.1"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.loads(r.read().decode("utf-8")), dict(r.headers)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:500]
            if e.code == 403 and "rate limit" in body.lower():
                reset = e.headers.get("X-RateLimit-Reset")
                raise RuntimeError(f"GitHub API rate limit reached. Reset epoch: {reset}. Set GITHUB_TOKEN for a higher limit.")
            raise RuntimeError(f"GitHub API HTTP {e.code}: {body}")

    def search_repositories(self, query, page=1, per_page=30):
        q = urllib.parse.urlencode({"q": query, "sort": "updated", "order": "desc", "page": page, "per_page": per_page})
        data, headers = self.request(f"{API}/search/repositories?{q}")
        return data.get("items", []), int(data.get("total_count", 0)), headers

    def repo_metadata(self, full_name):
        data, _ = self.request(f"{API}/repos/{full_name}")
        return data

    def download_tarball(self, full_name, branch, destination):
        url = f"https://api.github.com/repos/{full_name}/tarball/{urllib.parse.quote(branch, safe='')}"
        headers = {"User-Agent": "sandbox-crawler/0.1", "Accept": "application/vnd.github+json"}
        if self.token: headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=self.timeout) as r, open(destination, "wb") as f:
            total = 0
            while True:
                chunk = r.read(1024 * 128)
                if not chunk: break
                total += len(chunk)
                if total > 35 * 1024 * 1024:
                    raise RuntimeError("Archive exceeds hard 35 MB safety limit")
                f.write(chunk)
        return total
