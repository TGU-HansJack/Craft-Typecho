#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests


_GITHUB_API = "https://api.github.com"
_RAW_BASE = "https://raw.githubusercontent.com"


@dataclass
class GithubRepo:
    owner: str
    repo: str
    html_url: str
    description: str
    default_branch: str
    homepage: str


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": "Craft-Typecho-Crawler",
            "Accept": "application/vnd.github+json",
        }
    )
    token = (
        os.getenv("GITHUB_TOKEN")
        or os.getenv("GH_TOKEN")
        or os.getenv("GITHUB_PAT")
        or os.getenv("GITHUB_API_TOKEN")
    )
    if token:
        s.headers["Authorization"] = f"Bearer {token.strip()}"
    return s


def _gh_get_json(s: requests.Session, path: str, params: Optional[dict] = None) -> Any:
    url = path if path.startswith("http") else f"{_GITHUB_API}{path}"
    r = s.get(url, params=params, timeout=25)
    if r.status_code == 403 and "rate limit" in r.text.lower():
        raise RuntimeError(
            "GitHub API rate limit exceeded. Set env GITHUB_TOKEN to increase limits."
        )
    r.raise_for_status()
    return r.json()


def _raw_get_text(s: requests.Session, owner: str, repo: str, branch: str, path: str) -> Optional[str]:
    url = f"{_RAW_BASE}/{owner}/{repo}/{branch}/{path.lstrip('/')}"
    r = s.get(url, timeout=25)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    r.encoding = r.encoding or "utf-8"
    return r.text


def _slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s


_DIR_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


def _is_valid_dir(s: str) -> bool:
    return bool(s and _DIR_RE.match(s))


def _derive_display_name(repo_name: str, kind: str) -> str:
    name = repo_name.strip()
    if kind == "plugin":
        name = re.sub(r"(?i)^typecho[-_]?plugin[-_]+", "", name)
    elif kind == "theme":
        name = re.sub(r"(?i)^typecho[-_]?theme[-_]+", "", name)
    name = name.strip()
    return name or repo_name


def _first_docblock(text: str) -> str:
    head = text[:8000]
    start = head.find("/**")
    if start == -1:
        return ""
    end = head.find("*/", start)
    if end == -1:
        return ""
    return head[start : end + 2]


def _docblock_lines(doc: str) -> List[str]:
    out: List[str] = []
    for raw in doc.splitlines():
        line = raw.strip()
        if line.startswith("/**"):
            line = line[3:]
        if line.endswith("*/"):
            line = line[:-2]
        line = line.lstrip("*").strip()
        out.append(line)
    return out


def _pick_first_nonempty(lines: Iterable[str]) -> str:
    for line in lines:
        if not line:
            continue
        if line.startswith("@"):
            continue
        return line.strip()
    return ""


def _parse_docblock(doc: str) -> Dict[str, str]:
    lines = _docblock_lines(doc)
    meta: Dict[str, str] = {
        "package": "",
        "author": "",
        "version": "",
        "link": "",
        "description": _pick_first_nonempty(lines),
    }
    for line in lines:
        m = re.match(r"@package\s+(.+)", line, re.I)
        if m and not meta["package"]:
            meta["package"] = m.group(1).strip()
            continue
        m = re.match(r"@author\s+(.+)", line, re.I)
        if m and not meta["author"]:
            meta["author"] = m.group(1).strip()
            continue
        m = re.match(r"@version\s+(.+)", line, re.I)
        if m and not meta["version"]:
            meta["version"] = m.group(1).strip()
            continue
        m = re.match(r"@link\s+(.+)", line, re.I)
        if m and not meta["link"]:
            meta["link"] = m.group(1).strip()
            continue
    return meta


def _extract_class_prefix(text: str) -> str:
    head = text[:16000]
    m = re.search(r"\bclass\s+([A-Za-z0-9_]+)_Plugin\b", head)
    return (m.group(1) if m else "").strip()


def _clean_version(v: str) -> str:
    v = v.strip()
    if not v:
        return ""
    m = re.search(r"(\d+\.\d+(?:\.\d+)?)", v)
    if m:
        return m.group(1)
    v = v.lstrip("vV").replace("_", ".")
    v = re.sub(r"[^0-9A-Za-z.+-]", "", v)
    return v


def _build_dir(kind: str, repo_name: str, meta: Dict[str, str], class_prefix: str) -> str:
    package = (meta.get("package") or "").strip()
    if _is_valid_dir(package):
        return package
    if _is_valid_dir(class_prefix):
        return class_prefix
    derived = _derive_display_name(repo_name, kind)
    if _is_valid_dir(derived):
        return derived
    # best-effort sanitize
    sanitized = re.sub(r"[^A-Za-z0-9_-]+", "-", derived).strip("-")
    if _is_valid_dir(sanitized):
        return sanitized
    sanitized = re.sub(r"[^A-Za-z0-9_-]+", "-", repo_name).strip("-")
    return sanitized if _is_valid_dir(sanitized) else ""


def _search_repos(s: requests.Session, q: str, per_page: int, pages: int) -> List[GithubRepo]:
    repos: List[GithubRepo] = []
    for page in range(1, pages + 1):
        data = _gh_get_json(
            s,
            "/search/repositories",
            params={
                "q": q,
                "sort": "stars",
                "order": "desc",
                "per_page": per_page,
                "page": page,
            },
        )
        items = data.get("items") or []
        for it in items:
            owner = ((it.get("owner") or {}).get("login") or "").strip()
            name = (it.get("name") or "").strip()
            if not owner or not name:
                continue
            repos.append(
                GithubRepo(
                    owner=owner,
                    repo=name,
                    html_url=(it.get("html_url") or "").strip(),
                    description=(it.get("description") or "").strip(),
                    default_branch=(it.get("default_branch") or "main").strip() or "main",
                    homepage=(it.get("homepage") or "").strip(),
                )
            )
    return repos


def _make_project(kind: str, gr: GithubRepo, file_text: str) -> Dict[str, Any]:
    doc = _first_docblock(file_text)
    meta = _parse_docblock(doc) if doc else {"package": "", "author": "", "version": "", "link": "", "description": ""}
    class_prefix = _extract_class_prefix(file_text) if kind == "plugin" else ""
    install_dir = _build_dir(kind, gr.repo, meta, class_prefix)

    display_name = _derive_display_name(gr.repo, kind)
    if meta.get("package") and len(display_name) > 40:
        display_name = meta["package"]

    donate = ""
    link = (meta.get("link") or "").strip()
    if link and not link.lower().startswith("https://github.com/"):
        donate = link
    if not donate and gr.homepage and gr.homepage.lower().startswith(("http://", "https://")):
        donate = gr.homepage

    version = _clean_version(meta.get("version") or "")

    author = (meta.get("author") or "").strip()
    if not author:
        author = gr.owner

    description = gr.description or (meta.get("description") or "")

    project_id = f"{kind}-{_slugify(install_dir or gr.repo) or _slugify(gr.owner + '-' + gr.repo)}"

    return {
        "id": project_id,
        "name": display_name,
        "type": kind,
        "link": gr.html_url or f"https://github.com/{gr.owner}/{gr.repo}",
        "isGithub": True,
        "direct": True,
        "version": version,
        "typecho": "",
        "author": author,
        "donate": donate,
        "description": description,
        "dir": install_dir or gr.repo,
    }


def _load_repo_json(path: str) -> Dict[str, Any]:
    if not os.path.isfile(path):
        return {"updatedAt": "", "projects": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_repo_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _merge_projects(existing: List[Dict[str, Any]], incoming: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_link: Dict[str, Dict[str, Any]] = {}
    for it in existing:
        if isinstance(it, dict) and it.get("link"):
            by_link[str(it["link"]).strip()] = it

    used_ids = {str(it.get("id")) for it in existing if isinstance(it, dict) and it.get("id")}

    def unique_id(base: str) -> str:
        if base not in used_ids:
            used_ids.add(base)
            return base
        i = 2
        while f"{base}-{i}" in used_ids:
            i += 1
        v = f"{base}-{i}"
        used_ids.add(v)
        return v

    out: List[Dict[str, Any]] = list(existing)
    for inc in incoming:
        link = str(inc.get("link") or "").strip()
        if not link:
            continue
        if link in by_link:
            cur = by_link[link]
            # Only fill blanks, but always fix install dir if we detected one.
            if inc.get("dir") and (not cur.get("dir") or cur.get("dir") == (cur.get("link", "").split("/")[-1] if isinstance(cur.get("link"), str) else "")):
                cur["dir"] = inc["dir"]
            elif inc.get("dir") and cur.get("dir") != inc.get("dir") and _is_valid_dir(str(inc.get("dir"))):
                cur["dir"] = inc["dir"]
            for k in ["version", "typecho", "author", "donate", "description", "name", "type"]:
                if (not cur.get(k)) and inc.get(k):
                    cur[k] = inc[k]
            if "isGithub" not in cur:
                cur["isGithub"] = True
            if "direct" not in cur:
                cur["direct"] = True
            continue

        inc2 = dict(inc)
        inc2["id"] = unique_id(str(inc2.get("id") or ""))
        out.append(inc2)
        by_link[link] = inc2
    return out


def main(argv: List[str]) -> int:
    p = argparse.ArgumentParser(description="Crawl Typecho plugins/themes from GitHub and update repo.json")
    p.add_argument("--repo-json", default=os.path.join(os.path.dirname(os.path.dirname(__file__)), "repo.json"))
    p.add_argument("--plugins", type=int, default=25, help="Max plugin projects to add/update")
    p.add_argument("--themes", type=int, default=25, help="Max theme projects to add/update")
    p.add_argument("--per-page", type=int, default=50)
    p.add_argument("--pages", type=int, default=2)
    args = p.parse_args(argv)

    repo_json_path = os.path.abspath(args.repo_json)
    data = _load_repo_json(repo_json_path)
    projects = data.get("projects")
    if not isinstance(projects, list):
        projects = []

    s = _session()

    plugin_repos = _search_repos(
        s,
        "topic:typecho plugin fork:false archived:false",
        per_page=max(1, min(100, args.per_page)),
        pages=max(1, args.pages),
    )
    theme_repos = _search_repos(
        s,
        "topic:typecho theme fork:false archived:false",
        per_page=max(1, min(100, args.per_page)),
        pages=max(1, args.pages),
    )

    discovered: List[Dict[str, Any]] = []

    def collect(kind: str, repos: List[GithubRepo], limit: int) -> None:
        added = 0
        for gr in repos:
            if added >= limit:
                break
            path = "Plugin.php" if kind == "plugin" else "index.php"
            text = _raw_get_text(s, gr.owner, gr.repo, gr.default_branch, path)
            if text is None:
                continue
            try:
                proj = _make_project(kind, gr, text)
            except Exception:
                continue
            if not _is_valid_dir(str(proj.get("dir") or "")):
                continue
            discovered.append(proj)
            added += 1

    collect("plugin", plugin_repos, max(0, args.plugins))
    collect("theme", theme_repos, max(0, args.themes))

    merged = _merge_projects(projects, discovered)

    today = _dt.date.today().isoformat()
    data_out = dict(data)
    data_out["updatedAt"] = today
    data_out["projects"] = merged
    _write_repo_json(repo_json_path, data_out)

    print(f"Updated: {repo_json_path}")
    print(f"Discovered: {len(discovered)}")
    print(f"Total projects: {len(merged)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

