"""Test script to list all MCP tools"""
import subprocess
import json
import sys

def list_mcp_tools():
    """Request the list of all available tools from the MCP server"""
    
    # Start the MCP server
    process = subprocess.Popen(
        ['.venv/Scripts/python.exe', 'mcp_server.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Send initialize request first
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    # Send tools/list request
    list_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    try:
        # Send initialize
        process.stdin.write(json.dumps(init_request) + '\n')
        process.stdin.flush()
        
        # Read initialize response
        init_response = process.stdout.readline()
        print("Initialize Response:", init_response)
        print()
        
        # Send tools/list
        process.stdin.write(json.dumps(list_request) + '\n')
        process.stdin.flush()
        
        # Read tools/list response
        list_response = process.stdout.readline()
        print("Tools List Response:")
        
        # Parse and pretty print
        response_data = json.loads(list_response)
        if "result" in response_data and "tools" in response_data["result"]:
            tools = response_data["result"]["tools"]
            print(f"\nFound {len(tools)} tools:")
            for i, tool in enumerate(tools, 1):
                print(f"{i}. {tool['name']}")
                if 'description' in tool:
                    desc = tool['description'].split('\n')[0][:80]
                    print(f"   {desc}...")
                print()
        else:
            print(json.dumps(response_data, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")
        stderr_output = process.stderr.read()
        if stderr_output:
            print("STDERR:", stderr_output)
    finally:
        process.terminate()
        process.wait()

if __name__ == '__main__':
    print("Listing MCP server tools...")
    print("=" * 60)
    list_mcp_tools()
