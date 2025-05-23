# WebScraper-Automated Mailer(Using Lang-Chain and SMTP)

An automated lead generation and personalized email outreach service powered by LangChain and LLMs. This tool helps freelancers and service providers find potential clients, analyze their needs, and create personalized outreach emails.

## Features

- Lead discovery through targeted web searches
- Data extraction and filtering for relevant contact information
- Content analysis using LLMs to identify client needs
- Automated email generation tailored to each prospect
- Flexible system that works for any type of service provider
- API for integration with other services
- Google profile search to avoid captchas and bans

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your API keys (copy from env-example):
   ```
   OPENAI_API_KEY=your_openai_key
   SERPAPI_API_KEY=your_serpapi_key
   SERVICE_TYPE=your_service_type
   # Or for local LLMs
   USE_LOCAL_LLM=true
   OLLAMA_BASE_URL=http://localhost:11434
   # For Google profile search
   SEARCH_METHOD=google_profile
   GOOGLE_PROFILE_PATH=path/to/your/chrome/profile
   ```

4. For Google profile search setup, see [GOOGLE_PROFILE_SETUP.md](GOOGLE_PROFILE_SETUP.md)
5. For local LLM setup with LM Studio, see [LM_STUDIO_SETUP.md](LM_STUDIO_SETUP.md)

## Usage

### Command Line Interface

Search for leads:
```
python main.py search --keywords "dentist" --platform "instagram.com" --location "New York" --limit 5 --output leads.json
```

Analyze leads:
```
python main.py analyze --input leads.json --service-type "web_development" --output analyzed_leads.json
```

Generate emails:
```
python main.py email --input analyzed_leads.json --service-type "web_development" --output emails.json
```

Start the API server:
```
python main.py api --service-type "web_development"
```

### API Usage

The API provides endpoints for searching leads, analyzing them, and generating personalized emails. You can interact with it using tools like curl, Postman, or directly from your application.

Example API request:
```
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"keywords": "dentist", "platform": "instagram.com", "location": "New York", "limit": 5}'
```

## How It Works

1. **Lead Finding**: The system searches for potential leads based on keywords, platform, and location using either:
   - Google search with a logged-in profile (recommended)
   - SerpAPI (if API key provided)
   - Mock implementations for platform-specific searches (fallback)
2. **Data Preprocessing**: Extracts emails, social handles, and other relevant information
3. **Lead Analysis**: Uses LLMs to analyze the lead's website and social profiles to identify needs and opportunities
4. **Email Generation**: Creates personalized emails based on the analysis, tailored to the specific service you offer

## Search Methods

### Google Profile Search (Recommended)
- Uses a logged-in Google Chrome profile to avoid captchas
- Requires setting up a Chrome profile (see [GOOGLE_PROFILE_SETUP.md](GOOGLE_PROFILE_SETUP.md))
- Most reliable for regular use

### SerpAPI
- Uses the SerpAPI service (requires API key)
- Costs money for each search
- Good for occasional use

### Fallback Methods
- Mock implementations for platform-specific searches
- Business directory listings
- Limited but free

## Project Structure

- `main.py`: Entry point for the application
- `lead_finder.py`: Search and extract potential leads
- `lead_analyzer.py`: Analyze leads and gather relevant information
- `email_generator.py`: Generate personalized emails
- `api.py`: FastAPI server for API access
- `templates/`: Email templates
- `utils/`: Utility functions

## Customization

You can customize the system for any type of service by specifying the `service_type` parameter. Some examples include:
- web_development
- graphic_design
- content_writing
- digital_marketing
- seo
- social_media_management
- video_editing
- photography
- consulting
- coaching

The system will adapt its analysis and email generation to match your specific service type. 
