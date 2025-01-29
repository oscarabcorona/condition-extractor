# HCC Condition Extractor

An AI-powered system for extracting and evaluating HCC-relevant conditions from clinical progress notes.

## Prerequisites

- Python 3.9+
- Poetry
- Docker (optional)
- Google Cloud Service Account with Vertex AI access

## Setup Instructions

1. **Clone and Setup Environment**
    ```sh
    git clone https://github.com/yourusername/hcc-extractor.git
    cd hcc-extractor
    poetry install
    ```

2. **Configure Google Cloud API Key**
    - Create a `.env` file in the root directory
    - Add your API key:
    ```sh
    GOOGLE_API_KEY=your_api_key_here
    ```
3. **Set up Python Environment (Alternative to Docker)**
    ```sh
    # Activate virtual environment
    source env/bin/activate
    
    # Run the application
    poetry run uvicorn app.main:app --reload
    ```

3.1 **Development Server**
    ```sh
    poetry run uvicorn app.main:app --reload
    ```

4. **LangGraph Development**
    > Note: The `langgraph dev` command is currently not supported. 
    > Please refer to the LangGraph documentation for alternative development approaches.
    > You can still use the core LangGraph functionality in your application.

## Using Docker

1. **Build the Image**
    ```sh
    docker build -t hcc-extractor .
    ```

2. **Run Container with Volume Mount**
    ```sh
    docker run -v $(pwd)/output:/app/output \
               -v $(pwd)/config:/app/config \
               hcc-extractor
    ```

    Results will be available in the local `output` directory.

## Project Structure

```
hcc-extractor/
├── app/
│   ├── main.py          # FastAPI application endpoints
│   └── services/        # Core business logic
│       ├── ai_service.py    # LangGraph condition extraction
│       └── hcc_service.py   # HCC validation service 
├── data/               # Data files
│   └── HCC_relevant_codes.csv  # HCC codes reference
└── .env               # Environment variables
```
 

## Development Guidelines

1. Follow PEP 8 style guide
2. Add tests for new features
3. Update documentation for API changes
4. Use type hints and docstrings