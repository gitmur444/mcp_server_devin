"""Main MCP server implementation for DonutBuffer interface."""

import asyncio
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    CallToolRequest,
    CallToolResult,
    ListResourcesRequest,
    ListResourcesResult,
    ListToolsRequest,
    ListToolsResult,
    ReadResourceRequest,
    ReadResourceResult,
)
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-donutbuffer")

server = Server("donutbuffer-mcp")

class BufferConfig(BaseModel):
    """Configuration for DonutBuffer execution."""
    buffer_type: str = "mutex"  # lockfree, mutex, concurrent_queue
    producers: int = 1
    consumers: int = 1
    buffer_size_mb: int = 1
    total_transfer_mb: int = 100
    nogui: bool = True

class DonutBufferInterface:
    """Interface to DonutBuffer C++ program."""
    
    def __init__(self, donut_buffer_path: Optional[str] = None):
        """Initialize with path to DonutBuffer repository."""
        self.donut_buffer_path = donut_buffer_path or self._find_donut_buffer()
        self.readme_content = self._load_readme()
    
    def _find_donut_buffer(self) -> str:
        """Find DonutBuffer repository path."""
        possible_paths = [
            "/home/ubuntu/DonutBuffer",
            "../DonutBuffer",
            "./DonutBuffer",
        ]
        
        for path in possible_paths:
            if os.path.exists(path) and os.path.exists(os.path.join(path, "README.md")):
                return path
        
        raise FileNotFoundError("DonutBuffer repository not found")
    
    def _load_readme(self) -> str:
        """Load README content from DonutBuffer."""
        readme_path = os.path.join(self.donut_buffer_path, "README.md")
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load README: {e}")
            return ""
    
    def analyze_readme(self) -> Dict[str, Any]:
        """Analyze README and extract key information."""
        return {
            "content": self.readme_content,
            "key_features": [
                "Ring Buffer Visualizer with GUI controls",
                "Multiple buffer implementations: lockfree, mutex, concurrent_queue",
                "Performance testing and benchmarking",
                "Docker and Codespaces support",
                "Command-line interface with various options"
            ],
            "build_requirements": [
                "C++20 compiler (g++/clang++)",
                "CMake 3.28+",
                "Ninja",
                "GLFW",
                "Dear ImGui",
                "GLAD"
            ],
            "buffer_types": ["lockfree", "mutex", "concurrent_queue"],
            "command_options": {
                "--nogui": "Run without GUI (default: true)",
                "--mutex-vs-lockfree": "Compare MutexRingBuffer and LockFreeRingBuffer",
                "--concurrent-vs-lockfree": "Compare ConcurrentQueue and LockFreeRingBuffer",
                "--buffer-type": "Type of buffer to use",
                "--producers": "Number of producer threads",
                "--consumers": "Number of consumer threads",
                "--buffer-size_mb": "Buffer size in megabytes",
                "--total-transfer_mb": "Total data transfer in megabytes"
            }
        }
    
    def configure_buffer(self, requirements: str) -> BufferConfig:
        """Configure buffer based on user requirements."""
        config = BufferConfig()
        
        requirements_lower = requirements.lower()
        
        if "lockfree" in requirements_lower or "lock-free" in requirements_lower:
            config.buffer_type = "lockfree"
        elif "concurrent" in requirements_lower:
            config.buffer_type = "concurrent_queue"
        else:
            config.buffer_type = "mutex"
        
        import re
        numbers = re.findall(r'\d+', requirements)
        
        if "producer" in requirements_lower and numbers:
            config.producers = min(int(numbers[0]), 16)  # Reasonable limit
        
        if "consumer" in requirements_lower and numbers:
            idx = 1 if "producer" in requirements_lower and len(numbers) > 1 else 0
            if idx < len(numbers):
                config.consumers = min(int(numbers[idx]), 16)
        
        if "large" in requirements_lower or "big" in requirements_lower:
            config.buffer_size_mb = 10
            config.total_transfer_mb = 1000
        elif "small" in requirements_lower:
            config.buffer_size_mb = 1
            config.total_transfer_mb = 10
        elif "performance" in requirements_lower or "benchmark" in requirements_lower:
            config.buffer_size_mb = 5
            config.total_transfer_mb = 500
        
        return config
    
    def run_buffer(self, config: BufferConfig) -> Dict[str, Any]:
        """Execute DonutBuffer with given configuration."""
        try:
            app_path = os.path.join(self.donut_buffer_path, "build", "DonutBufferApp")
            
            if not os.path.exists(app_path):
                return {
                    "success": False,
                    "error": f"DonutBufferApp not found at {app_path}. Please build the project first.",
                    "build_instructions": "Run: mkdir -p build && cd build && cmake .. -G Ninja && cmake --build ."
                }
            
            cmd = [app_path]
            
            if config.nogui:
                cmd.append("--nogui")
            
            cmd.extend([
                f"--buffer-type={config.buffer_type}",
                f"--producers={config.producers}",
                f"--consumers={config.consumers}",
                f"--buffer-size_mb={config.buffer_size_mb}",
                f"--total-transfer_mb={config.total_transfer_mb}"
            ])
            
            result = subprocess.run(
                cmd,
                cwd=self.donut_buffer_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd),
                "config": config.dict()
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Buffer execution timed out after 30 seconds",
                "config": config.dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to execute buffer: {str(e)}",
                "config": config.dict()
            }
    
    def interpret_results(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Interpret buffer execution results and provide insights."""
        if not execution_result.get("success", False):
            return {
                "interpretation": "Execution failed",
                "error": execution_result.get("error", "Unknown error"),
                "recommendations": [
                    "Check if DonutBuffer is built correctly",
                    "Verify all dependencies are installed",
                    "Try with different buffer configuration"
                ]
            }
        
        stdout = execution_result.get("stdout", "")
        config = execution_result.get("config", {})
        
        analysis = {
            "interpretation": "Buffer execution completed successfully",
            "config_used": config,
            "performance_notes": [],
            "recommendations": []
        }
        
        if "throughput" in stdout.lower():
            analysis["performance_notes"].append("Throughput metrics available in output")
        
        if "latency" in stdout.lower():
            analysis["performance_notes"].append("Latency measurements recorded")
        
        buffer_type = config.get("buffer_type", "unknown")
        if buffer_type == "lockfree":
            analysis["recommendations"].append("Lock-free buffer chosen - good for high-performance scenarios")
        elif buffer_type == "mutex":
            analysis["recommendations"].append("Mutex buffer chosen - good for general use cases")
        elif buffer_type == "concurrent_queue":
            analysis["recommendations"].append("Concurrent queue chosen - good for complex producer-consumer patterns")
        
        producers = config.get("producers", 1)
        consumers = config.get("consumers", 1)
        
        if producers > consumers:
            analysis["recommendations"].append("More producers than consumers - may cause buffer overflow")
        elif consumers > producers:
            analysis["recommendations"].append("More consumers than producers - may cause buffer underflow")
        else:
            analysis["recommendations"].append("Balanced producer-consumer ratio")
        
        return analysis

try:
    donut_interface = DonutBufferInterface()
    logger.info(f"DonutBuffer interface initialized with path: {donut_interface.donut_buffer_path}")
except Exception as e:
    logger.error(f"Failed to initialize DonutBuffer interface: {e}")
    donut_interface = None

@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List available resources."""
    resources = [
        Resource(
            uri="file:///donut_buffer_docs/readme",
            name="DonutBuffer README",
            description="Complete README documentation for DonutBuffer",
            mimeType="text/markdown",
        ),
        Resource(
            uri="file:///donut_buffer_docs/analysis",
            name="DonutBuffer Analysis",
            description="Analyzed information about DonutBuffer features and capabilities",
            mimeType="application/json",
        ),
        Resource(
            uri="file:///buffer_configs/templates",
            name="Buffer Configuration Templates",
            description="Common buffer configuration templates for different use cases",
            mimeType="application/json",
        ),
    ]
    return resources

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read a specific resource."""
    if not donut_interface:
        raise ValueError("DonutBuffer interface not available")
    
    if uri == "file:///donut_buffer_docs/readme":
        return donut_interface.readme_content
    
    elif uri == "file:///donut_buffer_docs/analysis":
        analysis = donut_interface.analyze_readme()
        return json.dumps(analysis, indent=2)
    
    elif uri == "file:///buffer_configs/templates":
        templates = {
            "high_performance": {
                "buffer_type": "lockfree",
                "producers": 4,
                "consumers": 4,
                "buffer_size_mb": 10,
                "total_transfer_mb": 1000,
                "description": "High-performance configuration for maximum throughput"
            },
            "balanced": {
                "buffer_type": "mutex",
                "producers": 2,
                "consumers": 2,
                "buffer_size_mb": 5,
                "total_transfer_mb": 500,
                "description": "Balanced configuration for general use"
            },
            "simple": {
                "buffer_type": "mutex",
                "producers": 1,
                "consumers": 1,
                "buffer_size_mb": 1,
                "total_transfer_mb": 100,
                "description": "Simple configuration for testing and learning"
            },
            "stress_test": {
                "buffer_type": "concurrent_queue",
                "producers": 8,
                "consumers": 8,
                "buffer_size_mb": 20,
                "total_transfer_mb": 2000,
                "description": "Stress test configuration with high load"
            }
        }
        return json.dumps(templates, indent=2)
    
    else:
        raise ValueError(f"Unknown resource URI: {uri}")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="analyze_readme",
            description="Analyze DonutBuffer README and provide insights about features and capabilities",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="configure_buffer",
            description="Help configure buffer parameters based on user requirements",
            inputSchema={
                "type": "object",
                "properties": {
                    "requirements": {
                        "type": "string",
                        "description": "User requirements for buffer configuration (e.g., 'high performance with 4 producers and 2 consumers')",
                    }
                },
                "required": ["requirements"],
            },
        ),
        Tool(
            name="run_buffer",
            description="Execute DonutBuffer with specified parameters",
            inputSchema={
                "type": "object",
                "properties": {
                    "buffer_type": {
                        "type": "string",
                        "enum": ["lockfree", "mutex", "concurrent_queue"],
                        "description": "Type of buffer implementation to use",
                        "default": "mutex"
                    },
                    "producers": {
                        "type": "integer",
                        "description": "Number of producer threads",
                        "default": 1,
                        "minimum": 1,
                        "maximum": 16
                    },
                    "consumers": {
                        "type": "integer", 
                        "description": "Number of consumer threads",
                        "default": 1,
                        "minimum": 1,
                        "maximum": 16
                    },
                    "buffer_size_mb": {
                        "type": "integer",
                        "description": "Buffer size in megabytes",
                        "default": 1,
                        "minimum": 1,
                        "maximum": 100
                    },
                    "total_transfer_mb": {
                        "type": "integer",
                        "description": "Total data transfer in megabytes",
                        "default": 100,
                        "minimum": 1,
                        "maximum": 10000
                    }
                },
                "required": [],
            },
        ),
        Tool(
            name="interpret_results",
            description="Analyze buffer performance output and provide recommendations",
            inputSchema={
                "type": "object",
                "properties": {
                    "execution_result": {
                        "type": "object",
                        "description": "Result from run_buffer tool execution",
                    }
                },
                "required": ["execution_result"],
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if not donut_interface:
        return [TextContent(type="text", text="Error: DonutBuffer interface not available")]
    
    try:
        if name == "analyze_readme":
            analysis = donut_interface.analyze_readme()
            result = json.dumps(analysis, indent=2)
            return [TextContent(type="text", text=result)]
        
        elif name == "configure_buffer":
            requirements = arguments.get("requirements", "")
            config = donut_interface.configure_buffer(requirements)
            result = {
                "configuration": config.dict(),
                "explanation": f"Generated configuration based on requirements: '{requirements}'"
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "run_buffer":
            config = BufferConfig(**arguments)
            execution_result = donut_interface.run_buffer(config)
            return [TextContent(type="text", text=json.dumps(execution_result, indent=2))]
        
        elif name == "interpret_results":
            execution_result = arguments.get("execution_result", {})
            interpretation = donut_interface.interpret_results(execution_result)
            return [TextContent(type="text", text=json.dumps(interpretation, indent=2))]
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return [TextContent(type="text", text=f"Error executing tool {name}: {str(e)}")]

async def main():
    """Main entry point for the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="donutbuffer-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(
                        resources_changed=False,
                        tools_changed=False,
                        prompts_changed=False,
                    ),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
