# AI Provider Setup Guide

Skynette supports multiple AI providers, allowing you to choose between local models (free and private) or cloud providers (powerful and fast). This guide will help you configure each provider.

## Table of Contents
- [Quick Start](#quick-start)
- [Local Models](#local-models)
- [Cloud Providers](#cloud-providers)
- [Configuration](#configuration)
- [Testing Your Setup](#testing-your-setup)
- [Troubleshooting](#troubleshooting)

## Quick Start

1. Choose your provider(s)
2. Obtain API keys (for cloud providers)
3. Configure Skynette
4. Test the connection

## Local Models

Run AI models locally on your machine - completely free and private.

### Supported Local Providers

- **llama.cpp**: LLaMA, Mistral, Phi, and other GGUF models
- **Ollama**: Easy model management with automatic downloads

### Setting Up Local Models

#### Option 1: Using llama.cpp (Built-in)

Skynette includes `llama-cpp-python` by default.

1. **Download a Model**:
   - Use Skynette's Model Hub (in the AI Hub view)
   - Or manually download from [Hugging Face](https://huggingface.co/models?library=gguf)

   Popular models:
   - [Mistral 7B GGUF](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF)
   - [LLaMA 2 7B GGUF](https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF)
   - [Phi-2 GGUF](https://huggingface.co/TheBloke/phi-2-GGUF)

2. **Configure Model Path**:
   ```yaml
   # ~/.skynette/config.yaml
   ai:
     default_provider: local
     local:
       model_path: ~/skynette/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf
       context_size: 4096
       gpu_layers: 35  # Use GPU acceleration (0 for CPU only)
   ```

3. **System Requirements**:
   - **CPU**: Modern multi-core processor
   - **RAM**: 8GB minimum, 16GB recommended
   - **GPU** (optional): NVIDIA GPU with CUDA for faster inference
   - **Storage**: 4-8GB per model

#### Option 2: Using Ollama

1. **Install Ollama**:
   ```bash
   # macOS/Linux
   curl -fsSL https://ollama.ai/install.sh | sh

   # Windows
   # Download from https://ollama.ai/download
   ```

2. **Download Models**:
   ```bash
   ollama pull mistral
   ollama pull llama2
   ollama pull codellama
   ```

3. **Configure Skynette**:
   ```yaml
   # ~/.skynette/config.yaml
   ai:
     default_provider: ollama
     ollama:
       base_url: http://localhost:11434
       model: mistral
   ```

## Cloud Providers

Cloud providers offer powerful models with minimal setup. Requires API keys and internet connection.

### OpenAI

Most popular provider with GPT-3.5, GPT-4, and more.

1. **Get API Key**:
   - Go to [OpenAI Platform](https://platform.openai.com/)
   - Sign up or log in
   - Navigate to API Keys section
   - Create new secret key
   - Copy the key (starts with `sk-`)

2. **Configure in Skynette**:
   ```yaml
   # ~/.skynette/config.yaml
   ai:
     default_provider: openai
     openai:
       api_key: sk-proj-...
       model: gpt-4-turbo-preview
       organization: org-...  # Optional
   ```

3. **Available Models**:
   - `gpt-4-turbo-preview`: Most capable, best for complex tasks
   - `gpt-4`: Stable GPT-4 version
   - `gpt-3.5-turbo`: Fast and cost-effective
   - `gpt-4-vision-preview`: Image understanding

4. **Pricing** (as of 2024):
   - GPT-4 Turbo: $0.01/1K input, $0.03/1K output tokens
   - GPT-3.5 Turbo: $0.0005/1K input, $0.0015/1K output tokens

### Anthropic (Claude)

High-quality models with large context windows.

1. **Get API Key**:
   - Go to [Anthropic Console](https://console.anthropic.com/)
   - Sign up or log in
   - Navigate to API Keys
   - Create new key
   - Copy the key (starts with `sk-ant-`)

2. **Configure in Skynette**:
   ```yaml
   # ~/.skynette/config.yaml
   ai:
     default_provider: anthropic
     anthropic:
       api_key: sk-ant-...
       model: claude-3-5-sonnet-20241022
   ```

3. **Available Models**:
   - `claude-3-5-sonnet-20241022`: Best balance of speed and intelligence
   - `claude-3-opus-20240229`: Most capable, best for complex tasks
   - `claude-3-haiku-20240307`: Fastest, most cost-effective

4. **Pricing**:
   - Claude 3.5 Sonnet: $3/MTok input, $15/MTok output
   - Claude 3 Opus: $15/MTok input, $75/MTok output
   - Claude 3 Haiku: $0.25/MTok input, $1.25/MTok output

### Google AI (Gemini)

Google's multimodal AI with competitive pricing.

1. **Get API Key**:
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Sign in with Google account
   - Create API key
   - Copy the key

2. **Configure in Skynette**:
   ```yaml
   # ~/.skynette/config.yaml
   ai:
     default_provider: google
     google:
       api_key: AIza...
       model: gemini-pro
   ```

3. **Available Models**:
   - `gemini-pro`: Text generation
   - `gemini-pro-vision`: Multimodal (text + images)
   - `gemini-ultra`: Most capable (limited access)

4. **Pricing**:
   - Gemini Pro: Free tier available, then $0.00025/1K characters

### Groq

Ultra-fast inference with competitive pricing.

1. **Get API Key**:
   - Go to [Groq Console](https://console.groq.com/)
   - Sign up or log in
   - Create API key
   - Copy the key (starts with `gsk_`)

2. **Configure in Skynette**:
   ```yaml
   # ~/.skynette/config.yaml
   ai:
     default_provider: groq
     groq:
       api_key: gsk_...
       model: mixtral-8x7b-32768
   ```

3. **Available Models**:
   - `mixtral-8x7b-32768`: Fast Mixtral model with large context
   - `llama2-70b-4096`: LLaMA 2 70B
   - `gemma-7b-it`: Google's Gemma model

4. **Features**:
   - Extremely fast inference (500+ tokens/sec)
   - Large context windows
   - Free tier available

## Configuration

### Configuration File Location

Skynette stores configuration in:
- **Windows**: `C:\Users\YourName\.skynette\config.yaml`
- **macOS/Linux**: `~/.skynette/config.yaml`

### Complete Configuration Example

```yaml
# ~/.skynette/config.yaml

# General Settings
theme: dark
language: en

# AI Configuration
ai:
  # Default provider to use
  default_provider: openai

  # Fallback chain (if primary fails, try next)
  fallback_providers:
    - anthropic
    - local

  # Local Models (llama.cpp)
  local:
    model_path: ~/skynette/models/mistral-7b-instruct.gguf
    context_size: 4096
    gpu_layers: 35
    temperature: 0.7

  # Ollama
  ollama:
    base_url: http://localhost:11434
    model: mistral
    temperature: 0.7

  # OpenAI
  openai:
    api_key: sk-proj-...
    model: gpt-4-turbo-preview
    max_tokens: 4096
    temperature: 0.7

  # Anthropic
  anthropic:
    api_key: sk-ant-...
    model: claude-3-5-sonnet-20241022
    max_tokens: 4096
    temperature: 0.7

  # Google AI
  google:
    api_key: AIza...
    model: gemini-pro
    temperature: 0.7

  # Groq
  groq:
    api_key: gsk_...
    model: mixtral-8x7b-32768
    temperature: 0.7

# Storage Settings
storage:
  workflows_dir: ~/skynette/workflows
  models_dir: ~/skynette/models
  cache_dir: ~/skynette/cache

# Cloud Sync (Optional)
cloud:
  enabled: false
  sync_interval: 300
```

### Environment Variables (Alternative)

You can also use environment variables for API keys:

```bash
# .env file or system environment
export OPENAI_API_KEY=sk-proj-...
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=AIza...
export GROQ_API_KEY=gsk_...
```

Skynette will automatically detect these if not specified in config.yaml.

## Testing Your Setup

### Using Skynette UI

1. Launch Skynette
2. Go to **Settings** → **AI Providers**
3. Click **Test Connection** for each configured provider
4. Check the status indicators

### Using Skynet Assistant

1. Open the **Assistant** tab
2. Type a simple message: "Hello, can you hear me?"
3. If configured correctly, you'll receive a response

### Command Line Test

```bash
# Test OpenAI
python -c "
from src.ai.providers.openai import OpenAIProvider
provider = OpenAIProvider()
response = provider.generate('Say hello')
print(response)
"
```

## Troubleshooting

### Common Issues

#### "API Key Invalid" Error

**Problem**: Invalid or expired API key

**Solution**:
1. Verify the API key in your provider's console
2. Check for typos in config.yaml
3. Ensure no extra spaces or quotes around the key
4. Regenerate the API key if needed

#### "Connection Timeout" Error

**Problem**: Network connectivity issue

**Solution**:
1. Check your internet connection
2. Verify firewall settings allow HTTPS traffic
3. Check if the provider's service is operational
4. Try a different provider as fallback

#### Local Model "Out of Memory" Error

**Problem**: Insufficient RAM for the model

**Solution**:
1. Download a smaller quantized model (Q4 instead of Q8)
2. Reduce `context_size` in config
3. Close other memory-intensive applications
4. Use a CPU-only model if GPU memory is limited

#### "Model Not Found" Error

**Problem**: Model file doesn't exist or path is wrong

**Solution**:
1. Verify the model file path in config.yaml
2. Use absolute paths instead of relative paths
3. Check file permissions
4. Re-download the model if corrupted

### Provider-Specific Issues

#### OpenAI Rate Limits

If you hit rate limits:
1. Add delays between requests in workflows
2. Upgrade to higher tier plan
3. Use fallback providers
4. Implement request queuing

#### Anthropic Context Length

If messages are too long:
1. Reduce conversation history
2. Summarize previous context
3. Split into multiple requests
4. Use streaming for long responses

#### Local Model Performance

If inference is slow:
1. Use GPU acceleration (configure `gpu_layers`)
2. Download smaller quantized models
3. Reduce `context_size`
4. Use Groq for fast cloud inference

## Best Practices

### Cost Optimization

1. **Use Local Models First**: For development and testing
2. **Choose Appropriate Models**: GPT-3.5 for simple tasks, GPT-4 for complex
3. **Implement Caching**: Avoid redundant API calls
4. **Set Token Limits**: Prevent unexpectedly large bills
5. **Monitor Usage**: Check provider dashboards regularly

### Security

1. **Never Commit API Keys**: Use environment variables or config files (gitignored)
2. **Rotate Keys Regularly**: Change keys every few months
3. **Use Key Restrictions**: Limit keys to specific domains/IPs if available
4. **Monitor Usage**: Watch for unauthorized access
5. **Local for Sensitive Data**: Use local models for private information

### Performance

1. **Use Fallback Chains**: Ensure high availability
2. **Cache Responses**: For repeated queries
3. **Parallel Requests**: When processing multiple items
4. **Stream Long Responses**: Better UX for slow generations
5. **Choose Right Model**: Balance speed vs capability

## Getting Help

If you need assistance:
- Check [GitHub Issues](https://github.com/flyingpurplepizzaeater/Skynette/issues)
- Read the [FAQ](docs/FAQ.md)
- Join community discussions
- Open a new issue with detailed error logs

---

Last Updated: 2026-01-10
