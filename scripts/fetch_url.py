#!/usr/bin/env python3
"""The only sanctioned way this vault reaches the network.

Ingesting third-party content means an agent chooses URLs based on text it did not
write. That is a server-side request forgery primitive: a note saying "see
http://169.254.169.254/latest/meta-data/" is asking the agent to read cloud
credentials and file them in a note. Routing every fetch through one audited script
turns that into a refusal.

What it refuses:
  - any scheme that is not http/https
  - loopback, private, link-local, multicast, reserved and CGNAT addresses
  - the cloud metadata address, explicitly, in every form
  - hosts outside the allowlist when `allowlist_only` is set in config
  - **every redirect hop**, re-checked before it is followed — a public URL that
    302s to 169.254.169.254 is the standard way naive SSRF checks are defeated

What it does not defend against: DNS rebinding between the check and the connect.
Closing that needs connection-level IP pinning, which urllib does not expose
cleanly. The compensating control is that a rebind still lands in a git-tracked
note, and the write guard means nothing worse than that.

Usage:
    python3 scripts/fetch_url.py <url> [--text] [--timeout 30]

Exit codes (stable; pipelines branch on them):
    0  ok            2  refused: dangerous host or scheme
    3  refused: not in allowlist        4  network error
    5  timeout                          6  empty or unparseable response
    7  blocked by the site (bot wall, 401/403/429) — fall back to a manual paste
"""
from __future__ import annotations

import argparse
import html
import ipaddress
import re
import socket
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, urlunparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lifeos_config import ConfigError, load

OK, E_DANGEROUS, E_ALLOWLIST, E_NETWORK, E_TIMEOUT, E_EMPTY, E_BLOCKED = 0, 2, 3, 4, 5, 6, 7

# Ranges Python's own is_private/is_reserved do not reliably flag across versions.
# CGNAT is the important one: Tailscale tailnets live in 100.64.0.0/10, so a host
# resolving there is very often a private machine on the operator's own network.
EXTRA_BLOCKED = (
    ipaddress.ip_network("100.64.0.0/10"),    # CGNAT / shared address space
    ipaddress.ip_network("192.0.0.0/24"),     # IETF protocol assignments
    ipaddress.ip_network("192.0.2.0/24"),     # TEST-NET-1
    ipaddress.ip_network("198.51.100.0/24"),  # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),   # TEST-NET-3
)
# Some corporate networks and VPNs resolve public names into this range via a
# transparent proxy. Blocked unless the operator opts in (config: allow_benchmark_range).
BENCHMARK_RANGE = ipaddress.ip_network("198.18.0.0/15")
METADATA_ADDRESSES = {"169.254.169.254", "fd00:ec2::254", "100.100.100.200"}

MAX_REDIRECTS = 5
MAX_BYTES = 8 * 1024 * 1024
USER_AGENT = "Mozilla/5.0 (compatible; LifeOS/1.0; +https://github.com/lifeos)"


class Refused(Exception):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code


# ------------------------------------------------------------------ host checks

def _normalize(ip):
    """Unwrap IPv4-mapped IPv6 (`::ffff:10.0.0.1`) to the IPv4 address it means.

    Without this, every IPv4 range test below silently fails on the mapped form —
    `ip in IPv4Network` is False for an IPv6Address regardless of what it wraps.
    getaddrinfo hands back mapped addresses routinely on dual-stack hosts, so this
    is the normal path, not an edge case.
    """
    mapped = getattr(ip, "ipv4_mapped", None)
    return mapped if mapped is not None else ip


def _address_is_public(ip, allow_benchmark: bool) -> bool:
    ip = _normalize(ip)
    if str(ip) in METADATA_ADDRESSES:
        return False
    if ip.version == 4 and ip in BENCHMARK_RANGE:
        return allow_benchmark
    if ip.version == 4 and any(ip in net for net in EXTRA_BLOCKED):
        return False
    return not (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_multicast or ip.is_reserved or ip.is_unspecified)


def check_host(host: str, allow_benchmark: bool) -> None:
    """Raise Refused unless every address this host resolves to is public."""
    if not host:
        raise Refused(E_DANGEROUS, "no host in URL")
    host = host.strip("[]").rstrip(".")
    if host.lower() in ("localhost", "localhost.localdomain") or host.lower().endswith(".localhost"):
        raise Refused(E_DANGEROUS, f"refusing loopback host: {host}")

    # A literal IP never gets the benchmark-range exception: that exception exists
    # for *names* a proxy rewrites, not for someone typing the address directly.
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None:
        if not _address_is_public(literal, allow_benchmark=False):
            raise Refused(E_DANGEROUS, f"refusing non-public address: {host}")
        return

    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as e:
        raise Refused(E_NETWORK, f"cannot resolve {host}: {e}") from None
    if not infos:
        raise Refused(E_NETWORK, f"cannot resolve {host}")

    for info in infos:
        addr = info[4][0].split("%")[0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            continue
        if not _address_is_public(ip, allow_benchmark):
            normalized = _normalize(ip)
            hint = ""
            if normalized.version == 4 and normalized in BENCHMARK_RANGE:
                hint = ("\n  This looks like a transparent proxy. If that is your network, set "
                        "allow_benchmark_range = true in config/lifeos.toml.")
            raise Refused(E_DANGEROUS,
                          f"refusing {host}: resolves to non-public address {ip}{hint}")


def check_allowlist(host: str, allowlist: list[str]) -> None:
    host = host.lower().rstrip(".")
    for entry in allowlist:
        entry = entry.lower().lstrip("*.")
        if host == entry or host.endswith("." + entry):
            return
    raise Refused(E_ALLOWLIST, f"{host} is not in [security].publisher_allowlist")


def validate_url(url: str, cfg) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise Refused(E_DANGEROUS,
                      f"refusing scheme {parsed.scheme!r}: only http and https are fetched")
    if not parsed.hostname:
        raise Refused(E_DANGEROUS, f"no host in {url!r}")
    check_host(parsed.hostname, cfg.allow_benchmark_range)
    if cfg.allowlist_only:
        check_allowlist(parsed.hostname, cfg.publisher_allowlist)
    return urlunparse(parsed)


# ------------------------------------------------------------------ fetch

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Stop urllib following redirects so each hop can be revalidated first."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch(url: str, cfg, timeout: int = 30) -> tuple[str, str]:
    """Return (final_url, body). Every hop is validated before it is followed."""
    opener = urllib.request.build_opener(_NoRedirect)
    current = validate_url(url, cfg)

    for _ in range(MAX_REDIRECTS + 1):
        request = urllib.request.Request(
            current, headers={"User-Agent": USER_AGENT,
                              "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9"})
        try:
            with opener.open(request, timeout=timeout) as response:
                raw = response.read(MAX_BYTES)
                charset = response.headers.get_content_charset() or "utf-8"
                return current, raw.decode(charset, errors="replace")
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308):
                location = e.headers.get("Location")
                if not location:
                    raise Refused(E_NETWORK, f"{e.code} with no Location header") from None
                # THE important line: the redirect target is untrusted input and gets
                # the same treatment as the original URL.
                current = validate_url(urllib.parse.urljoin(current, location), cfg)
                continue
            if e.code in (401, 403, 405, 429) or e.code == 503:
                raise Refused(E_BLOCKED,
                              f"{e.code} {e.reason} — the site is refusing automated access; "
                              "open it in a browser and paste the text") from None
            raise Refused(E_NETWORK, f"HTTP {e.code} {e.reason}") from None
        except socket.timeout:
            raise Refused(E_TIMEOUT, f"timed out after {timeout}s") from None
        except urllib.error.URLError as e:
            raise Refused(E_NETWORK, f"network error: {e.reason}") from None

    raise Refused(E_NETWORK, f"more than {MAX_REDIRECTS} redirects")


# ------------------------------------------------------------------ extraction

class _TextExtractor(HTMLParser):
    """Good-enough HTML to text, stdlib only.

    A dedicated extractor (trafilatura, defuddle) does this better. This exists so
    the framework has zero required dependencies; docs/ingestion.md says how to
    plug a better one in.
    """

    SKIP = {"script", "style", "noscript", "svg", "head", "nav", "footer", "form"}
    BLOCK = {"p", "div", "br", "li", "tr", "section", "article",
             "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip_depth = 0
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip_depth += 1
        elif tag == "title":
            self._in_title = True
        elif tag in self.BLOCK:
            self.parts.append("\n")
        if tag in ("h1", "h2", "h3"):
            self.parts.append("\n" + "#" * int(tag[1]) + " ")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip_depth:
            self._skip_depth -= 1
        elif tag == "title":
            self._in_title = False
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif not self._skip_depth:
            self.parts.append(data)

    def text(self) -> str:
        joined = "".join(self.parts)
        joined = re.sub(r"[ \t\r\f\v]+", " ", joined)
        joined = re.sub(r" ?\n ?", "\n", joined)
        return re.sub(r"\n{3,}", "\n\n", joined).strip()


def extract_text(body: str) -> tuple[str, str]:
    parser = _TextExtractor()
    try:
        parser.feed(body)
    except Exception:
        pass
    return html.unescape(parser.title.strip()), parser.text()


# ------------------------------------------------------------------ main

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("url")
    ap.add_argument("--text", action="store_true", help="extract readable text (default: raw)")
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--check-only", action="store_true", help="validate the URL, fetch nothing")
    args = ap.parse_args(argv)

    try:
        cfg = load()
    except ConfigError as e:
        print(f"ERROR  {e}", file=sys.stderr)
        return E_NETWORK

    try:
        if args.check_only:
            print(validate_url(args.url, cfg))
            return OK
        final_url, body = fetch(args.url, cfg, args.timeout)
    except Refused as e:
        print(f"fetch-url: {e}", file=sys.stderr)
        return e.code

    if not body.strip():
        print("fetch-url: empty response", file=sys.stderr)
        return E_EMPTY

    if args.text:
        title, text = extract_text(body)
        if not text:
            print("fetch-url: no readable text extracted", file=sys.stderr)
            return E_EMPTY
        # A caller must know what it actually fetched: a redirect may have moved it.
        print(f"# {title}\n\nsource: {final_url}\n\n{text}")
    else:
        print(body)
    return OK


if __name__ == "__main__":
    sys.exit(main())
