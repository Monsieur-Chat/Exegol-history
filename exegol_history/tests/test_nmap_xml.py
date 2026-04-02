import textwrap
from pathlib import Path

from exegol_history.targets.nmap_xml import parse_nmap_xml


def test_parse_nmap_xml_basic(tmp_path: Path):
    xml = textwrap.dedent(
        """\
        <?xml version="1.0"?>
        <nmaprun>
          <host>
            <status state="up"/>
            <address addr="10.10.10.1" addrtype="ipv4"/>
            <address addr="AA:BB:CC:DD:EE:FF" addrtype="mac"/>
          </host>
          <host>
            <address addr="10.10.10.2" addrtype="ipv4"/>
          </host>
        </nmaprun>
        """
    )
    p = tmp_path / "scan.xml"
    p.write_text(xml, encoding="utf-8")
    rows = parse_nmap_xml(p)
    assert rows == [("10.10.10.1", ""), ("10.10.10.2", "")]


def test_parse_nmap_xml_hostname_and_ipv6(tmp_path: Path):
    xml = textwrap.dedent(
        """\
        <?xml version="1.0"?>
        <nmaprun>
          <host>
            <hostnames>
              <hostname name="dc.lab.local" type="PTR"/>
            </hostnames>
            <address addr="192.168.0.10" addrtype="ipv4"/>
            <address addr="fe80::1" addrtype="ipv6"/>
          </host>
        </nmaprun>
        """
    )
    p = tmp_path / "scan.xml"
    p.write_text(xml, encoding="utf-8")
    rows = parse_nmap_xml(p)
    assert ("192.168.0.10", "dc.lab.local") in rows
    assert ("fe80::1", "dc.lab.local") in rows


def test_parse_nmap_xml_dedup(tmp_path: Path):
    xml = textwrap.dedent(
        """\
        <?xml version="1.0"?>
        <nmaprun>
          <host>
            <address addr="10.0.0.1" addrtype="ipv4"/>
          </host>
          <host>
            <address addr="10.0.0.1" addrtype="ipv4"/>
          </host>
        </nmaprun>
        """
    )
    p = tmp_path / "scan.xml"
    p.write_text(xml, encoding="utf-8")
    rows = parse_nmap_xml(p)
    assert rows == [("10.0.0.1", "")]
