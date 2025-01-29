import pandas as pd
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class HCCService:
    def __init__(self, csv_path: str):
        try:
            if not Path(csv_path).exists():
                raise FileNotFoundError(f"HCC data file not found at {csv_path}")
            self.hcc_data = pd.read_csv(csv_path)
            if len(self.hcc_data) == 0:
                raise ValueError("HCC data file is empty")
            logger.info(f"Loaded HCC data with {len(self.hcc_data)} entries")
        except Exception as e:
            logger.error(f"Failed to load HCC data: {str(e)}")
            raise

    def validate_conditions(self, conditions: list[str]) -> dict:
        """Validate conditions against HCC criteria"""
        result = {
            "hcc_relevant": [],
            "non_hcc": []
        }
        
        for condition in conditions:
            if self._is_hcc_relevant(condition):
                result["hcc_relevant"].append(condition)
            else:
                result["non_hcc"].append(condition)
        
        return result

    def _is_hcc_relevant(self, condition: str) -> bool:
        try:
            return condition.lower() in self.hcc_data['condition'].str.lower().values
        except Exception as e:
            logger.error(f"Error checking HCC relevance for condition '{condition}': {str(e)}")
            return False
