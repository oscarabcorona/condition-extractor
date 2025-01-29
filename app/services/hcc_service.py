import pandas as pd
import logging
from pathlib import Path
import re

logger = logging.getLogger(__name__)

class HCCService:
    def __init__(self, csv_path: str, hcc_codes_path: str = None):
        try:
            if not Path(csv_path).exists():
                raise FileNotFoundError(f"HCC data file not found at {csv_path}")
            self.hcc_data = pd.read_csv(csv_path)
            if len(self.hcc_data) == 0:
                raise ValueError("HCC data file is empty")
            self.hcc_indicators = set()
            if hcc_codes_path:
                if not Path(hcc_codes_path).exists():
                    raise FileNotFoundError(f"HCC codes file not found at {hcc_codes_path}")
                hcc_codes_df = pd.read_csv(hcc_codes_path)
                self.hcc_indicators = set(hcc_codes_df['code'].str.lower().str.strip())
                logger.info(f"Loaded {len(self.hcc_indicators)} HCC indicator codes")
            logger.info(f"Available columns in CSV: {self.hcc_data.columns.tolist()}")
            required_columns = ['ICD-10-CM Codes', 'Description']
            missing_columns = [col for col in required_columns if col not in self.hcc_data.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            self.hcc_data['condition'] = self.hcc_data['Description'].str.lower().str.strip()
            self.hcc_data['icd_code'] = self.hcc_data['ICD-10-CM Codes'].str.strip()
            
            logger.info(f"Loaded HCC data with {len(self.hcc_data)} entries")
            logger.debug(f"First few HCC conditions: {self.hcc_data['condition'].head().tolist()}")
            
        except Exception as e:
            logger.error(f"Failed to load HCC data: {str(e)}")
            raise

    def validate_conditions(self, conditions: list[str]) -> dict:
        """Validate conditions against HCC criteria"""
        if not conditions:
            logger.warning("Empty conditions list provided for HCC validation")
            return {"hcc_relevant": [], "non_hcc": []}
            
        result = {
            "hcc_relevant": [],
            "non_hcc": []
        }
        
        logger.info(f"Validating {len(conditions)} conditions for HCC relevance")
        
        for condition in conditions:
            if not condition or not isinstance(condition, str):
                logger.warning(f"Invalid condition format: {condition}")
                continue
                
            if self._is_hcc_relevant(condition):
                result["hcc_relevant"].append(condition)
            else:
                result["non_hcc"].append(condition)
        
        logger.info(f"Found {len(result['hcc_relevant'])} HCC relevant conditions")
        return result

    def _normalize_condition(self, condition: str) -> str:
        """Normalize condition text for matching."""
        condition = re.sub(r'[A-Z]\d+\.\d+:', '', condition)
        condition = re.sub(r'\s*-\s*(Stable|Improving|Unchanged|Worsening).*$', '', condition)
        condition = ' '.join(condition.lower().split())
        return condition

    def _is_hcc_relevant(self, condition: str) -> bool:
        """Check if a condition is HCC relevant using improved matching."""
        try:
            normalized_condition = self._normalize_condition(condition)
            logger.debug(f"Checking HCC relevance for normalized condition: {normalized_condition}")
            
            if self.hcc_indicators and any(indicator in normalized_condition for indicator in self.hcc_indicators):
                logger.debug(f"Found HCC indicator in condition: {normalized_condition}")
                return True
            
            for hcc_condition in self.hcc_data['condition']:
                if (normalized_condition in hcc_condition or 
                    hcc_condition in normalized_condition or
                    self._conditions_similar(normalized_condition, hcc_condition)):
                    logger.debug(f"Matched '{normalized_condition}' with HCC condition '{hcc_condition}'")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking HCC relevance for condition '{condition}': {str(e)}")
            return False

    def _conditions_similar(self, cond1: str, cond2: str) -> bool:
        """Check if two conditions are semantically similar."""
        common_words = {'due', 'to', 'with', 'without', 'and', 'or', 'the', 'a', 'an'}
        words1 = set(cond1.split()) - common_words
        words2 = set(cond2.split()) - common_words
        
        return len(words1.intersection(words2)) >= 2
