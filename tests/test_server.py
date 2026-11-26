from network_diagnostics_mcp import server

def test_interfaces():
    result = server.list_interfaces()
    assert result["success"] is True
    assert "interfaces" in result["data"]

def test_stats():
    assert server.get_interface_stats()["success"] is True

def test_dns_and_port_check():
    dns = server.dns_lookup("localhost")
    assert dns["success"] is True
    port = server.check_tcp_port("127.0.0.1", 1, timeout=0.2)
    assert port["success"] is True
    assert port["data"]["open"] is False
