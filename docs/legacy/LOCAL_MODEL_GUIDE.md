# Local GGUF Model Support – AnomFIN/JugiAI

This guide explains how to use local GGUF models with JugiAI for offline, on-device AI inference.

## Overview

JugiAI now supports running local GGUF models via `llama-cpp-python`, providing:

- **Offline Operation**: No internet connection required
- **GPU Acceleration**: Automatic GPU detection with CPU fallback
- **Privacy**: Your data never leaves your machine
- **Cost Savings**: No API fees for local inference
- **Flexibility**: Use any GGUF-compatible model

## Installation

### Basic Setup (CPU Only)

The `install.bat` script will prompt you to install llama-cpp-python:

```cmd
install.bat
```

When prompted, choose `Y` to install local model support. This installs the CPU-only version by default.

### GPU Acceleration (Optional)

For NVIDIA GPU acceleration (CUDA), after running `install.bat`, upgrade to a CUDA-enabled wheel:

```cmd
.\.venv\Scripts\activate.bat
python -m pip install llama-cpp-python --force-reinstall --no-cache-dir --extra-index-url https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu121
```

Replace `cu121` with your CUDA version (e.g., `cu118` for CUDA 11.8).

## Configuration

### Quick Start

1. Open JugiAI
2. Click the ⚙️ (Settings) icon
3. Go to the "Paikallinen" (Local) tab
4. Click "Valitse…" to select your `.gguf` model file
5. Set "Taustajärjestelmä" to "local"
6. Click "Tallenna" (Save)

### Configuration Parameters

All parameters are configurable in Settings → Paikallinen tab:

| Parameter | Default | Description |
|-----------|---------|-------------|
| **Paikallinen malli (.gguf)** | (empty) | Path to your GGUF model file |
| **Säikeet** | 0 (auto) | Number of CPU threads. 0 = auto-detect |
| **Kontekstin koko (n_ctx)** | 4096 | Context window size in tokens |
| **Eräkoko (n_batch)** | 256 | Batch size for prompt processing |
| **GPU-tasot (n_gpu_layers)** | -1 (auto) | Number of model layers to offload to GPU<br>-1 = auto (GPU if available)<br>0 = CPU only<br>>0 = specific number of layers |
| **Käytä GPU-kiihdytystä** | ✓ | Master switch for GPU acceleration |
| **Max tokeneja** | (empty) | Max tokens per completion (empty = model decides) |
| **Siemen (seed)** | (empty) | Random seed for reproducible outputs (empty = random) |

### Advanced: config.json

You can also edit `config.json` directly:

```json
{
  "backend": "local",
  "local_model_path": "C:\\Models\\llama-3-8b-instruct.Q5_K_M.gguf",
  "local_threads": 0,
  "local_n_ctx": 8192,
  "local_n_batch": 512,
  "local_gpu_layers": 35,
  "local_max_tokens": 2048,
  "local_seed": null,
  "local_rope_scale": null,
  "prefer_gpu": true
}
```

## Obtaining GGUF Models

### Recommended Sources

1. **Hugging Face**: Search for GGUF models
   - Example: [TheBloke/Llama-2-7B-Chat-GGUF](https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF)
   - Look for files ending in `.gguf`

2. **Popular Model Series**:
   - **Llama 3**: High quality, instruction-tuned
   - **Mistral**: Excellent performance for size
   - **Phi-3**: Microsoft's small but capable models
   - **Gemma**: Google's open models

### Choosing Quantization

GGUF models come in different quantization levels. Balance quality vs. size:

| Quantization | Quality | File Size | VRAM Usage | Use Case |
|--------------|---------|-----------|------------|----------|
| **Q2_K** | Lower | Smallest | Minimal | Testing, low-end hardware |
| **Q4_K_M** | Good | Medium | Moderate | Recommended for most users |
| **Q5_K_M** | Better | Larger | Higher | Good balance |
| **Q8_0** | Excellent | Large | High | High-quality, lots of VRAM |

Example filename: `llama-3-8b-instruct.Q5_K_M.gguf`

## Performance Tuning

### Thread Count

- **0 (Auto)**: Recommended for most users
- **Manual**: Set to 4-8 for typical CPUs
- **Warning**: Exceeds 4× CPU core count will be capped automatically

### Context Window

- **2048**: Minimum for basic conversations
- **4096**: Default, good for most use cases
- **8192+**: Extended conversations, requires more RAM/VRAM

### GPU Layers

#### Finding the Right Value

1. Start with `-1` (auto)
2. If you see a GPU warning, check your CUDA installation
3. Monitor VRAM usage:
   - 6GB VRAM: Try 20-25 layers
   - 8GB VRAM: Try 30-35 layers
   - 12GB+ VRAM: Use all layers (-1)

#### GPU vs CPU Comparison

- **GPU Mode**: 10-50x faster inference
- **CPU Mode**: Slower but works everywhere

### Memory Requirements

Approximate VRAM/RAM needed by model size:

| Model Size | Q4_K_M VRAM | Q5_K_M VRAM | Q8_0 VRAM |
|------------|-------------|-------------|-----------|
| 7B params  | ~4GB        | ~5GB        | ~7GB      |
| 13B params | ~8GB        | ~10GB       | ~14GB     |
| 70B params | ~40GB       | ~50GB       | ~70GB     |

Add 1-2GB for context window overhead.

## Troubleshooting

### "Paikallista mallia ei voitu alustaa"

**Issue**: llama-cpp-python not installed or import failed

**Solution**:
```cmd
.\.venv\Scripts\activate.bat
python -m pip install --upgrade --prefer-binary llama-cpp-python
```

### GPU Initialization Failed

**Issue**: GPU attempted but failed, app falls back to CPU

**Causes**:
1. CPU-only wheel installed (no CUDA support)
2. CUDA version mismatch
3. Insufficient VRAM

**Solution**:
1. Install CUDA-enabled wheel (see GPU Acceleration section)
2. Match your CUDA version (check with `nvidia-smi`)
3. Reduce `local_gpu_layers` or use a smaller model

### Out of Memory

**Issue**: Model loading fails or crashes

**Solutions**:
- Use a smaller model
- Choose a more aggressive quantization (Q4_K_M instead of Q5_K_M)
- Reduce `local_n_ctx`
- Reduce `local_gpu_layers` or set to 0 (CPU mode)
- Close other applications

### Slow Inference

**Issue**: Model generates text slowly

**Solutions**:
- **Enable GPU**: Install CUDA wheel and set `local_gpu_layers > 0`
- **Increase threads**: Try `local_threads = 8` for CPU inference
- **Smaller model**: Use a 7B model instead of 13B
- **Better quantization**: Q4_K_M is faster than Q8_0

### Context Trimming Warning

**Issue**: "Trimmed N oldest message(s) to fit context window"

**Explanation**: Your conversation exceeded `local_n_ctx`. Oldest messages were removed to stay within limits.

**Solutions**:
- Increase `local_n_ctx` (requires more VRAM/RAM)
- Start a new conversation periodically
- This is normal for long conversations

## Feature Comparison

| Feature | OpenAI Backend | Local Backend |
|---------|----------------|---------------|
| Internet Required | Yes | No |
| API Costs | Yes | No |
| Privacy | Data sent to OpenAI | Data stays local |
| Speed | Fast (usually) | Depends on hardware |
| Setup Complexity | Easy (API key) | Moderate (model download) |
| Model Selection | OpenAI models only | Any GGUF model |

## Best Practices

1. **Start Small**: Test with a 7B Q4_K_M model first
2. **Monitor Resources**: Watch CPU/GPU/RAM usage in Task Manager
3. **Update Regularly**: Keep llama-cpp-python updated for bug fixes and performance improvements
4. **Test GPU**: Verify GPU mode is working by checking logs (GPU status shown in settings)
5. **Backup Configs**: Save your `config.json` before experimenting

## Support

For issues specific to:
- **JugiAI integration**: Open an issue on [AnomFIN/AnomAI](https://github.com/AnomFIN/AnomAI/issues)
- **llama-cpp-python**: See [abetlen/llama-cpp-python](https://github.com/abetlen/llama-cpp-python)
- **GGUF models**: Check the model's Hugging Face page

## Security Summary

All code changes have been validated with CodeQL with **0 security alerts**.

- No credentials or sensitive data are stored insecurely
- Model files are read-only operations
- Local inference keeps your data private
- GPU fallback prevents application crashes

---

**AnomFIN · Älykkyyden käyttöönotto**
