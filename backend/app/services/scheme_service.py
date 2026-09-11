import json
import os
from app.config import settings

class SchemeService:
    def __init__(self):
        self.schemes = []
        try:
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'database', 'schemes.json')
            with open(db_path, 'r', encoding='utf-8') as f:
                self.schemes = json.load(f)
        except Exception as e:
            from app.utils.logger import logger
            logger.error(f"Failed to load schemes.json: {e}")

    def get_schemes_context(self) -> str:
        """
        Returns the entire schemes database as a formatted string to inject into the prompt.
        The LLM will match the user's condition to the best scheme.
        """
        if not self.schemes:
            return "No government schemes currently available in the database."
            
        context = "Verified Government Agricultural Schemes:\n"
        for idx, scheme in enumerate(self.schemes, 1):
            context += f"\n{idx}. Name: {scheme['scheme_name']}\n"
            context += f"   Description: {scheme['description']}\n"
            context += f"   Eligibility: {scheme['eligibility']}\n"
            context += f"   Benefits: {scheme['benefits']}\n"
            context += f"   How to Apply: {scheme['application_process']}\n"
            
        return context
