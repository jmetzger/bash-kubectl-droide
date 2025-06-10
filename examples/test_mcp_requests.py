#!/usr/bin/env python3
"""
Example client to test the MCP server
"""
import requests
import json

MCP_SERVER_URL = "http://localhost:8000/mcp"

def send_mcp_request(method, params=None):
    """Send MCP request to server"""
    if params is None:
        params = {}
    
    request_data = {
        "method": method,
        "params": params
    }
    
    print(f"\n=== Sending MCP Request: {method} ===")
    print(f"Params: {json.dumps(params, indent=2)}")
    
    response = requests.post(MCP_SERVER_URL, json=request_data)
    result = response.json()
    
    print(f"Response: {json.dumps(result, indent=2)}")
    return result

def main():
    print("Testing MCP Server...")
    
    # Test 1: Write YAML manifest
    nginx_yaml = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-nginx
  labels:
    app: test-nginx
spec:
  replicas: 1
  selector:
    matchLabels:
      app: test-nginx
  template:
    metadata:
      labels:
        app: test-nginx
    spec:
      containers:
      - name: nginx
        image: nginx:latest
        ports:
        - containerPort: 80
"""
    
    send_mcp_request("write_yaml_manifest", {
        "yaml": nginx_yaml,
        "filename": "test-nginx.yaml"
    })
    
    # Test 2: List manifests
    send_mcp_request("list_manifests")
    
    # Test 3: Execute kubectl command
    send_mcp_request("execute_kubectl", {
        "command": ["version", "--client"]
    })
    
    # Test 4: Apply manifest with kubectl
    send_mcp_request("execute_kubectl", {
        "command": ["apply", "-f", "test-nginx.yaml"]
    })
    
    # Test 5: Check deployment status
    send_mcp_request("execute_kubectl", {
        "command": ["get", "deployments"]
    })
    
    # Test 6: Delete manifest with kubectl
    send_mcp_request("execute_kubectl", {
        "command": ["delete", "-f", "test-nginx.yaml"]
    })
    
    # Test 7: Execute bash script
    test_script = """#!/bin/bash
echo "Hello from MCP server!"
echo "Current directory: $(pwd)"
echo "Available files:"
ls -la /app/manifests/
"""
    
    send_mcp_request("execute_bash_script", {
        "script": test_script,
        "name": "hello_test"
    })

if __name__ == "__main__":
    main()