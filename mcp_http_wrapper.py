"""
FastAPI HTTP Wrapper for DonutBuffer MCP Server
Allows OpenAI GPTs to connect via Custom Actions
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession
import json
import logging
from typing import Optional, Dict, Any
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-http-wrapper")

app = FastAPI(
    title="DonutBuffer MCP HTTP Wrapper",
    version="1.0.0",
    description="HTTP API wrapper for DonutBuffer MCP Server - enables OpenAI GPT integration via Custom Actions"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BufferRequirementsRequest(BaseModel):
    requirements: str

class BufferConfig(BaseModel):
    buffer_type: str = "mutex"
    producers: int = 1
    consumers: int = 1
    buffer_size_mb: int = 1
    total_transfer_mb: int = 100
    nogui: bool = True

class RunBufferRequest(BaseModel):
    config: BufferConfig

class InterpretResultsRequest(BaseModel):
    execution_output: str
    config: BufferConfig

async def call_mcp_tool(tool_name: str, arguments: Dict[str, Any] = None) -> str:
    """Call MCP server tool and return result"""
    try:
        mcp_server_path = os.path.dirname(os.path.abspath(__file__))
        
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "mcp_server_devin_pkg"],
            cwd=mcp_server_path
        )
        
        async with stdio_client(server_params) as (read_stream, write_stream):
            logger.info(f"Calling MCP tool: {tool_name} with args: {arguments}")
            
            async with ClientSession(read_stream, write_stream) as client:
                await client.initialize()
                result = await client.call_tool(tool_name, arguments or {})
                
                if result.content and len(result.content) > 0:
                    return result.content[0].text
                else:
                    return "No content returned from MCP server"
                
    except Exception as e:
        logger.error(f"Error calling MCP tool {tool_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"MCP server error: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "DonutBuffer MCP HTTP Wrapper",
        "version": "1.0.0",
        "description": "HTTP API for OpenAI GPT integration with DonutBuffer MCP Server",
        "endpoints": {
            "analyze_readme": "GET /analyze-readme",
            "configure_buffer": "POST /configure-buffer", 
            "run_buffer": "POST /run-buffer",
            "interpret_results": "POST /interpret-results"
        },
        "docs": "/docs"
    }

@app.get("/analyze-readme")
async def analyze_readme():
    """
    Analyze DonutBuffer README documentation
    Returns structured analysis of features, requirements, and capabilities
    """
    try:
        result = await call_mcp_tool("analyze_readme")
        return {
            "success": True,
            "analysis": result,
            "tool": "analyze_readme"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in analyze_readme: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/configure-buffer")
async def configure_buffer(request: BufferRequirementsRequest):
    """
    Generate buffer configuration based on user requirements
    Takes natural language requirements and returns optimized buffer config
    """
    try:
        result = await call_mcp_tool("configure_buffer", {
            "requirements": request.requirements
        })
        return {
            "success": True,
            "configuration": result,
            "requirements": request.requirements,
            "tool": "configure_buffer"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in configure_buffer: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/run-buffer")
async def run_buffer(request: RunBufferRequest):
    """
    Execute DonutBuffer with specified configuration
    Returns execution results or build/runtime errors
    """
    try:
        result = await call_mcp_tool("run_buffer", {
            "config": request.config.model_dump()
        })
        return {
            "success": True,
            "execution_result": result,
            "config_used": request.config.model_dump(),
            "tool": "run_buffer"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in run_buffer: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/interpret-results")
async def interpret_results(request: InterpretResultsRequest):
    """
    Interpret DonutBuffer execution results
    Analyzes performance metrics and provides recommendations
    """
    try:
        result = await call_mcp_tool("interpret_results", {
            "execution_output": request.execution_output,
            "config": request.config.model_dump()
        })
        return {
            "success": True,
            "interpretation": result,
            "execution_output": request.execution_output,
            "config_analyzed": request.config.model_dump(),
            "tool": "interpret_results"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in interpret_results: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        result = await call_mcp_tool("analyze_readme")
        return {
            "status": "healthy",
            "mcp_server": "connected",
            "timestamp": "2025-06-27T12:29:26Z"
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "mcp_server": "disconnected",
            "error": str(e),
            "timestamp": "2025-06-27T12:29:26Z"
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
