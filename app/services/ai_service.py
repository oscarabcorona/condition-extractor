import logging
from os import getenv
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, AnyMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END, START
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

class Condition(BaseModel):
    """Schema for medical conditions extracted from clinical notes."""
    name: str = Field(..., description="Name of the medical condition")
    description: Optional[str] = Field(None, description="Additional details about the condition")

class State(BaseModel):
    """State maintained between nodes in the graph."""
    messages: List[AnyMessage]
    conditions: List[Condition]
    attempt_number: int = 0

class AIService:
    def __init__(self):
        load_dotenv()
        google_api_key = getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            google_api_key=google_api_key,
            temperature=0.1
        )

        # Create state graph
        self.graph = self._create_extraction_graph()
        
        # Update prompt to be more explicit
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a medical condition extractor specialized in analyzing clinical notes. Extract conditions from the Assessment/Plan section only.

Instructions:
1. Focus ONLY on numbered items in the Assessment/Plan section
2. Extract the primary condition from each numbered item
3. Ignore treatment plans and medication details
4. Return conditions in a clean list format
5. Remove ICD codes and other annotations

Example Assessment/Plan section:
1. Hypertension - Stable
2. Diabetes Type 2 - Improving
3. COPD - Unchanged

Expected output:
Hypertension
Diabetes Type 2
COPD"""),
            ("human", "Clinical Note: {text}")
        ])

    def _create_extraction_graph(self):
        # Create graph
        workflow = StateGraph(dict)  # Change to dict instead of State
        
        # Add nodes
        workflow.add_node("extract", self._extract_conditions)
        workflow.add_node("validate", self._validate_conditions)
        
        # Add edges
        workflow.add_edge(START, "extract")
        workflow.add_edge("extract", "validate")
        workflow.add_conditional_edges(
            "validate",
            self._should_retry,
            {
                True: "extract",
                False: END
            }
        )
        
        return workflow.compile()

    async def _extract_conditions(self, state: dict) -> dict:
        try:
            messages = state["messages"]
            if not messages:
                logger.error("No messages provided to LLM")
                return {
                    "messages": messages,
                    "conditions": [],
                    "attempt_number": state.get("attempt_number", 0) + 1
                }

            # Format message content for Gemini
            formatted_content = ""
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    formatted_content += f"Clinical Note:\n{msg.content}\n"
                elif isinstance(msg, SystemMessage):
                    formatted_content += f"Instructions:\n{msg.content}\n"

            if not formatted_content.strip():
                logger.error("No valid content to send to LLM")
                return {
                    "messages": messages,
                    "conditions": [],
                    "attempt_number": state.get("attempt_number", 0) + 1
                }

            # Create a new message with the formatted content
            llm_message = HumanMessage(content=formatted_content.strip())
            
            # Call LLM with formatted message
            response = await self.llm.ainvoke([llm_message])
            
            # Parse conditions from response
            extracted_conditions = self._parse_conditions(response)
            
            return {
                "messages": state["messages"] + [response],
                "conditions": extracted_conditions,
                "attempt_number": state.get("attempt_number", 0) + 1
            }
        except Exception as e:
            logger.error(f"Error in extraction: {str(e)}")
            return {
                "messages": state.get("messages", []),
                "conditions": [],
                "attempt_number": state.get("attempt_number", 0) + 1
            }

    def _validate_conditions(self, state: dict) -> dict:
        try:
            # Validate extracted conditions
            valid_conditions = [
                condition for condition in state["conditions"] 
                if self._is_valid_condition(condition)
            ]
            
            if not valid_conditions and state["attempt_number"] >= 3:
                logger.warning("No valid conditions found after maximum attempts")
            
            return {
                "messages": state["messages"],
                "conditions": valid_conditions,
                "attempt_number": state["attempt_number"]
            }
        except Exception as e:
            logger.error(f"Error in condition validation: {str(e)}")
            return {
                "messages": state["messages"],
                "conditions": [],
                "attempt_number": state["attempt_number"]
            }

    def _should_retry(self, state: dict) -> bool:
        return (
            len(state.get("conditions", [])) == 0 and 
            state.get("attempt_number", 0) < 3
        )

    def _parse_conditions(self, message: AIMessage) -> List[Condition]:
        """Parse conditions from LLM response.
        
        Args:
            message: AIMessage containing the response from the LLM
            
        Returns:
            List[Condition]: List of parsed conditions
        """
        try:
            if not isinstance(message, AIMessage) or not isinstance(message.content, str):
                return []

            conditions = []
            for line in message.content.strip().split('\n'):
                line = line.strip()
                if line:
                    # Clean up the condition name
                    name = line.split('-')[0].strip()  # Remove status indicators
                    name = name.split(':')[0].strip()  # Remove any colons
                    if any(char.isalpha() for char in name):
                        conditions.append(Condition(
                            name=name,
                            description=None
                        ))

            return conditions

        except Exception as e:
            logger.error(f"Error parsing conditions: {str(e)}")
            return []

    def _is_valid_condition(self, condition: Condition) -> bool:
        """Validate if the condition name is properly formatted."""
        if not condition.name:
            return False
            
        # Must be between 3 and 100 characters
        if not (3 <= len(condition.name) <= 100):
            return False
            
        # Must contain letters
        if not any(c.isalpha() for c in condition.name):
            return False
            
        return True

    async def extract_conditions(self, text: str) -> list[str]:
        if not text or not text.strip():
            logger.warning("Empty or whitespace-only text provided")
            return []

        try:
            # Initialize state with properly formatted messages
            formatted_messages = self.prompt.format_messages(text=text)
            initial_state = {
                "messages": formatted_messages,
                "conditions": [],
                "attempt_number": 0
            }
            
            # Run graph
            final_state = await self.graph.ainvoke(initial_state)
            
            # Return condition names from final state
            return [c.name for c in final_state.get("conditions", [])]
            
        except Exception as e:
            logger.error(f"Error extracting conditions: {str(e)}", exc_info=True)
            raise
