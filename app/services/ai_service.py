from os import getenv
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import CommaSeparatedListOutputParser

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
            template="""Extract all medical conditions related to HCC from the following text. 
            Return them as a comma-separated list. If no conditions are found, return an empty list.
            
            Text: {text}
            
            Conditions:""",
            input_variables=["text"]
        )

    async def extract_conditions(self, text: str) -> list[str]:
        chain = self.prompt | self.llm | self.output_parser
        return await chain.ainvoke({"text": text})
