#!/usr/bin/env python3
"""Validate the generated academic site using only the Python standard library."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse
from xml.etree import ElementTree


SITE_URL = "https://fy-yuan.github.io"
CORE_PAGES = ("index.html", "publications/index.html", "teaching/index.html")
REQUIRED_PATHS = CORE_PAGES + (
    "404.html",
    "about/index.html",
    "about.html",
    "awards/index.html",
    "cv/index.html",
    "resume/index.html",
    "talks/index.html",
    "assets/CV.pdf",
    "images/favicon.ico",
    "images/og-card.png",
    "images/fengyi-yuan-portrait-320.jpg",
    "images/fengyi-yuan-portrait-640.jpg",
)
FORBIDDEN_TEXT = (
    "Future Blog Post",
    "GitHub University",
    "Paper Title Number",
    "Portfolio item number",
    "Talk 1 on Relevant Topic",
    "Teaching experience 1",
    "43 different slack teams",
)
EXPECTED_SITEMAP_URLS = {
    f"{SITE_URL}/",
    f"{SITE_URL}/publications/",
    f"{SITE_URL}/teaching/",
}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.h1_count = 0
        self.ids: set[str] = set()
        self.id_counts: Counter[str] = Counter()
        self.links: list[tuple[str, str]] = []
        self.images: list[dict[str, str | None]] = []
        self.scripts: list[str] = []
        self.html_lang: str | None = None
        self.main_count = 0
        self.main_ids: set[str] = set()
        self.description: str | None = None
        self.canonical: str | None = None
        self.og_image: str | None = None
        self.robots: str | None = None
        self.refresh_target: str | None = None
        self.json_ld: list[str] = []
        self._capture_json_ld = False
        self._json_buffer: list[str] = []
        self._section_stack: list[str | None] = []
        self._list_stack: list[set[str]] = []
        self.section_item_counts: Counter[str] = Counter()
        self.list_item_counts: Counter[str] = Counter()

    def handle_starttag(self, tag: str, attrs_list: list[tuple[str, str | None]]) -> None:
        attrs = dict(attrs_list)
        element_id = attrs.get("id")
        if element_id:
            self.ids.add(element_id)
            self.id_counts[element_id] += 1
        if tag == "html":
            self.html_lang = attrs.get("lang")
        if tag == "main":
            self.main_count += 1
            if element_id:
                self.main_ids.add(element_id)
        if tag == "h1":
            self.h1_count += 1
        if tag == "section":
            self._section_stack.append(attrs.get("aria-labelledby") or element_id)
        if tag in {"ul", "ol"}:
            self._list_stack.append(set((attrs.get("class") or "").split()))
        if tag == "li":
            classes = set((attrs.get("class") or "").split())
            if "publication-item" in classes and self._section_stack and self._section_stack[-1]:
                self.section_item_counts[self._section_stack[-1]] += 1
            for context in self._list_stack:
                for name in {"presentation-list", "course-list", "honors-list"} & context:
                    self.list_item_counts[name] += 1
        if tag == "a" and attrs.get("href"):
            self.links.append(("href", attrs["href"] or ""))
        if tag == "link" and attrs.get("href"):
            self.links.append(("href", attrs["href"] or ""))
            if "canonical" in (attrs.get("rel") or "").split():
                self.canonical = attrs.get("href")
        if tag == "img":
            src = attrs.get("src") or ""
            self.images.append(
                {
                    "src": src,
                    "alt": attrs.get("alt"),
                    "width": attrs.get("width"),
                    "height": attrs.get("height"),
                    "srcset": attrs.get("srcset"),
                    "sizes": attrs.get("sizes"),
                }
            )
            if src:
                self.links.append(("src", src))
            for candidate in (attrs.get("srcset") or "").split(","):
                candidate_url = candidate.strip().split(" ", 1)[0]
                if candidate_url:
                    self.links.append(("srcset", candidate_url))
        if tag == "script":
            if attrs.get("src"):
                self.scripts.append(attrs["src"] or "")
                self.links.append(("src", attrs["src"] or ""))
            if attrs.get("type") == "application/ld+json":
                self._capture_json_ld = True
                self._json_buffer = []
        if tag == "meta":
            name = (attrs.get("name") or "").lower()
            prop = (attrs.get("property") or "").lower()
            if name == "description":
                self.description = attrs.get("content")
            elif name == "robots":
                self.robots = attrs.get("content")
            if prop == "og:image":
                self.og_image = attrs.get("content")
            if (attrs.get("http-equiv") or "").lower() == "refresh":
                match = re.search(r"url=(.+)$", attrs.get("content") or "", re.I)
                if match:
                    self.refresh_target = match.group(1).strip()

    def handle_endtag(self, tag: str) -> None:
        if tag == "section" and self._section_stack:
            self._section_stack.pop()
        if tag in {"ul", "ol"} and self._list_stack:
            self._list_stack.pop()
        if tag == "script" and self._capture_json_ld:
            self.json_ld.append("".join(self._json_buffer).strip())
            self._capture_json_ld = False
            self._json_buffer = []

    def handle_data(self, data: str) -> None:
        if self._capture_json_ld:
            self._json_buffer.append(data)


def parse_page(path: Path) -> PageParser:
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def target_file(site_dir: Path, source: Path, raw_url: str) -> tuple[Path | None, str]:
    parsed = urlparse(raw_url)
    if parsed.scheme in {"http", "https", "mailto", "tel", "data"} or parsed.netloc:
        return None, parsed.fragment
    path = unquote(parsed.path)
    if not path:
        target = source
    elif path.startswith("/"):
        target = site_dir / path.lstrip("/")
    else:
        target = source.parent / path
    if path.endswith("/") or target.is_dir():
        target = target / "index.html"
    return target.resolve(), parsed.fragment


def validate_assets(site_dir: Path, errors: list[str]) -> None:
    manifest_path = Path(__file__).with_name("asset_manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for relative, expected in manifest.items():
        path = site_dir / relative
        if not path.is_file():
            errors.append(f"Missing preserved asset: {relative}")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != expected["sha256"] or path.stat().st_size != expected["size"]:
            errors.append(f"Preserved asset changed: {relative}")


def main() -> int:
    site_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "_site").resolve()
    errors: list[str] = []
    for relative in REQUIRED_PATHS:
        if not (site_dir / relative).is_file():
            errors.append(f"Missing required output: {relative}")

    html_paths = sorted(site_dir.rglob("*.html"))
    pages = {path.resolve(): parse_page(path) for path in html_paths}
    for path, page in pages.items():
        relative = path.relative_to(site_dir)
        duplicates = sorted(element_id for element_id, count in page.id_counts.items() if count > 1)
        if duplicates:
            errors.append(f"{relative} has duplicate IDs: {duplicates}")
        if page.scripts:
            errors.append(f"{relative} loads runtime scripts: {page.scripts}")
        for image in page.images:
            if image["alt"] is None:
                errors.append(f"{relative} image lacks alt text: {image['src']}")
            if not image["width"] or not image["height"]:
                errors.append(f"{relative} image lacks intrinsic dimensions: {image['src']}")

    for relative in CORE_PAGES:
        path = (site_dir / relative).resolve()
        page = pages.get(path)
        if not page:
            continue
        if page.h1_count != 1:
            errors.append(f"{relative} has {page.h1_count} h1 elements; expected 1")
        if not page.description or not page.description.strip():
            errors.append(f"{relative} lacks a meta description")
        if not page.canonical:
            errors.append(f"{relative} lacks a canonical URL")
        if page.html_lang != "en":
            errors.append(f"{relative} has unexpected HTML language: {page.html_lang!r}")
        if page.main_count != 1 or "main-content" not in page.main_ids:
            errors.append(f"{relative} lacks one identifiable main landmark")

    home = pages.get((site_dir / "index.html").resolve())
    if home:
        if not home.json_ld:
            errors.append("Homepage lacks JSON-LD")
        else:
            try:
                data = json.loads(home.json_ld[0])
                if data.get("@type") != "ProfilePage" or data.get("mainEntity", {}).get("@type") != "Person":
                    errors.append("Homepage JSON-LD is not ProfilePage/Person")
            except json.JSONDecodeError as exc:
                errors.append(f"Homepage JSON-LD is invalid: {exc}")
        if home.list_item_counts["honors-list"] != 6:
            errors.append(f"Homepage has {home.list_item_counts['honors-list']} honors; expected 6")
        if not home.og_image:
            errors.append("Homepage lacks og:image")
        if not any(image["srcset"] and image["sizes"] for image in home.images):
            errors.append("Homepage lacks a responsive image source declaration")

    research = pages.get((site_dir / "publications/index.html").resolve())
    if research:
        if research.section_item_counts["preprints"] != 5:
            errors.append(f"Research page has {research.section_item_counts['preprints']} preprints; expected 5")
        if research.section_item_counts["journal-publications"] != 8:
            errors.append(f"Research page has {research.section_item_counts['journal-publications']} journal publications; expected 8")
        if research.list_item_counts["presentation-list"] != 11:
            errors.append(f"Research page has {research.list_item_counts['presentation-list']} presentations; expected 11")

    teaching = pages.get((site_dir / "teaching/index.html").resolve())
    if teaching and teaching.list_item_counts["course-list"] != 10:
        errors.append(f"Teaching page has {teaching.list_item_counts['course-list']} courses; expected 10")

    for source, page in pages.items():
        for kind, raw_url in page.links:
            target, fragment = target_file(site_dir, source, raw_url)
            if target is None:
                continue
            try:
                target.relative_to(site_dir)
            except ValueError:
                errors.append(f"{source.relative_to(site_dir)} {kind} escapes site root: {raw_url}")
                continue
            if not target.is_file():
                errors.append(f"{source.relative_to(site_dir)} has missing {kind}: {raw_url}")
                continue
            if fragment and target.suffix == ".html":
                target_page = pages.get(target)
                if target_page and fragment not in target_page.ids:
                    errors.append(f"{source.relative_to(site_dir)} has missing fragment: {raw_url}")

    redirect_expectations = {
        "awards/index.html": "/#honors",
        "talks/index.html": "/publications/#presentations",
        "cv/index.html": "/assets/CV.pdf",
        "resume/index.html": "/assets/CV.pdf",
    }
    for relative, expected in redirect_expectations.items():
        page = pages.get((site_dir / relative).resolve())
        if page and (page.refresh_target != expected or "noindex" not in (page.robots or "")):
            errors.append(f"Incorrect redirect page: {relative}")

    combined_html = "\n".join(path.read_text(encoding="utf-8") for path in html_paths)
    for text in FORBIDDEN_TEXT:
        if text in combined_html:
            errors.append(f"Template sample text remains in output: {text}")

    sitemap_path = site_dir / "sitemap.xml"
    if not sitemap_path.is_file():
        errors.append("Missing sitemap.xml")
    else:
        root = ElementTree.parse(sitemap_path).getroot()
        namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = {node.text.rstrip("/") + "/" if node.text == SITE_URL else node.text for node in root.findall("sm:url/sm:loc", namespace)}
        if urls != EXPECTED_SITEMAP_URLS:
            errors.append(f"Unexpected sitemap URLs: {sorted(urls)}")

    validate_assets(site_dir, errors)
    if errors:
        print("Site validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Validated {len(html_paths)} HTML files and all preserved assets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
