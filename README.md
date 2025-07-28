# Statler & Waldorf MCP - The Nitpicky Systems Architects

Statler and Waldorf are Model Context Protocol (MCP) servers that provide critical code review tools. They act as nitpicky systems architects that challenge your code and architectural plans to help you write better, more secure, and more maintainable software.

- **Statler**: Powered by Ollama (local LLMs)
- **Waldorf**: Powered by OpenRouter (cloud LLMs)

## Features

- 🔍 **Critical Code Review**: Identifies security vulnerabilities, performance issues, and code quality problems
- 🏗️ **Architecture Analysis**: Reviews system designs and architectural plans
- 🎭 **Personality-Driven**: Statler has a grumpy but helpful personality that provides constructive criticism
- 🚀 **Ollama Integration**: Uses local LLMs through Ollama for privacy and customization
- 🔧 **MCP Compatible**: Works seamlessly with Claude Code and other MCP clients

## Prerequisites

### For Statler (Ollama)
1. **Ollama**: Install Ollama from [ollama.ai](https://ollama.ai)
2. **Python 3.8+**: Required for running the MCP server
3. **A compatible LLM**: Pull a model in Ollama (e.g., `ollama pull llama3.2`)

### For Waldorf (OpenRouter)
1. **OpenRouter Account**: Sign up at [openrouter.ai](https://openrouter.ai)
2. **Python 3.8+**: Required for running the MCP server
3. **API Key**: Get your API key from OpenRouter dashboard

## Installation

1. Clone the repository:
```bash
git clone https://github.com/coconsultant/statler.git
cd statler
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Ensure Ollama is running:
```bash
ollama list  # Should show available models
```

## Configuration

Both servers **exclusively** use environment variables for configuration. These variables always take precedence.

### Statler (Ollama) Configuration

- `OLLAMA_API_BASE`: Ollama API endpoint (default: `http://localhost:11434`)
- `OLLAMA_MCP_MODEL`: Model to use for reviews (default: `llama3.2`)

Example:
```bash
export OLLAMA_API_BASE="http://localhost:11434"
export OLLAMA_MCP_MODEL="llama3.2"
```

### Waldorf (OpenRouter) Configuration

- `OPENROUTER_BASE_URL`: OpenRouter API endpoint (default: `https://openrouter.ai/api/v1`)
- `OPENROUTER_API_KEY`: Your OpenRouter API key (**required**)
- `OPENROUTER_MCP_MODEL`: Model to use for reviews (default: `openai/gpt-3.5-turbo`)

Example:
```bash
export OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
export OPENROUTER_API_KEY="your-api-key-here"
export OPENROUTER_MCP_MODEL="openai/gpt-4"
```

**Important**: There are no configuration files or local settings. Both servers always read from environment variables, ensuring consistent behavior across all environments.

## Running the Server

### Standalone Mode

For Statler (Ollama):
```bash
python statler_mcp.py
```

For Waldorf (OpenRouter):
```bash
python waldorf_mcp.py
```

### With Claude Code

You can add either server to Claude Code in two ways:

#### Option 1: Using Claude MCP CLI (Recommended)

For Statler:
```bash
claude mcp add statler $(PWD)/statler_mcp.py
```

For Waldorf:
```bash
claude mcp add waldorf $(PWD)/waldorf_mcp.py
```

#### Option 2: Manual Configuration
Add to your Claude Code configuration (`.claude/claude_desktop_config.json`):

For Statler:
```json
{
  "mcpServers": {
    "statler": {
      "command": "python",
      "args": ["$(PWD)/statler_mcp.py"],
      "env": {
        "OLLAMA_API_BASE": "http://localhost:11434",
        "OLLAMA_MCP_MODEL": "llama3.2"
      }
    }
  }
}
```

For Waldorf:
```json
{
  "mcpServers": {
    "waldorf": {
      "command": "python",
      "args": ["$(PWD)/waldorf_mcp.py"],
      "env": {
        "OPENROUTER_API_KEY": "your-api-key-here",
        "OPENROUTER_MCP_MODEL": "openai/gpt-4"
      }
    }
  }
}
```

After either method, restart Claude Code.

### Using in Claude Code

For Statler:
```
Can you use the statler_architect tool to review this code:

def get_user(id):
    return db.query(f"SELECT * FROM users WHERE id={id}")
```

For Waldorf:
```
Can you use the waldorf_architect tool to review this code:

def get_user(id):
    return db.query(f"SELECT * FROM users WHERE id={id}")
```

## Usage Examples

### Code Review
```python
# Request a code review
result = await statler_architect(
    code_or_plan='''
    def authenticate_user(username, password):
        user = db.find_user(username)
        if user.password == password:
            return True
        return False
    ''',
    context="User authentication function"
)
```

### Architecture Review
```python
# Review an architectural plan
result = await statler_architect(
    code_or_plan='''
    Our microservices architecture:
    - Frontend talks directly to all microservices
    - Each service has its own database
    - No API gateway or service mesh
    - Services communicate via HTTP
    ''',
    context="E-commerce platform architecture"
)
```

## Available MCP Resources

### Statler Resources
- `statler://config`: View current Statler configuration
- `statler://personality`: Learn about Statler's personality

### Waldorf Resources
- `waldorf://config`: View current Waldorf configuration
- `waldorf://personality`: Learn about Waldorf's personality

## Development

### Project Structure
```
statler/
├── statler_mcp.py          # Statler MCP server (Ollama)
├── waldorf_mcp.py          # Waldorf MCP server (OpenRouter)
├── statler_config.py       # Statler configuration
├── waldorf_config.py       # Waldorf configuration
├── tools/
│   ├── base_architect.py   # Shared base class
│   ├── statler_architect.py # Statler architect (Ollama)
│   └── waldorf_architect.py # Waldorf architect (OpenRouter)
├── prompts/
│   └── statler_prompts.py  # Shared personality and prompts
└── requirements.txt        # Dependencies
```

### Running Tests
```bash
# Test Statler locally
mcp dev ./statler_mcp.py

# Test Waldorf locally
mcp dev ./waldorf_mcp.py

# Run unit tests
python -m pytest tests/
```

## Troubleshooting

### Statler (Ollama) Issues

#### "Cannot connect to Ollama"
- Ensure Ollama is running: `ollama serve`
- Check the API base URL is correct
- Verify the model exists: `ollama list`

#### "Model not found"
- Pull the required model: `ollama pull llama3.2`
- Set the correct model name in `OLLAMA_MCP_MODEL`

### Waldorf (OpenRouter) Issues

#### "Authentication failed"
- Verify your `OPENROUTER_API_KEY` is correct
- Check your OpenRouter account status

#### "Model not found"
- Check available models at [openrouter.ai/models](https://openrouter.ai/models)
- Use the full model name (e.g., `openai/gpt-4`, not just `gpt-4`)

#### "Rate limit exceeded"
- Wait a few minutes before trying again
- Consider upgrading your OpenRouter plan

### General Issues

#### Server won't start
- Check Python version: `python --version` (needs 3.8+)
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check environment variables are set correctly

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

GPL v3 License - see LICENSE file for details

## Acknowledgments

- Inspired by the Muppets' Statler and Waldorf
- Built on the MCP protocol by Anthropic
- Statler powered by Ollama and open-source LLMs
- Waldorf powered by OpenRouter's multi-model platform
