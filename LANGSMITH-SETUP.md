# LangSmith Integration Guide

This project has been integrated with LangSmith for comprehensive AI tracing, monitoring, and debugging.

## What is LangSmith?

LangSmith is a platform for debugging, testing, and monitoring LLM applications. It provides:
- **Tracing**: Track every step of your LLM chain execution
- **Debugging**: Identify bottlenecks and errors in real-time
- **Monitoring**: Track costs, latency, and performance metrics
- **Testing**: Evaluate and compare different prompts and models

## Setup Instructions

### 1. Get Your LangSmith API Key

1. Sign up for a free account at [smith.langchain.com](https://smith.langchain.com/)
2. Navigate to Settings → API Keys
3. Create a new API key and copy it

### 2. Configure Environment Variables

Add the following to your `.env.local` file (or copy from `.env.example`):

```bash
# LangSmith Configuration
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
LANGCHAIN_API_KEY="your_langsmith_api_key_here"
LANGCHAIN_PROJECT="gdrive-clone"
```

**Important**: 
- Set `LANGCHAIN_TRACING_V2="true"` to enable tracing
- Set `LANGCHAIN_TRACING_V2="false"` to disable tracing (no impact on functionality)
- Replace `your_langsmith_api_key_here` with your actual API key
- You can customize `LANGCHAIN_PROJECT` to organize traces by project name

### 3. Install Dependencies

#### For Python (ai-agent):
```bash
cd ai-agent
pip install -r requirements.txt
```

The `langsmith` package is already included in `requirements.txt`.

#### For Next.js:
```bash
npm install
```

No additional LangSmith packages needed for Next.js - all tracing is handled by the Python agent to avoid duplicate traces.

### 4. Restart Your Services

After configuring environment variables:

**Python Agent:**
```bash
cd ai-agent
uvicorn main:app --reload
```

**Next.js App:**
```bash
npm run dev
```

You should see a message in the Python console:
- `🔍 LangSmith tracing enabled - Project: gdrive-clone` (if enabled)
- `ℹ️  LangSmith tracing disabled` (if disabled)

## What Gets Traced?

### Python Agent (ai-agent/)

The LangGraph agent automatically traces:
- **LLM calls** (Gemini model invocations)
- **Tool executions** (file operations, searches, etc.)
- **Agent state transitions** (graph nodes and edges)
- **Streaming responses**

Each trace includes:
- User ID and email for request attribution
- Input messages and parameters
- Tool call details and results
- Error messages and stack traces
- Latency metrics

### Next.js API Route (app/api/chat/route.ts)

The Next.js chat API creates parent traces that include:
- HTTP request metadata
- User session information
- Request/response timing
- Error handling

## Viewing Traces in LangSmith

1. Go to [smith.langchain.com](https://smith.langchain.com/)
2. Select your project (e.g., "gdrive-clone")
3. View the traces dashboard with:
   - Request timeline
   - Token usage and costs
   - Latency breakdown
   - Error rates
   - User-specific filters

### Trace Details

Click on any trace to see:
- **Input/Output**: Full message history and responses
- **Metadata**: userId, userEmail, message preview
- **Steps**: Each LLM call and tool invocation
- **Timing**: Latency for each component
- **Tokens**: Input/output token counts
- **Errors**: Stack traces and error messages

## Advanced Features

### Custom Tags and Metadata

The integration automatically adds:
- Tags: `["chat-endpoint", "gdrive-clone"]`
- Metadata: `userId`, `userEmail`, `message_preview`

You can extend this in `ai-agent/main.py` by modifying the `langsmith_config` object.

### Filtering Traces

In the LangSmith UI, you can filter by:
- User ID or email
- Date range
- Success/failure status
- Latency threshold
- Tags

### Cost Tracking

LangSmith automatically tracks token usage and estimates costs based on your model pricing.

## Troubleshooting

### Tracing Not Working?

1. **Verify environment variables are set correctly:**
   ```bash
   # In Python
   python -c "import os; print(os.getenv('LANGCHAIN_TRACING_V2'))"
   
   # Check Next.js env vars are available
   ```

2. **Check API key validity:**
   - Ensure the API key is active in LangSmith settings
   - Verify no extra spaces or quotes in the `.env.local` file

3. **Network issues:**
   - Ensure your server can reach `https://api.smith.langchain.com`
   - Check firewall settings

4. **Check console logs:**
   - Python: Look for "LangSmith tracing enabled" message
   - Next.js: Check for LangSmith-related errors in the browser console

### Performance Impact

LangSmith tracing adds minimal overhead:
- ~10-50ms per request
- Async logging (non-blocking)
- No impact on user-facing latency

To disable tracing without code changes, simply set:
```bash
LANGCHAIN_TRACING_V2="false"
```

## Production Deployment

### Environment Variables

Ensure these environment variables are set in your production environment:

**Vercel (Next.js):**
1. Go to Project Settings → Environment Variables
2. Add `LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`, `LANGCHAIN_ENDPOINT`, `LANGCHAIN_PROJECT`

**Render (Python Agent):**
1. Go to Environment → Environment Variables
2. Add the same variables

### Security Best Practices

- **Never commit** `.env.local` or `.env` files to version control
- Use separate LangSmith projects for dev/staging/production
- Rotate API keys regularly
- Use environment-specific API keys if possible

## Support

- LangSmith Docs: https://docs.smith.langchain.com/
- LangChain Discord: https://discord.gg/langchain
- GitHub Issues: Report issues in this repository

## Cost Considerations

LangSmith offers:
- **Free Tier**: 5,000 traces/month
- **Developer Tier**: $39/month for 50,000 traces
- **Team Tier**: Custom pricing

For most development and small-scale production, the free tier is sufficient.
