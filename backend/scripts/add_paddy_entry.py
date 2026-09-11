import json

path = "database/rice_qa_kannada.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

new_entry = {
    "id": len(data) + 1,
    "crop_name": "ಭತ್ತ (Rice / Paddy)",
    "crop_type": "Cereal Crop",
    "language": "kn",
    "region": "Karnataka",
    "season": "Kharif / Rabi",
    "topic": "ರೋಗ ಮತ್ತು ಪೋಷಕಾಂಶ ನಿರ್ವಹಣೆ",
    "subtopic": "Diagnostic",
    "query_type": "diagnostic",
    "difficulty_level": "intermediate",
    "user_profile": "small_farmer",
    "question": "ಕಳೆದ 15 ದಿನಗಳಿಂದ ಮಳೆ ಸರಿಯಾಗಿ ಆಗಿಲ್ಲ. ಭತ್ತದ ಎಲೆಗಳ ತುದಿ ಒಣಗುತ್ತಿದೆ ಮತ್ತು ಕೆಳಗಿನ ಎಲೆಗಳು ಹಳದಿಯಾಗುತ್ತಿವೆ. ಇದು ನೀರಿನ ಕೊರತೆಯೇ ಅಥವಾ ಪೋಷಕಾಂಶದ ಕೊರತೆಯೇ ಎಂದು ಹೇಗೆ ಗುರುತಿಸುವುದು?",
    "question_variants": [
      "ಭತ್ತದ ಎಲೆಗಳ ತುದಿ ಒಣಗುತ್ತಿದೆ, ಕೆಳಗಿನ ಎಲೆಗಳು ಹಳದಿಯಾಗುತ್ತಿವೆ, ಕಾರಣವೇನು?",
      "ಮಳೆ ಇಲ್ಲದೆ ಎಲೆಗಳ ತುದಿ ಒಣಗುತ್ತಿದ್ದರೆ ಅದು ನೀರಿನ ಕೊರತೆಯೇ?"
    ],
    "keywords": [
      "ನೀರಿನ ಕೊರತೆ",
      "ಪೋಷಕಾಂಶದ ಕೊರತೆ",
      "ಹಳದಿಯಾಗುತ್ತಿವೆ",
      "ತುದಿ ಒಣಗುತ್ತಿದೆ"
    ],
    "context": {
      "crop_stage": "vegetative",
      "soil_type": "all",
      "irrigation": "rainfed / poor irrigation"
    },
    "problem_description": "Water stress vs Nitrogen deficiency diagnosis in paddy during dry spells.",
    "symptoms": [
      "ಎಲೆಗಳ ತುದಿ ಒಣಗುವುದು",
      "ಕೆಳಗಿನ ಎಲೆಗಳು ಹಳದಿಯಾಗುವುದು"
    ],
    "causes": [
      "ನೀರಿನ ಕೊರತೆ (Water stress)",
      "ಸಾರಜನಕದ ಕೊರತೆ (Nitrogen deficiency)"
    ],
    "solution": {
      "short_answer": "ಮೊದಲಿಗೆ ಮಳೆಯ ಕೊರತೆಯಿಂದ ಮಣ್ಣಿನಲ್ಲಿ ತೇವಾಂಶ ಕಡಿಮೆಯಾಗಿ ನೀರಿನ ಕೊರತೆ ಉಂಟಾಗಿದೆ. ಇದರಿಂದ ಸಸ್ಯಗಳಿಗೆ ಪೋಷಕಾಂಶಗಳನ್ನು ಹೀರಿಕೊಳ್ಳಲು ಸಾಧ್ಯವಾಗದೆ, ಸಾರಜನಕದ (Nitrogen) ಕೊರತೆಯೂ ಕಾಣಿಸಿಕೊಂಡಿದೆ. ಇದು ಎರಡೂ ಸಮಸ್ಯೆಗಳ ಸಂಯೋಜನೆಯಾಗಿದೆ.",
      "detailed_answer": "ಮಳೆಯಿಲ್ಲದೆ ಉಂಟಾದ ತೇವಾಂಶದ ಕೊರತೆಯು ಪ್ರಾಥಮಿಕ ಸಮಸ್ಯೆಯಾಗಿದೆ. ನೀರಿನ ಕೊರತೆಯಿಂದಾಗಿ ಎಲೆಗಳ ತುದಿ ಒಣಗುತ್ತದೆ ಮತ್ತು ಉರುಳಿಕೊಳ್ಳುತ್ತದೆ. ಅದೇ ಸಮಯದಲ್ಲಿ, ಮಣ್ಣಿನಲ್ಲಿ ತೇವಾಂಶವಿಲ್ಲದ ಕಾರಣ ಸಸ್ಯದ ಬೇರುಗಳು ಸಾರಜನಕವನ್ನು ಹೀರಿಕೊಳ್ಳಲು ಸಾಧ್ಯವಾಗುವುದಿಲ್ಲ. ಇದರಿಂದಾಗಿ ಸಾರಜನಕದ ಕೊರತೆ ಉಂಟಾಗಿ, ಕೆಳಗಿನ ಹಳೆಯ ಎಲೆಗಳು ತುದಿಯಿಂದ ಮಧ್ಯದವರೆಗೆ V-ಆಕಾರದಲ್ಲಿ ಹಳದಿಯಾಗುತ್ತವೆ.",
      "step_by_step": [
        "ಸಾಧ್ಯವಾದರೆ ತಕ್ಷಣ ನೀರಾವರಿ ಒದಗಿಸಿ ಮಣ್ಣಿನ ತೇವಾಂಶವನ್ನು ಕಾಪಾಡಿ.",
        "ಮಣ್ಣಿನಲ್ಲಿ ತೇವಾಂಶ ಬಂದ ನಂತರ, ಎಕರೆಗೆ 10-15 ಕೆ.ಜಿ ಯೂರಿಯಾ (Urea) ಮೇಲುಗೊಬ್ಬರವಾಗಿ ಕೊಡಿ.",
        "ನೀರು ಒದಗಿಸಲು ಸಾಧ್ಯವಾಗದಿದ್ದರೆ ಶೇ. 1-2 ಯೂರಿಯಾ ದ್ರಾವಣವನ್ನು (10 ಲೀಟರ್ ನೀರಿಗೆ 100-200 ಗ್ರಾಂ) ಎಲೆಗಳ ಮೇಲೆ ಸಿಂಪಡಿಸಿ."
      ],
      "preventive_measures": [
        "ಮಳೆಗಾಲದ ಮುನ್ನ ಸಾವಯವ ಗೊಬ್ಬರವನ್ನು ಹೆಚ್ಚಾಗಿ ಬಳಸಿ ಮಣ್ಣಿನ ತೇವಾಂಶ ಹಿಡಿದಿಡುವ ಸಾಮರ್ಥ್ಯವನ್ನು ಹೆಚ್ಚಿಸಿ."
      ],
      "recommended_products": [
        "Urea (ಯೂರಿಯಾ)",
        "Water (ನೀರಾವರಿ)"
      ],
      "organic_solutions": [],
      "warnings": [
        "ಮಣ್ಣಿನಲ್ಲಿ ತೇವಾಂಶ ಇಲ್ಲದಾಗ ಒಣ ಮಣ್ಣಿಗೆ ಯೂರಿಯಾ ಅಥವಾ ಇತರ ರಾಸಾಯನಿಕ ಗೊಬ್ಬರಗಳನ್ನು ಹಾಕಬೇಡಿ, ಇದು ಸಸ್ಯಗಳನ್ನು ಸುಡಬಹುದು."
      ]
    },
    "retrieval_text": "ಭತ್ತ (Rice / Paddy) ಬೆಳೆಗೆ ಸಂಬಂಧಿಸಿದ ಪ್ರಶ್ನೆ: ಮಳೆ ಸರಿಯಾಗಿ ಆಗಿಲ್ಲ, ಭತ್ತದ ಎಲೆಗಳ ತುದಿ ಒಣಗುತ್ತಿದೆ ಮತ್ತು ಕೆಳಗಿನ ಎಲೆಗಳು ಹಳದಿಯಾಗುತ್ತಿವೆ, ಇದು ನೀರಿನ ಕೊರತೆಯೇ ಅಥವಾ ಪೋಷಕಾಂಶದ ಕೊರತೆಯೇ? ವಿಷಯ: ಪೋಷಕಾಂಶ ಮತ್ತು ನೀರಿನ ನಿರ್ವಹಣೆ. ಉತ್ತರ: ಮಳೆಯ ಕೊರತೆಯಿಂದ ತೇವಾಂಶ ಕಡಿಮೆಯಾಗಿ ನೀರಿನ ಕೊರತೆ ಉಂಟಾಗಿದೆ. ಇದರಿಂದ ಸಸ್ಯಗಳಿಗೆ ಪೋಷಕಾಂಶಗಳನ್ನು ಹೀರಿಕೊಳ್ಳಲು ಸಾಧ್ಯವಾಗದೆ ಸಾರಜನಕದ (Nitrogen) ಕೊರತೆಯೂ ಕಾಣಿಸಿಕೊಂಡಿದೆ. ತಕ್ಷಣ ನೀರು ಒದಗಿಸಿ, ತೇವಾಂಶ ಬಂದ ನಂತರ ಯೂರಿಯಾ ಕೊಡಿ.",
    "metadata": {
      "source": "Agricultural Knowledge Dataset",
      "verified": True,
      "confidence_level": "high",
      "last_updated": "2026-08-15"
    }
}

data.append(new_entry)

with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Added Paddy Diagnostic entry successfully!")
