import asyncio
from app.rag.retriever import Retriever
import json

def test():
    retriever = Retriever()
    retriever.load()
    query = "ಕಳೆದ 15 ದಿನಗಳಿಂದ ಮಳೆ ಸರಿಯಾಗಿ ಆಗಿಲ್ಲ. ಭತ್ತದ ಎಲೆಗಳ ತುದಿ ಒಣಗುತ್ತಿದೆ ಮತ್ತು ಕೆಳಗಿನ ಎಲೆಗಳು ಹಳದಿಯಾಗುತ್ತಿವೆ. ಇದು ನೀರಿನ ಕೊರತೆಯೇ ಅಥವಾ ಪೋಷಕಾಂಶದ ಕೊರತೆಯೇ ಎಂದು ಹೇಗೆ ಗುರುತಿಸುವುದು? ಭತ್ತ identification ಎಲೆಗಳ ತುದಿ ಒಣಗುವಿಕೆ ಕೆಳಗಿನ ಎಲೆಗಳು ಹಳದಿಯಾಗುವಿಕೆ"
    
    entries = retriever.retrieve(
        query=query,
        crop_name="ಭತ್ತ",
        season=None,
        region=None,
        intent="identification",
        extracted_entities={'pest_name': None, 'disease_name': None, 'fertilizer_name': None, 'pesticide_name': None}
    )
    
    print(f"Retrieved entries length: {len(entries)}")
    # Also test with top_k explicitly set to 5
    entries2 = retriever.retrieve(
        query=query,
        crop_name="ಭತ್ತ",
        top_k=5,
        season=None,
        region=None,
        intent="identification",
        extracted_entities={'pest_name': None, 'disease_name': None, 'fertilizer_name': None, 'pesticide_name': None}
    )
    print(f"Retrieved entries (top_k=5) length: {len(entries2)}")

test()
