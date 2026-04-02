"""Parse Nmap -oX (XML) output for host addresses."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


def _local_name(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def parse_nmap_xml(path: Path) -> list[tuple[str, str]]:
    """Extract (ip_or_v6, comment) from an Nmap XML file.

    Comment is set to the first hostname (PTR/user) found on the host, if any.
    Order follows the document; duplicates are skipped.
    """
    tree = ET.parse(path)
    root = tree.getroot()
    seen: set[str] = set()
    out: list[tuple[str, str]] = []

    for host in root.iter():
        if _local_name(host.tag) != "host":
            continue

        hostname = ""
        for child in host:
            if _local_name(child.tag) != "hostnames":
                continue
            for hn in child:
                if _local_name(hn.tag) != "hostname":
                    continue
                name = (hn.get("name") or "").strip()
                if name:
                    hostname = name
                    break
            if hostname:
                break

        for child in host:
            if _local_name(child.tag) != "address":
                continue
            if child.get("addrtype") not in ("ipv4", "ipv6"):
                continue
            addr = (child.get("addr") or "").strip()
            if not addr or addr in seen:
                continue
            seen.add(addr)
            out.append((addr, hostname))

    return out
