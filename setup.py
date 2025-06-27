from setuptools import setup, find_packages

setup(
    name="mcp_server_devin",
    version="0.1.0",
    description="MCP Server for DonutBuffer - AI interface for C++ ring buffer program",
    packages=["mcp_server_devin_pkg"],
    install_requires=[
        "mcp>=1.0.0",
        "pydantic>=2.0.0",
        "asyncio-mqtt>=0.16.0",
        "httpx>=0.25.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "mcp-server-devin=mcp_server_devin_pkg.server:main",
        ],
    },
)
