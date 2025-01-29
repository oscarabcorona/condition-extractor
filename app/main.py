from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .services.ai_service import AIService

app = FastAPI(title="Condition Extractor API")
ai_service = AIService()

class ExtractionRequest(BaseModel):
    text: str

class ExtractionResponse(BaseModel):
    conditions: list[str]

@app.post("/extract-conditions", response_model=ExtractionResponse)
async def extract_conditions(request: ExtractionRequest):
    try:
        conditions = await ai_service.extract_conditions(request.text)
        return ExtractionResponse(conditions=conditions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
