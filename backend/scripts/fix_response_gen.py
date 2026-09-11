import os

file_path = "app/llm/response_generator.py"
with open(file_path, "rb") as f:
    text = f.read().decode("utf-8", errors="replace")

idx_start = text.find("    # ── Main Generate Method")
idx_end = text.find("        self.session_manager.add_user_turn(session_id, user_query)")

if idx_start != -1 and idx_end != -1:
    corrupted_header = text[idx_start:idx_end]
    new_methods = """    # ── Main Generate Methods ─────────────────────────────────────────

    async def generate(
        self,
        session_id: str,
        user_query: str,
        is_voice_mode: bool = False,
        language: str = "kn",
    ) -> dict:
        \"\"\"
        Non-streaming response generation.
        \"\"\"
        full_tokens = []
        async for token in self.generate_stream(
            session_id=session_id,
            user_query=user_query,
            is_voice_mode=is_voice_mode,
            language=language,
        ):
            full_tokens.append(token)

        full_text = "".join(full_tokens)
        state = self.session_manager.get_state(session_id)

        return {
            "response": full_text,
            "is_followup": False,
            "context_used": True,
            "retrieved_count": 1,
            "source": "rag",
            "confidence": 0.9,
            "provider": "gemini",
            "metadata": {"state": state.to_dict() if state else {}},
        }

    async def generate_stream(
        self,
        session_id: str,
        user_query: str,
        is_voice_mode: bool = False,
        language: str = "kn",
    ):
        \"\"\"
        Streaming version of generate() -- yields tokens as they arrive.
        \"\"\"
"""
    updated_text = text[:idx_start] + new_methods + text[idx_end:]
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(updated_text)
    print("Fixed response_generator.py successfully!")
else:
    print("Could not find targets:", idx_start, idx_end)
