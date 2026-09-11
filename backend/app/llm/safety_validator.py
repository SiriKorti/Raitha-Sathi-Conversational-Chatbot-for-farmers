import json
import re
from app.utils.logger import logger
from app.conversation.dialogue_state import DialogueState

class SafetyValidator:
    """
    Validates generated LLM responses to ensure agricultural safety.
    Checks for crop consistency and prevents dosage hallucination.
    """
    def __init__(self, call_llm_fn):
        self.call_llm_fn = call_llm_fn

    async def validate_response(self, generated_response: str, context: str, state: DialogueState) -> str:
        """
        Validate the generated response against the context.
        If hallucinated dosages or mismatched crops are found, redacts or warns.
        """
        if not context:
            # If there's no context, we can't verify dosages. We just return it.
            # (The response generator should have already added an unverified warning).
            return generated_response

        prompt = (
            "You are an agricultural safety validator.\n"
            "Review the GENERATED_RESPONSE against the VERIFIED_CONTEXT.\n\n"
            f"=== VERIFIED_CONTEXT ===\n{context}\n\n"
            f"=== GENERATED_RESPONSE ===\n{generated_response}\n\n"
            "Check for the following FATAL violations:\n"
            "1. CROP MISMATCH: Does the response give advice for a different crop than the context?\n"
            "2. DOSAGE HALLUCINATION: Does the response contain chemical dosages, quantities, or prices that are NOT explicitly stated in the context?\n\n"
            "Respond in JSON format ONLY:\n"
            "{\n"
            "  \"is_safe\": true/false,\n"
            "  \"violation_reason\": \"Explanation if false, else null\"\n"
            "}\n"
        )

        try:
            raw_eval, _ = await self.call_llm_fn(prompt)
            match = re.search(r"\{.*\}", raw_eval, re.DOTALL)
            if match:
                eval_json = json.loads(match.group(0))
                if not eval_json.get("is_safe", True):
                    logger.warning(f"Safety Violation Detected: {eval_json.get('violation_reason')}")
                    warning_msg = (
                        "\n\n⚠️ **SAFETY WARNING / ಎಚ್ಚರಿಕೆ**\n"
                        "This response was flagged by our safety system for potentially containing unverified chemical dosages or crop mismatches. "
                        "Please verify all chemical quantities with an expert before application."
                    )
                    return generated_response + warning_msg
        except Exception as e:
            logger.error(f"Safety validation failed: {e}")
            
        return generated_response
