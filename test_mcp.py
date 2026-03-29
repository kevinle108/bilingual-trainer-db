"""Test script for the MCP server"""
import subprocess
import json
import sys

def test_mcp_server():
    """Test the MCP server by sending a test request"""
    
    # Start the MCP server
    process = subprocess.Popen(
        ['.venv/Scripts/python.exe', 'mcp_server.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Send a test request to get language stats
    test_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "get_language_stats",
            "arguments": {}
        }
    }
    
    try:
        # Send request
        process.stdin.write(json.dumps(test_request) + '\n')
        process.stdin.flush()
        
        # Read response
        response = process.stdout.readline()
        print("Response:", response)
        
    finally:
        process.terminate()
        process.wait()

if __name__ == '__main__':
    print("Testing MCP server...")
    test_mcp_server()
