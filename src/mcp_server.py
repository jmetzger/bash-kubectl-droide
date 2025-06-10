#!/usr/bin/env python3
import os
import subprocess
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Kubernetes MCP Server", version="1.0.0")

class MCPRequest(BaseModel):
    method: str
    params: Dict[str, Any] = {}

class MCPResponse(BaseModel):
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class KubectlMCPServer:
    def __init__(self):
        self.manifests_dir = Path("/app/manifests")
        self.scripts_dir = Path("/app/scripts")
        self.logs_dir = Path("/app/logs")
        
        # Ensure directories exist
        self.manifests_dir.mkdir(exist_ok=True)
        self.scripts_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Verify kubectl is available
        try:
            subprocess.run(["kubectl", "version", "--client"], 
                         capture_output=True, check=True)
        except subprocess.CalledProcessError:
            raise RuntimeError("kubectl not available in container")

    async def execute_bash_script(self, script_content: str, script_name: str = "temp_script") -> Dict[str, Any]:
        """Execute a bash script and return MCP-compliant response"""
        try:
            script_path = self.scripts_dir / f"{script_name}.sh"
            
            # Write script to file
            script_path.write_text(script_content)
            script_path.chmod(0o755)
            
            # Execute script
            process = await asyncio.create_subprocess_exec(
                "bash", str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ}
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "exit_code": process.returncode,
                "stdout": stdout.decode('utf-8'),
                "stderr": stderr.decode('utf-8'),
                "script_path": str(script_path)
            }
            
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "script_path": ""
            }

    async def write_yaml_manifest(self, yaml_content: str, filename: str) -> Dict[str, Any]:
        """Write YAML manifest to filesystem"""
        try:
            manifest_path = self.manifests_dir / filename
            manifest_path.write_text(yaml_content)
            
            return {
                "path": str(manifest_path),
                "size": len(yaml_content),
                "exists": manifest_path.exists()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to write manifest: {str(e)}")

    async def execute_kubectl_command(self, command: list) -> Dict[str, Any]:
        """Execute kubectl command"""
        try:
            full_command = ["kubectl"] + command
            
            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ}
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "exit_code": process.returncode,
                "stdout": stdout.decode('utf-8'),
                "stderr": stderr.decode('utf-8'),
                "command": " ".join(full_command)
            }
            
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "command": " ".join(["kubectl"] + command)
            }

    async def list_manifests(self) -> Dict[str, Any]:
        """List all YAML manifests in the manifests directory"""
        try:
            manifests = []
            for manifest_file in self.manifests_dir.glob("*.yaml"):
                manifests.append({
                    "name": manifest_file.name,
                    "path": str(manifest_file),
                    "size": manifest_file.stat().st_size
                })
            
            return {"manifests": manifests, "count": len(manifests)}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list manifests: {str(e)}")

# Initialize server
mcp_server = KubectlMCPServer()

@app.post("/mcp", response_model=MCPResponse)
async def handle_mcp_request(request: MCPRequest):
    """Main MCP endpoint"""
    try:
        method = request.method
        params = request.params
        
        if method == "execute_bash_script":
            script_content = params.get("script", "")
            script_name = params.get("name", "temp_script")
            
            if not script_content:
                return MCPResponse(success=False, error="Script content is required")
            
            result = await mcp_server.execute_bash_script(script_content, script_name)
            
            if result["exit_code"] == 0:
                return MCPResponse(success=True, result=result)
            else:
                return MCPResponse(
                    success=False, 
                    error=f"Script execution failed: {result['stderr']}",
                    result=result
                )
        
        elif method == "write_yaml_manifest":
            yaml_content = params.get("yaml", "")
            filename = params.get("filename", "manifest.yaml")
            
            if not yaml_content:
                return MCPResponse(success=False, error="YAML content is required")
            
            result = await mcp_server.write_yaml_manifest(yaml_content, filename)
            return MCPResponse(success=True, result=result)
        
        elif method == "execute_kubectl":
            command = params.get("command", [])
            
            if not command:
                return MCPResponse(success=False, error="kubectl command is required")
            
            result = await mcp_server.execute_kubectl_command(command)
            
            if result["exit_code"] == 0:
                return MCPResponse(success=True, result=result)
            else:
                return MCPResponse(
                    success=False,
                    error=f"kubectl command failed: {result['stderr']}",
                    result=result
                )
        
        elif method == "list_manifests":
            result = await mcp_server.list_manifests()
            return MCPResponse(success=True, result=result)
        
        else:
            return MCPResponse(success=False, error=f"Unknown method: {method}")
    
    except Exception as e:
        return MCPResponse(success=False, error=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "kubectl_available": True}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Kubernetes MCP Server",
        "version": "1.0.0",
        "description": "MCP server for kubectl operations and bash script execution",
        "endpoints": {
            "mcp": "/mcp",
            "health": "/health"
        },
        "supported_methods": [
            "execute_bash_script",
            "write_yaml_manifest", 
            "execute_kubectl",
            "list_manifests"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)