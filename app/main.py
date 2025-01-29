from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
import logging
from .services.ai_service import AIService
from .services.hcc_service import HCCService

# Configure logging
logger = logging.getLogger(__name__)

# Get the project root directory and construct path to CSV
BASE_DIR = Path(__file__).parent.parent
HCC_CODES_PATH = BASE_DIR / "data" / "HCC_relevant_codes.csv"

app = FastAPI(title="HCC Condition Extractor API")
ai_service = AIService()
hcc_service = HCCService(str(HCC_CODES_PATH))

class ExtractionRequest(BaseModel):
    text: str

class ExtractionResponse(BaseModel):
    hcc_relevant: list[str]
    non_hcc: list[str]

@app.post("/extract-conditions", response_model=ExtractionResponse)
async def extract_conditions(request: ExtractionRequest):
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Empty text provided")

        conditions = await ai_service.extract_conditions(request.text)
        if not conditions:
            return ExtractionResponse(hcc_relevant=[], non_hcc=[])

        result = hcc_service.validate_conditions(conditions)
        return ExtractionResponse(**result)
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in extraction pipeline: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your request"
        )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
