import re
from typing import Tuple, List, Dict, Any


EMERGENCY_RULES: List[Dict[str, Any]] = [
    {
        "pattern": r"(?i)\b(chest\s+pain|heart\s+attack|pressure\s+in\s+chest|pain\s+radiat(ing|es)\s+to\s+(left\s+arm|jaw)|நெஞ்சு\s*வலி|மாரடைப்பு)\b",
        "condition": "Acute Coronary Syndrome / Myocardial Infarction Warning",
        "instruction_en": "CRITICAL EMERGENCY: Signs of potential cardiac distress detected. Immediately stop and inform the Emergency Nurse Station (Room 101) or press the red Emergency Call Button.",
        "instruction_ta": "அவசர எச்சரிக்கை: மாரடைப்பு அறிகுறிகள் தென்படுகின்றன. உடனடியாக அவசர சிகிச்சை பிரிவுக்கு (அறை 101) செல்லவும் அல்லது அவசர அழைப்பு பொத்தானை அழுத்தவும்.",
    },
    {
        "pattern": r"(?i)\b(cannot\s+breathe|gasping\s+for\s+air|severe\s+breathlessness|blue\s+lips|மூச்சு\s*திணறல்)\b",
        "condition": "Severe Acute Respiratory Distress",
        "instruction_en": "CRITICAL EMERGENCY: Severe respiratory distress detected. High-flow oxygen and urgent medical assessment required immediately at Triage.",
        "instruction_ta": "அவசர எச்சரிக்கை: கடுமையான மூச்சுத் திணறல். உடனடியாக அவசர சிகிச்சை பிரிவுக்கு சென்று மருத்துவ உதவியைப் பெறவும்.",
    },
    {
        "pattern": r"(?i)\b(facial\s+droop|slurred\s+speech|sudden\s+weakness\s+in\s+(one\s+side|arm|leg)|stroke|பக்கவாதம்)\b",
        "condition": "Acute Neurological Deficit / Possible Stroke (FAST Protocol)",
        "instruction_en": "CRITICAL EMERGENCY: Potential signs of acute stroke detected. Urgent neuro-triage evaluation is immediately required.",
        "instruction_ta": "அவசர எச்சரிக்கை: பக்கவாத அறிகுறிகள். உடனடியாக அவசர சிகிச்சை பிரிவை அணுகவும்.",
    },
    {
        "pattern": r"(?i)\b(heavy\s+bleeding|coughing\s+up\s+blood|vomiting\s+blood|hemoptysis|அதிக\s*இரத்தப்போக்கு)\b",
        "condition": "Severe Acute Hemorrhage",
        "instruction_en": "CRITICAL EMERGENCY: Signs of severe acute bleeding. Direct in-person trauma/emergency stabilization required immediately.",
        "instruction_ta": "அவசர எச்சரிக்கை: அதிக இரத்தப்போக்கு. உடனே மருத்துவர் அவசர உதவி பெறவும்.",
    },
]


class EmergencyClassifier:
    """Evaluates patient input against configured emergency clinical safety rules."""

    @staticmethod
    def evaluate(text: str, language: str = "en") -> Tuple[bool, List[str], List[str]]:
        """
        Returns:
            (is_emergency, list_of_conditions, list_of_instructions)
        """
        is_emergency = False
        conditions = []
        instructions = []

        for rule in EMERGENCY_RULES:
            if re.search(rule["pattern"], text):
                is_emergency = True
                conditions.append(rule["condition"])
                if language == "ta":
                    instructions.append(rule["instruction_ta"])
                else:
                    instructions.append(rule["instruction_en"])

        return is_emergency, conditions, instructions
