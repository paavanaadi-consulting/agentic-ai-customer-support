from mcp_servers.aws_mcp import AWSMCP

def test_aws_mcp_methods():
    mcp = AWSMCP({"region_name": "us-east-1"})
    # These methods are stubs, just check they run
    mcp.connect()
    mcp.send("test")
    mcp.receive()
    mcp.close()
