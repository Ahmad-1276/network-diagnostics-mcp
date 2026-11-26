# Network Diagnostics MCP

Let agents inspect interfaces, DNS, reachability, and open TCP ports.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-000000)
![License](https://img.shields.io/badge/license-MIT-green)

## Tools

| Tool | Description |
| --- | --- |
| `list_interfaces` | Network interfaces with addresses, state, speed, and MTU |
| `get_interface_stats` | Per-interface byte, packet, error, and drop counters |
| `dns_lookup` | Resolve a hostname to IPv4/IPv6 addresses |
| `ping_host` | Send ICMP echo requests and report reachability |
| `check_tcp_port` | Check whether a TCP port is open and measure latency |

## Requirements

- Python 3.10+
- `pip install -e .`

## Install

```bash
git clone https://github.com/Ahmad-1276/network-diagnostics-mcp.git
cd network-diagnostics-mcp

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -e .
```

## Run

```bash
network-diagnostics-mcp
# or
python -m network_diagnostics_mcp.server
```

The server speaks the MCP stdio protocol and waits for a client.

## Connect an MCP client

Add this to your client's MCP config (Claude Desktop, Cursor, VS Code, etc.):

```json
{
  "mcpServers": {
    "network-diagnostics": {
      "command": "/absolute/path/to/.venv/bin/network-diagnostics-mcp",
      "args": []
    }
  }
}
```

Use the absolute path to the executable inside your virtual environment. On Windows the path is `.venv\Scripts\network-diagnostics-mcp.exe`.

## Example prompts

- List network interfaces and IP addresses.
- Resolve example.com.
- Can this host reach 1.1.1.1?
- Is port 443 open on github.com?

## Notes

`ping_host` and `check_tcp_port` generate network traffic. Hostnames are validated and commands are executed without a shell. Some networks block ICMP or outbound ports.

## Development

```bash
pip install -e ".[dev]"
pytest -q
```

## License

MIT — see [LICENSE](LICENSE).
