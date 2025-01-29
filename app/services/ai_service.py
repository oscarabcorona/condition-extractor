import logging
from os import getenv
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import CommaSeparatedListOutputParser

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Get API key from environment
        google_api_key = getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.0-pro",
            google_api_key=google_api_key,  # Pass the API key directly
            temperature=0.1,
            top_p=0.8,
            max_output_tokens=1024
        )
        
        self.output_parser = CommaSeparatedListOutputParser()
        self.prompt = PromptTemplate(
            template="""Analyze the following clinical progress note and extract all medical conditions, 
            focusing specifically on the Assessment/Plan section.
            Return them as a comma-separated list. If no conditions are found, return an empty list.
            
            Clinical Note: {text}
            
            Medical Conditions:""",
            input_variables=["text"]
        )

    async def extract_conditions(self, text: str) -> list[str]:
        if not text or not text.strip():
            logger.warning("Empty or whitespace-only text provided")
            return []

        try:
            logger.debug(f"Processing text of length: {len(text)}")
            chain = self.prompt | self.llm | self.output_parser
            conditions = await chain.ainvoke({"text": text})
            
            if not conditions:
                logger.info("No conditions extracted from text")
                return []
                
            logger.info(f"Extracted {len(conditions)} conditions: {conditions}")
            return [cond.strip() for cond in conditions if cond.strip()]
        except Exception as e:
            logger.error(f"Error extracting conditions: {str(e)}", exc_info=True)
            raise
