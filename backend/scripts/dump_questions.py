import sys
import json
import glob
import os

sys.stdout.reconfigure(encoding='utf-8')

files = sorted(glob.glob('database/*.json'))
for f in files:
    name = os.path.basename(f)
    if name in ['farm_profiles.json', 'saved_advice.json', 'eval_dataset.json']:
        continue
    with open(f, 'r', encoding='utf-8') as fp:
        try:
            data = json.load(fp)
            if isinstance(data, list) and data:
                print(f"\n==========================================")
                print(f"🌾 {name.replace('.json', '').replace('_qa_kannada', '').replace('_dataset_schema_format', '').upper()}")
                print(f"==========================================")
                for item in data[:5]:
                    q = item.get('question', '')
                    topic = item.get('topic', '')
                    crop = item.get('crop_name', '')
                    sol = item.get('solution', '')
                    if isinstance(sol, dict):
                        short_sol = sol.get('short_answer', '')
                    else:
                        short_sol = str(sol)
                    if q:
                        print(f"• [{topic}]")
                        print(f"  ಪ್ರಶ್ನೆ (Question): {q}")
                        if item.get('question_variants'):
                            print(f"  ಇತರ ರೂಪಗಳು (Variants): {', '.join(item.get('question_variants')[:2])}")
                        print(f"  ಸಂಕ್ಷಿಪ್ತ ಉತ್ತರ (Answer): {short_sol[:120]}...\n")
        except Exception as e:
            print(f"Error {name}: {e}")
