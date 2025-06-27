# MCP Server for DonutBuffer

This is an MCP (Model Context Protocol) server that provides an AI interface for working with the DonutBuffer C++ ring buffer program.

## Features

- Analyze DonutBuffer README and documentation
- Help users configure ring buffer parameters
- Assist with running different buffer implementations (lockfree, mutex, concurrent_queue)
- Evaluate and interpret buffer performance results
- Provide guidance on buffer usage and optimization

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Run the MCP server:

```bash
python -m mcp_server_devin
```

## Available Tools

- `analyze_readme`: Analyze DonutBuffer README and provide insights
- `configure_buffer`: Help configure buffer parameters based on user requirements
- `run_buffer`: Execute DonutBuffer with specified parameters
- `interpret_results`: Analyze buffer performance output and provide recommendations

## Available Resources

- `donut_buffer_docs`: Access to DonutBuffer documentation and README content
- `buffer_configs`: Common buffer configuration templates
