# Docs Writer - AI-Powered Thesis Writing System

An intelligent thesis writing system built with CrewAI and Django that automates the research, outlining, and writing process for academic documents.

## Features

- **Automated Research**: Conducts comprehensive academic research using multiple search tools and PDF readers
- **Intelligent Outlining**: Creates well-structured thesis outlines based on research findings
- **Section-by-Section Writing**: Writes comprehensive, detailed content for each section and subsection
- **MDX Format Support**: Outputs content in Markdown Extended (MDX) format
- **Citation Management**: Supports multiple citation styles (APA, MLA, Chicago, etc.)
- **Quality Guardrails**: Ensures minimum source requirements and word count targets
- **Django Backend**: RESTful API for managing projects and user accounts

## Architecture

The system uses a CrewAI Flow with three main stages:

1. **Research Stage** (`crews/researcher.py`): Finds and analyzes academic sources
2. **Outlining Stage** (`crews/outliner.py`): Creates structured thesis outline
3. **Writing Stage** (`crews/writer.py`): Writes comprehensive content for each section

The Django backend provides API endpoints for managing thesis projects, user authentication, and storing results.

### CrewAI Project Tools

Each crew now has access to purpose-built tools located in `crews/tools/project_model_tools.py`:

- `project_research_save_tool` – Persists research summaries and source lists while moving the project into the `researching` status.
- `project_outline_save_tool` – Saves structured outlines (including nested sections) and marks the project as `outlined`.
- `project_section_save_tool` – Stores written sections, supports hierarchical content, and updates the project status to `writing` or `completed`.
- `project_status_update_tool` – Allows any agent to explicitly update the project status if additional workflow states are needed.
- `project_lookup_tool` – Lightweight helper for validating project IDs and fetching context.

These tools ensure that every step of the CrewAI pipeline keeps the Django project models in sync, enabling real-time progress tracking across research, outlining, and writing phases.

## Prerequisites

- Python 3.8+
- OpenAI API key
- Serper API key (for internet search)
- BrightData API key and zone (optional, for web scraping)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd docs-writer
```

2. Create a virtual environment:
```bash
python -m venv .venv
```

3. Activate the virtual environment:
```bash
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Create a `.env` file in the root directory:
```env
OPENAI_API_KEY=your_openai_api_key_here
SERPER_API_KEY=your_serper_api_key_here
BRIGHT_DATA_API_KEY=your_brightdata_api_key_here
BRIGHT_DATA_ZONE=your_brightdata_zone_here
SECRET_KEY=your_django_secret_key_here
```

6. Set up the Django database:
```bash
python manage.py migrate
```

7. (Optional) Create a Django superuser:
```bash
python manage.py createsuperuser
```

## Usage

### Running the CrewAI Flow Directly

Run the main flow:

```bash
python -m crews.main
```

Or directly:

```bash
python crews/main.py
```

### Customizing the Project

Edit `crews/main.py` to customize the topic and citation style:

```python
if __name__ == "__main__":
    project = ProjectInfo(
        topic="Your research topic here",
        citation_style="APA"  # or "MLA", "Chicago", etc.
    )
    asyncio.run(run_flow(project))
```

### Running the Django Server

Start the Django development server:

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/`

## Project Structure

```
docs-writer/
├── accounts/              # Django app for user authentication
│   ├── models.py
│   ├── views.py
│   └── ...
├── config/                # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── crews/                 # CrewAI agents and flows
│   ├── main.py            # Main flow orchestration
│   ├── researcher.py      # Research agent and crew
│   ├── outliner.py        # Outline generation agent and crew
│   ├── writer.py          # Writing agent and crew
│   └── tools/
│       └── main.py        # Custom tools (PDF reader, web scraper)
├── projects/              # Django app for thesis projects
│   ├── models.py
│   ├── views.py
│   └── ...
├── manage.py              # Django management script
├── .env                   # Environment variables (not in git)
├── .gitignore
├── requirements.txt
└── README.md
```

## How It Works

### 1. Research Phase
- Searches the internet for academic sources using SerperDev
- Scrapes content from academic websites using BrightData
- Reads and extracts content from PDF documents
- Analyzes sources for relevance and quality
- Generates citations in the specified style
- **Requirement**: Must find at least 10 sources (will automatically refine search if needed)

### 2. Outlining Phase
- Analyzes research findings
- Creates structured outline with sections and subsections
- Estimates word counts for each section
- Provides rationale for structure
- Top-level sections have empty `parent_section` field

### 3. Writing Phase
- Writes one section at a time (including all subsections)
- Produces comprehensive, detailed content (not summaries)
- Uses MDX format for rich formatting
- Ensures word counts meet or exceed targets (aims for 120-150% of minimum)
- Properly cites sources throughout

## Output Format

The system outputs content in MDX (Markdown Extended) format with the following structure:

```json
{
  "section": {
    "section_title": "Introduction",
    "section_type": "introduction",
    "content": "MDX formatted content...",
    "word_count": 180,
    "subsections": [
      {
        "section_title": "Background",
        "parent_section": "Introduction",
        "section_type": "subsection",
        "content": "MDX formatted content...",
        "word_count": 540
      }
    ]
  },
  "total_word_count": 720,
  "writing_notes": "..."
}
```

## Configuration

### Models
- Research: `gpt-4o-mini` (configurable in `crews/researcher.py`)
- Outlining: `gpt-4o-mini` (configurable in `crews/outliner.py`)
- Writing: `gpt-4o` (configurable in `crews/writer.py`)

### Word Count Targets
The system respects word count targets from the outline and aims to exceed them by 20-50% for comprehensive coverage.

### Django Settings
- Database: SQLite (default, can be changed in `config/settings.py`)
- Django Version: 5.2.8
- REST Framework: Available for API endpoints

## API Endpoints

The Django backend provides REST API endpoints (when configured):
- User authentication endpoints
- Project management endpoints
- Thesis document endpoints

## Troubleshooting

### Tools Not Working
- Ensure all API keys are set in `.env`
- Check that tools are assigned to the agent (not just the task)
- Verify API key permissions and quotas
- Check the debug output: `Research tools loaded: [...]`

### Low Source Count
- The system will automatically refine search queries if fewer than 10 sources are found
- Check that Serper API key is valid and has credits
- Verify internet connectivity

### Word Count Issues
- The system aims for 120-150% of target word counts
- If content is too short, check the outline's word count estimates
- Ensure the writing agent is configured to write comprehensively

### Django Issues
- Run migrations: `python manage.py migrate`
- Check Django settings in `config/settings.py`
- Verify database connection

### Dependency Conflicts
- Ensure Django version is >= 4.2 (required by django-cors-headers)
- Remove `djongo` if not using MongoDB (it conflicts with modern Django)
- Use `pip install -r requirements.txt` to install all dependencies

## Development

### Running Tests
```bash
python manage.py test
```

### Creating Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Deactivating Virtual Environment
```bash
# Windows (Git Bash)
deactivate

# Or simply close the terminal
```

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

[Add support information here]
