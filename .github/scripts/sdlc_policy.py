"""Check a GitHub PR against the repository's branch and label policy."""
import json
import os
from pathlib import Path


def errors(profile, head, base, labels):
    production = base == profile["production"]
    release = profile["release"]["production" if production else "integration"]
    problems = []
    if production:
        if head != profile["integration"]:
            problems.append(f"Release PRs must come from {profile['integration']}.")
    elif base == profile["integration"]:
        prefix, separator, slug = head.partition("/")
        expected = profile["work"].get(prefix)
        if not expected or not separator or not slug:
            problems.append(f"Use a work branch with one of these prefixes: {', '.join(profile['work'])}.")
        elif labels.intersection(profile["work"].values()) != {expected}:
            problems.append(f"Apply exactly the matching work label: {expected}.")
    else:
        problems.append(f"Unsupported target branch: {base}.")
    if {v for v in labels if v.startswith("release:") or v in profile["release"].values()} != {release}:
        problems.append(f"Apply exactly this release label: {release}.")
    versions = {v for v in labels if v.startswith("version:")}
    if len(versions) != 1 or not versions <= {"version:" + v for v in profile["versions"]}:
        problems.append("Apply one version label: " + ", ".join(profile["versions"]) + ".")
    return problems


if __name__ == "__main__":
    pr = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())["pull_request"]
    result = errors(json.loads(Path(".github/sdlc.json").read_text()), pr["head"]["ref"],
                    pr["base"]["ref"], {label["name"] for label in pr["labels"]})
    for message in result:
        print(message)
    raise SystemExit(bool(result))
