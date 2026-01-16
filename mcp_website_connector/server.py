from mcp.server.fastmcp import FastMCP

mcp = FastMCP('Apotheon Website Connector MCP')

@mcp.tool()
def search_pages(query: str):
    return {'query': query}

if __name__ == '__main__':
    mcp.run()
