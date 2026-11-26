"""Network diagnostics MCP server."""

from __future__ import annotations

import re
import shutil
import socket
import time
from typing import Any

import psutil
from mcp.server.fastmcp import FastMCP

from .common import err, human_bytes, ok, run

mcp = FastMCP("network-diagnostics")

_HOST_RE = re.compile(r"^[A-Za-z0-9._:-]+$")


def _valid_host(host: str) -> bool:
    host = host.strip()
    return bool(host) and len(host) <= 253 and not host.startswith("-") and bool(_HOST_RE.match(host))


def _family_name(family: int) -> str:
    if family == socket.AF_INET:
        return "IPv4"
    if family == socket.AF_INET6:
        return "IPv6"
    if hasattr(psutil, "AF_LINK") and family == psutil.AF_LINK:
        return "MAC"
    return str(family)


@mcp.tool()
def list_interfaces() -> dict[str, Any]:
    """Return network interfaces with addresses, state, speed, and MTU."""
    try:
        addresses = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        interfaces = []

        for name in sorted(addresses):
            interface_stats = stats.get(name)
            interface_addresses = []
            for address in addresses[name]:
                interface_addresses.append(
                    {
                        "family": _family_name(address.family),
                        "address": address.address,
                        "netmask": address.netmask,
                        "broadcast": address.broadcast,
                    }
                )
            interfaces.append(
                {
                    "name": name,
                    "addresses": interface_addresses,
                    "is_up": interface_stats.isup if interface_stats else None,
                    "speed_mbps": interface_stats.speed if interface_stats else None,
                    "mtu": interface_stats.mtu if interface_stats else None,
                    "duplex": str(interface_stats.duplex) if interface_stats else None,
                }
            )

        return ok({"interfaces": interfaces, "count": len(interfaces)})
    except Exception as exc:  # noqa: BLE001
        return err(str(exc))


@mcp.tool()
def get_interface_stats() -> dict[str, Any]:
    """Return per-interface byte, packet, error, and drop counters."""
    try:
        counters = psutil.net_io_counters(pernic=True)
        interfaces = {}
        for name, item in counters.items():
            data = item._asdict()
            data["bytes_sent_human"] = human_bytes(item.bytes_sent)
            data["bytes_recv_human"] = human_bytes(item.bytes_recv)
            interfaces[name] = data
        return ok({"interfaces": interfaces, "count": len(interfaces)})
    except Exception as exc:  # noqa: BLE001
        return err(str(exc))


@mcp.tool()
def dns_lookup(host: str) -> dict[str, Any]:
    """Resolve a hostname to IPv4/IPv6 addresses."""
    try:
        host = host.strip()
        if not _valid_host(host):
            return err("invalid hostname")
        results = socket.getaddrinfo(host, None)
        seen = set()
        addresses = []
        for family, _socktype, _proto, _canonname, sockaddr in results:
            address = sockaddr[0]
            key = (family, address)
            if key in seen:
                continue
            seen.add(key)
            addresses.append({"family": _family_name(family), "address": address})
        return ok({"host": host, "addresses": addresses, "count": len(addresses)})
    except socket.gaierror as exc:
        return err(f"DNS lookup failed: {exc}")
    except Exception as exc:  # noqa: BLE001
        return err(str(exc))


@mcp.tool()
def ping_host(host: str, count: int = 3) -> dict[str, Any]:
    """Send ICMP echo requests and report reachability.

    Args:
        host: Hostname or IP address (no shell metacharacters).
        count: Number of echo requests (1-10).
    """
    try:
        host = host.strip()
        if not _valid_host(host):
            return err("invalid hostname")
        count = max(1, min(int(count), 10))

        ping = shutil.which("ping")
        if not ping:
            return err("ping executable not found on this system")

        if psutil.WINDOWS:
            command = [ping, "-n", str(count), host]
        else:
            command = [ping, "-c", str(count), host]

        result = run(command, timeout=count * 3 + 5)
        if result is None:
            return err("ping failed or timed out")

        output = (result.stdout or "") + (result.stderr or "")
        times = [float(value) for value in re.findall(r"time[=<]\s*([\d.]+)", output)]
        return ok(
            {
                "host": host,
                "reachable": result.returncode == 0,
                "returncode": result.returncode,
                "packets_sent": count,
                "rtt_ms": times,
                "min_rtt_ms": min(times) if times else None,
                "max_rtt_ms": max(times) if times else None,
                "output": output.strip()[:4000],
            }
        )
    except Exception as exc:  # noqa: BLE001
        return err(str(exc))


@mcp.tool()
def check_tcp_port(host: str, port: int, timeout: float = 3.0) -> dict[str, Any]:
    """Check whether a TCP port is open and measure connection latency."""
    try:
        host = host.strip()
        if not _valid_host(host):
            return err("invalid hostname")
        port = int(port)
        if not 1 <= port <= 65535:
            return err("port must be between 1 and 65535")
        timeout = max(0.1, min(float(timeout), 30.0))

        started = time.perf_counter()
        try:
            connection = socket.create_connection((host, port), timeout=timeout)
        except OSError as exc:
            return ok(
                {
                    "host": host,
                    "port": port,
                    "open": False,
                    "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                    "error": str(exc),
                }
            )

        with connection:
            latency = (time.perf_counter() - started) * 1000
        return ok(
            {
                "host": host,
                "port": port,
                "open": True,
                "latency_ms": round(latency, 2),
                "error": None,
            }
        )
    except Exception as exc:  # noqa: BLE001
        return err(str(exc))


def main() -> None:
    """Run the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
