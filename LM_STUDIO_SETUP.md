# Setting Up LM Studio for LangChain AutoMailer

This guide will help you set up LM Studio to work with the LangChain AutoMailer application.

## What is LM Studio?

LM Studio is a desktop application that allows you to run powerful large language models (LLMs) locally on your computer. It provides a user-friendly interface for downloading, managing, and running various open-source LLMs.

## Installation Steps

1. **Download LM Studio**
   - Visit [LM Studio's website](https://lmstudio.ai/) and download the application for your operating system (Windows, macOS, or Linux).
   - Install the application following the standard installation process for your OS.

2. **Install a Compatible Model**
   - Open LM Studio after installation.
   - Navigate to the "Models" tab.
   - Search for "DeepSeek Qwen 7B" or any other model you prefer.
   - Click "Download" to install the model locally.
   - Wait for the download to complete (this may take some time depending on your internet connection).

3. **Start the Local Server**
   - After downloading the model, go to the "Local Server" tab in LM Studio.
   - Select the downloaded model from the dropdown menu.
   - Click "Start Server" to launch the API server.
   - The server should start running on `http://localhost:1234/v1` by default.
   - You should see a message indicating that the server is running.

## Configuring LangChain AutoMailer to Use LM Studio

When you run the LangChain AutoMailer application, follow these steps:

1. When prompted "Do you want to use a local LLM instead of OpenAI?", select **Yes**.
2. When asked which local LLM provider to use, select **lm_studio**.
3. Verify that LM Studio is running with a model loaded.
4. The default URL is `http://localhost:1234/v1`. If you've configured LM Studio to use a different port, enter that URL when prompted.

## Troubleshooting

- **Server Connection Issues**: Ensure that LM Studio's server is running before starting the LangChain AutoMailer application.
- **Memory Issues**: If you encounter out-of-memory errors, try using a smaller model or adjust the model settings in LM Studio (reduce context length or batch size).
- **Slow Responses**: Local LLMs can be slower than cloud-based ones, especially on computers without powerful GPUs. Be patient during processing.
- **API Errors**: Make sure you're using the correct API URL. You can check this in the LM Studio interface under the "Local Server" tab.

## Recommended Models for LangChain AutoMailer

The following models work well with our application:

- **DeepSeek Qwen 7B**: Good balance of performance and resource usage
- **Mistral 7B**: Excellent for text generation tasks
- **Llama 2 7B**: Good general-purpose model
- **Vicuna 13B**: Higher quality but requires more resources

Choose a model based on your computer's specifications and the quality of responses you need.

## System Requirements

To run LLMs locally with LM Studio, your computer should have:

- **CPU**: Modern multi-core processor
- **RAM**: At least 16GB (32GB recommended for larger models)
- **GPU**: NVIDIA GPU with 8GB+ VRAM for optimal performance
- **Storage**: At least 10GB of free space for models

## Additional Resources

- [LM Studio Documentation](https://lmstudio.ai/docs)
- [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction)
- [DeepSeek Qwen Model Information](https://huggingface.co/deepseek-ai/deepseek-llm-7b-chat) 