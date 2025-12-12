"""
Библиотека голосов ElevenLabs с категориями

ПОЛНЫЙ список доступных голосов из бесплатной библиотеки ElevenLabs
с рекомендациями по использованию и preview URL.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class VoiceInfo:
    """Информация о голосе"""
    voice_id: str
    name: str
    gender: str  # male / female
    age: str  # young / middle / old
    accent: str  # american / british / australian / etc
    category: str  # narration / conversational / characters / etc
    use_case: List[str]  # documentary, podcast, audiobook, etc
    description: str
    preview_url: str = ""  # URL для прослушивания
    
    @property
    def display_name(self) -> str:
        """Отображаемое имя с описанием"""
        return f"{self.name} ({self.gender}, {self.accent}, {self.category})"


# === ПОЛНАЯ БИБЛИОТЕКА ГОЛОСОВ ELEVENLABS ===

VOICE_LIBRARY: Dict[str, VoiceInfo] = {}

# ============ МУЖСКИЕ ГОЛОСА — НАРРАТОРЫ ============

VOICE_LIBRARY["nPczCjzI2devNBz1zQrb"] = VoiceInfo(
    voice_id="nPczCjzI2devNBz1zQrb",
    name="Brian",
    gender="male",
    age="middle",
    accent="american",
    category="narration",
    use_case=["documentary", "audiobook", "history", "military"],
    description="Глубокий нарраторский голос, идеален для документальных фильмов",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/nPczCjzI2devNBz1zQrb/manifest.json"
)

VOICE_LIBRARY["pNInz6obpgDQGcFmaJgB"] = VoiceInfo(
    voice_id="pNInz6obpgDQGcFmaJgB",
    name="Adam",
    gender="male",
    age="middle",
    accent="american",
    category="narration",
    use_case=["documentary", "news", "educational"],
    description="Глубокий спокойный голос, профессиональный нарратор",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/pNInz6obpgDQGcFmaJgB/manifest.json"
)

VOICE_LIBRARY["2EiwWnXFnvU5JabPnv8n"] = VoiceInfo(
    voice_id="2EiwWnXFnvU5JabPnv8n",
    name="Clyde",
    gender="male",
    age="old",
    accent="american",
    category="narration",
    use_case=["documentary", "history", "military", "drama"],
    description="Старший авторитетный голос, идеален для военной истории",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/2EiwWnXFnvU5JabPnv8n/manifest.json"
)

VOICE_LIBRARY["onwK4e9ZLuTAKqWW03F9"] = VoiceInfo(
    voice_id="onwK4e9ZLuTAKqWW03F9",
    name="Daniel",
    gender="male",
    age="middle",
    accent="british",
    category="narration",
    use_case=["documentary", "news", "educational", "british"],
    description="Британский акцент, чёткая дикция, профессиональный",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/onwK4e9ZLuTAKqWW03F9/manifest.json"
)

VOICE_LIBRARY["pqHfZKP75CvOlQylNhV4"] = VoiceInfo(
    voice_id="pqHfZKP75CvOlQylNhV4",
    name="Bill",
    gender="male",
    age="middle",
    accent="american",
    category="narration",
    use_case=["documentary", "audiobook", "storytelling"],
    description="Американский документальный голос, тёплый тембр",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/pqHfZKP75CvOlQylNhV4/manifest.json"
)


# ============ МУЖСКИЕ ГОЛОСА — РАЗГОВОРНЫЕ ============

VOICE_LIBRARY["JBFqnCBsd6RMkjVDRZzb"] = VoiceInfo(
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    name="George",
    gender="male",
    age="middle",
    accent="british",
    category="conversational",
    use_case=["podcast", "educational", "tutorial"],
    description="Тёплый британский голос, дружелюбный и понятный",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/JBFqnCBsd6RMkjVDRZzb/manifest.json"
)

VOICE_LIBRARY["cjVigY5qzO86Huf0OWal"] = VoiceInfo(
    voice_id="cjVigY5qzO86Huf0OWal",
    name="Eric",
    gender="male",
    age="middle",
    accent="american",
    category="conversational",
    use_case=["podcast", "vlog", "casual"],
    description="Дружелюбный американский голос, casual стиль",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/cjVigY5qzO86Huf0OWal/manifest.json"
)

VOICE_LIBRARY["iP95p4xoKVk53GoZ742B"] = VoiceInfo(
    voice_id="iP95p4xoKVk53GoZ742B",
    name="Chris",
    gender="male",
    age="middle",
    accent="american",
    category="conversational",
    use_case=["podcast", "vlog", "tech"],
    description="Casual американский голос, подходит для tech контента",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/iP95p4xoKVk53GoZ742B/manifest.json"
)

VOICE_LIBRARY["TX3LPaxmHKxFdv7VOQHJ"] = VoiceInfo(
    voice_id="TX3LPaxmHKxFdv7VOQHJ",
    name="Liam",
    gender="male",
    age="young",
    accent="american",
    category="conversational",
    use_case=["podcast", "vlog", "gaming"],
    description="Молодой американский голос, нейтральный",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/TX3LPaxmHKxFdv7VOQHJ/manifest.json"
)

VOICE_LIBRARY["N2lVS1w4EtoT3dr4eOWO"] = VoiceInfo(
    voice_id="N2lVS1w4EtoT3dr4eOWO",
    name="Callum",
    gender="male",
    age="middle",
    accent="american",
    category="conversational",
    use_case=["podcast", "vlog", "storytelling"],
    description="Транскатлантический акцент, универсальный",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/N2lVS1w4EtoT3dr4eOWO/manifest.json"
)


# ============ МУЖСКИЕ ГОЛОСА — МОЛОДЫЕ/ЭНЕРГИЧНЫЕ ============

VOICE_LIBRARY["IKne3meq5aSn9XLyUdCD"] = VoiceInfo(
    voice_id="IKne3meq5aSn9XLyUdCD",
    name="Charlie",
    gender="male",
    age="young",
    accent="australian",
    category="conversational",
    use_case=["vlog", "gaming", "entertainment"],
    description="Молодой энергичный голос, австралийский акцент",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/IKne3meq5aSn9XLyUdCD/manifest.json"
)

VOICE_LIBRARY["SOYHLrjzK2X1ezoPC6cr"] = VoiceInfo(
    voice_id="SOYHLrjzK2X1ezoPC6cr",
    name="Harry",
    gender="male",
    age="young",
    accent="american",
    category="conversational",
    use_case=["vlog", "podcast", "casual"],
    description="Молодой спокойный голос, расслабленный стиль",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/SOYHLrjzK2X1ezoPC6cr/manifest.json"
)

VOICE_LIBRARY["bIHbv24MWmeRgasZH58o"] = VoiceInfo(
    voice_id="bIHbv24MWmeRgasZH58o",
    name="Will",
    gender="male",
    age="young",
    accent="american",
    category="conversational",
    use_case=["vlog", "gaming", "friendly"],
    description="Дружелюбный молодой голос",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/bIHbv24MWmeRgasZH58o/manifest.json"
)

VOICE_LIBRARY["g5CIjZEefAph4nQFvHAz"] = VoiceInfo(
    voice_id="g5CIjZEefAph4nQFvHAz",
    name="Ethan",
    gender="male",
    age="young",
    accent="american",
    category="conversational",
    use_case=["vlog", "gaming", "energetic"],
    description="Энергичный молодой голос",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/g5CIjZEefAph4nQFvHAz/manifest.json"
)

# ============ МУЖСКИЕ ГОЛОСА — ПРОФЕССИОНАЛЬНЫЕ ============

VOICE_LIBRARY["CwhRBWXzGAHq8TQ4Fs17"] = VoiceInfo(
    voice_id="CwhRBWXzGAHq8TQ4Fs17",
    name="Roger",
    gender="male",
    age="middle",
    accent="american",
    category="professional",
    use_case=["news", "corporate", "presentation"],
    description="Уверенный профессиональный голос, корпоративный стиль",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/CwhRBWXzGAHq8TQ4Fs17/manifest.json"
)

VOICE_LIBRARY["ZQe5CZNOzWyzPSCn5a3c"] = VoiceInfo(
    voice_id="ZQe5CZNOzWyzPSCn5a3c",
    name="James",
    gender="male",
    age="middle",
    accent="australian",
    category="professional",
    use_case=["news", "documentary", "professional"],
    description="Австралийский новостной голос, профессиональный",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/ZQe5CZNOzWyzPSCn5a3c/manifest.json"
)

VOICE_LIBRARY["ErXwobaYiN019PkySvjV"] = VoiceInfo(
    voice_id="ErXwobaYiN019PkySvjV",
    name="Antoni",
    gender="male",
    age="young",
    accent="american",
    category="professional",
    use_case=["educational", "tutorial", "calm"],
    description="Хорошо модулированный голос, образовательный контент",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/ErXwobaYiN019PkySvjV/manifest.json"
)

VOICE_LIBRARY["VR6AewLTigWG4xSOukaG"] = VoiceInfo(
    voice_id="VR6AewLTigWG4xSOukaG",
    name="Arnold",
    gender="male",
    age="middle",
    accent="american",
    category="narration",
    use_case=["documentary", "drama", "intense"],
    description="Хриплый драматичный голос, для напряжённых сцен",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/VR6AewLTigWG4xSOukaG/manifest.json"
)


# ============ ЖЕНСКИЕ ГОЛОСА — НАРРАТОРЫ ============

VOICE_LIBRARY["21m00Tcm4TlvDq8ikWAM"] = VoiceInfo(
    voice_id="21m00Tcm4TlvDq8ikWAM",
    name="Rachel",
    gender="female",
    age="middle",
    accent="american",
    category="narration",
    use_case=["documentary", "audiobook", "meditation"],
    description="Спокойный профессиональный женский голос",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/21m00Tcm4TlvDq8ikWAM/manifest.json"
)

VOICE_LIBRARY["XrExE9yKIg1WjnnlVkGX"] = VoiceInfo(
    voice_id="XrExE9yKIg1WjnnlVkGX",
    name="Matilda",
    gender="female",
    age="middle",
    accent="american",
    category="narration",
    use_case=["documentary", "corporate", "professional"],
    description="Тёплый профессиональный голос, бизнес стиль",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/XrExE9yKIg1WjnnlVkGX/manifest.json"
)

VOICE_LIBRARY["pFZP5JQG7iQjIQuC4Bku"] = VoiceInfo(
    voice_id="pFZP5JQG7iQjIQuC4Bku",
    name="Lily",
    gender="female",
    age="middle",
    accent="british",
    category="narration",
    use_case=["audiobook", "documentary", "british"],
    description="Британский нарраторский голос, элегантный",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/pFZP5JQG7iQjIQuC4Bku/manifest.json"
)

VOICE_LIBRARY["ThT5KcBeYPX3keUQqHPh"] = VoiceInfo(
    voice_id="ThT5KcBeYPX3keUQqHPh",
    name="Dorothy",
    gender="female",
    age="old",
    accent="british",
    category="narration",
    use_case=["audiobook", "storytelling", "calm"],
    description="Мудрый спокойный голос, идеален для историй",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/ThT5KcBeYPX3keUQqHPh/manifest.json"
)

VOICE_LIBRARY["AZnzlk1XvdvUeBnXmlld"] = VoiceInfo(
    voice_id="AZnzlk1XvdvUeBnXmlld",
    name="Domi",
    gender="female",
    age="young",
    accent="american",
    category="narration",
    use_case=["audiobook", "storytelling", "strong"],
    description="Сильный уверенный голос",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/AZnzlk1XvdvUeBnXmlld/manifest.json"
)


# ============ ЖЕНСКИЕ ГОЛОСА — РАЗГОВОРНЫЕ ============

VOICE_LIBRARY["EXAVITQu4vr4xnSDxMaL"] = VoiceInfo(
    voice_id="EXAVITQu4vr4xnSDxMaL",
    name="Sarah",
    gender="female",
    age="young",
    accent="american",
    category="conversational",
    use_case=["podcast", "vlog", "lifestyle"],
    description="Тёплый молодой голос, дружелюбный",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/EXAVITQu4vr4xnSDxMaL/manifest.json"
)

VOICE_LIBRARY["FGY2WhTYpPnrIDTdsKH5"] = VoiceInfo(
    voice_id="FGY2WhTYpPnrIDTdsKH5",
    name="Laura",
    gender="female",
    age="young",
    accent="american",
    category="conversational",
    use_case=["podcast", "vlog", "entertainment"],
    description="Молодой энергичный голос",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/FGY2WhTYpPnrIDTdsKH5/manifest.json"
)

VOICE_LIBRARY["Xb7hH8MSUJpSbSDYk0k2"] = VoiceInfo(
    voice_id="Xb7hH8MSUJpSbSDYk0k2",
    name="Alice",
    gender="female",
    age="middle",
    accent="british",
    category="conversational",
    use_case=["podcast", "educational", "british"],
    description="Британский уверенный голос",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/Xb7hH8MSUJpSbSDYk0k2/manifest.json"
)

VOICE_LIBRARY["XB0fDUnXU5powFXDhCwa"] = VoiceInfo(
    voice_id="XB0fDUnXU5powFXDhCwa",
    name="Charlotte",
    gender="female",
    age="middle",
    accent="swedish",
    category="conversational",
    use_case=["podcast", "educational", "calm"],
    description="Шведский акцент, спокойный голос",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/XB0fDUnXU5powFXDhCwa/manifest.json"
)

VOICE_LIBRARY["z9fAnlkpzviPz146aGWa"] = VoiceInfo(
    voice_id="z9fAnlkpzviPz146aGWa",
    name="Glinda",
    gender="female",
    age="middle",
    accent="american",
    category="conversational",
    use_case=["podcast", "storytelling", "witch"],
    description="Волшебный голос, для сказок",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/z9fAnlkpzviPz146aGWa/manifest.json"
)


# ============ ЖЕНСКИЕ ГОЛОСА — МОЛОДЫЕ/ЭНЕРГИЧНЫЕ ============

VOICE_LIBRARY["cgSgspJ2msm6clMCkdW9"] = VoiceInfo(
    voice_id="cgSgspJ2msm6clMCkdW9",
    name="Jessica",
    gender="female",
    age="young",
    accent="american",
    category="conversational",
    use_case=["vlog", "entertainment", "social"],
    description="Выразительный молодой голос",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/cgSgspJ2msm6clMCkdW9/manifest.json"
)

VOICE_LIBRARY["jBpfuIE2acCO8z3wKNLl"] = VoiceInfo(
    voice_id="jBpfuIE2acCO8z3wKNLl",
    name="Gigi",
    gender="female",
    age="young",
    accent="american",
    category="conversational",
    use_case=["animation", "gaming", "fun"],
    description="Игривый молодой голос",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/jBpfuIE2acCO8z3wKNLl/manifest.json"
)

VOICE_LIBRARY["jsCqWAovK2LkecY7zXl4"] = VoiceInfo(
    voice_id="jsCqWAovK2LkecY7zXl4",
    name="Freya",
    gender="female",
    age="young",
    accent="american",
    category="conversational",
    use_case=["vlog", "lifestyle", "friendly"],
    description="Дружелюбный молодой голос",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/jsCqWAovK2LkecY7zXl4/manifest.json"
)

VOICE_LIBRARY["MF3mGyEYCl7XYWbV9V6O"] = VoiceInfo(
    voice_id="MF3mGyEYCl7XYWbV9V6O",
    name="Elli",
    gender="female",
    age="young",
    accent="american",
    category="conversational",
    use_case=["educational", "tutorial", "friendly"],
    description="Эмоциональный молодой голос",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/MF3mGyEYCl7XYWbV9V6O/manifest.json"
)

VOICE_LIBRARY["LcfcDJNUP1GQjkzn1xUU"] = VoiceInfo(
    voice_id="LcfcDJNUP1GQjkzn1xUU",
    name="Emily",
    gender="female",
    age="young",
    accent="american",
    category="conversational",
    use_case=["vlog", "meditation", "calm"],
    description="Спокойный молодой голос",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/LcfcDJNUP1GQjkzn1xUU/manifest.json"
)

# ============ ЖЕНСКИЕ ГОЛОСА — ПРОФЕССИОНАЛЬНЫЕ ============

VOICE_LIBRARY["oWAxZDx7w5VEj9dCyTzz"] = VoiceInfo(
    voice_id="oWAxZDx7w5VEj9dCyTzz",
    name="Grace",
    gender="female",
    age="middle",
    accent="american",
    category="professional",
    use_case=["corporate", "presentation", "news"],
    description="Профессиональный корпоративный голос",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/oWAxZDx7w5VEj9dCyTzz/manifest.json"
)

VOICE_LIBRARY["t0jbNlBVZ17f02VDIeMI"] = VoiceInfo(
    voice_id="t0jbNlBVZ17f02VDIeMI",
    name="Serena",
    gender="female",
    age="middle",
    accent="american",
    category="professional",
    use_case=["corporate", "news", "professional"],
    description="Приятный профессиональный голос",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/t0jbNlBVZ17f02VDIeMI/manifest.json"
)

VOICE_LIBRARY["D38z5RcWu1voky8WS1ja"] = VoiceInfo(
    voice_id="D38z5RcWu1voky8WS1ja",
    name="Fin",
    gender="female",
    age="old",
    accent="irish",
    category="narration",
    use_case=["audiobook", "storytelling", "irish"],
    description="Ирландский акцент, для историй",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/D38z5RcWu1voky8WS1ja/manifest.json"
)


# ============ СПЕЦИАЛЬНЫЕ/ХАРАКТЕРНЫЕ ГОЛОСА ============

VOICE_LIBRARY["ODq5zmih8GrVes37Dizd"] = VoiceInfo(
    voice_id="ODq5zmih8GrVes37Dizd",
    name="Patrick",
    gender="male",
    age="middle",
    accent="american",
    category="characters",
    use_case=["animation", "characters", "dramatic"],
    description="Характерный голос для персонажей",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/ODq5zmih8GrVes37Dizd/manifest.json"
)

VOICE_LIBRARY["yoZ06aMxZJJ28mfd3POQ"] = VoiceInfo(
    voice_id="yoZ06aMxZJJ28mfd3POQ",
    name="Sam",
    gender="male",
    age="young",
    accent="american",
    category="characters",
    use_case=["animation", "gaming", "raspy"],
    description="Хриплый молодой голос",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/yoZ06aMxZJJ28mfd3POQ/manifest.json"
)

VOICE_LIBRARY["GBv7mTt0atIp3Br8iCZE"] = VoiceInfo(
    voice_id="GBv7mTt0atIp3Br8iCZE",
    name="Thomas",
    gender="male",
    age="young",
    accent="american",
    category="conversational",
    use_case=["vlog", "casual", "calm"],
    description="Спокойный молодой голос",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/GBv7mTt0atIp3Br8iCZE/manifest.json"
)

VOICE_LIBRARY["flq6f7yk4E4fJM5XTYuZ"] = VoiceInfo(
    voice_id="flq6f7yk4E4fJM5XTYuZ",
    name="Michael",
    gender="male",
    age="old",
    accent="american",
    category="narration",
    use_case=["audiobook", "documentary", "wise"],
    description="Мудрый старший голос",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/flq6f7yk4E4fJM5XTYuZ/manifest.json"
)

VOICE_LIBRARY["TxGEqnHWrfWFTfGW9XjX"] = VoiceInfo(
    voice_id="TxGEqnHWrfWFTfGW9XjX",
    name="Josh",
    gender="male",
    age="young",
    accent="american",
    category="conversational",
    use_case=["vlog", "gaming", "energetic"],
    description="Энергичный молодой голос",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/TxGEqnHWrfWFTfGW9XjX/manifest.json"
)

VOICE_LIBRARY["ZF6FPAbjXT4488VcRRnw"] = VoiceInfo(
    voice_id="ZF6FPAbjXT4488VcRRnw",
    name="Mimi",
    gender="female",
    age="young",
    accent="swedish",
    category="conversational",
    use_case=["vlog", "lifestyle", "swedish"],
    description="Шведский акцент, молодой голос",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/ZF6FPAbjXT4488VcRRnw/manifest.json"
)

VOICE_LIBRARY["Zlb1dXrM653N07WRdFW3"] = VoiceInfo(
    voice_id="Zlb1dXrM653N07WRdFW3",
    name="Joseph",
    gender="male",
    age="middle",
    accent="british",
    category="narration",
    use_case=["audiobook", "documentary", "british"],
    description="Британский нарраторский голос",
    preview_url="https://storage.googleapis.com/eleven-public-prod/premade/voices/Zlb1dXrM653N07WRdFW3/manifest.json"
)


# === КАТЕГОРИИ ГОЛОСОВ ===

VOICE_CATEGORIES = {
    "military_history": {
        "name": "⚔️ Военная история",
        "description": "Специально для военной и исторической тематики",
        "voices": ["Brian", "Clyde", "Daniel", "Adam", "Arnold", "Bill"]
    },
    "documentary": {
        "name": "📚 Документальные",
        "description": "Для документальных фильмов, истории",
        "voices": ["Brian", "Adam", "Clyde", "Daniel", "Bill", "Rachel", "Matilda", "Joseph", "Michael"]
    },
    "audiobook": {
        "name": "📖 Аудиокниги",
        "description": "Для аудиокниг и длинных историй",
        "voices": ["Brian", "Adam", "Rachel", "Lily", "Dorothy", "Domi", "Fin", "Michael"]
    },
    "podcast": {
        "name": "🎙 Подкасты",
        "description": "Для подкастов и разговорного контента",
        "voices": ["George", "Eric", "Chris", "Liam", "Callum", "Sarah", "Laura", "Alice", "Charlotte"]
    },
    "news": {
        "name": "📰 Новости",
        "description": "Для новостного и профессионального контента",
        "voices": ["Daniel", "Roger", "James", "Grace", "Serena", "Antoni"]
    },
    "entertainment": {
        "name": "🎬 Развлечения",
        "description": "Для влогов, gaming, развлекательного контента",
        "voices": ["Charlie", "Harry", "Will", "Ethan", "Josh", "Jessica", "Gigi", "Laura", "Freya", "Emily"]
    },
    "characters": {
        "name": "🎭 Персонажи",
        "description": "Характерные голоса для анимации и персонажей",
        "voices": ["Patrick", "Sam", "Arnold", "Gigi", "Glinda", "Thomas"]
    },
    "corporate": {
        "name": "💼 Корпоративные",
        "description": "Для бизнес презентаций и корпоративного контента",
        "voices": ["Roger", "Grace", "Matilda", "Serena", "Daniel", "James"]
    }
}


# === ФУНКЦИИ ДЛЯ РАБОТЫ С ГОЛОСАМИ ===

def get_voices_by_category(category: str) -> List[VoiceInfo]:
    """Получить голоса по категории"""
    if category not in VOICE_CATEGORIES:
        return list(VOICE_LIBRARY.values())
    
    voice_names = VOICE_CATEGORIES[category]["voices"]
    return [v for v in VOICE_LIBRARY.values() if v.name in voice_names]


def get_voice_by_name(name: str) -> Optional[VoiceInfo]:
    """Получить голос по имени"""
    for voice in VOICE_LIBRARY.values():
        if voice.name.lower() == name.lower():
            return voice
    return None


def get_voice_by_id(voice_id: str) -> Optional[VoiceInfo]:
    """Получить голос по ID"""
    return VOICE_LIBRARY.get(voice_id)


def recommend_voice_for_content(content_type: str, gender: str = "male") -> VoiceInfo:
    """
    Рекомендация голоса на основе типа контента
    
    content_type: documentary, podcast, audiobook, news, entertainment, military
    gender: male, female
    """
    type_to_category = {
        "documentary": "documentary",
        "history": "documentary",
        "military": "military_history",
        "war": "military_history",
        "podcast": "podcast",
        "vlog": "entertainment",
        "audiobook": "audiobook",
        "news": "news",
        "entertainment": "entertainment",
        "gaming": "entertainment",
        "corporate": "corporate",
        "business": "corporate"
    }
    
    category = type_to_category.get(content_type.lower(), "documentary")
    voices = get_voices_by_category(category)
    
    filtered = [v for v in voices if v.gender == gender]
    
    if filtered:
        return filtered[0]
    
    all_gender_voices = [v for v in VOICE_LIBRARY.values() if v.gender == gender]
    if all_gender_voices:
        narrators = [v for v in all_gender_voices if v.category == "narration"]
        if narrators:
            return narrators[0]
        return all_gender_voices[0]
    
    return VOICE_LIBRARY["nPczCjzI2devNBz1zQrb"]


def get_all_voices_for_ui() -> List[tuple]:
    """
    Получить все голоса для отображения в UI
    Returns: [(display_name, voice_id), ...]
    """
    result = []
    
    for category_id, category_info in VOICE_CATEGORIES.items():
        result.append((f"--- {category_info['name']} ---", ""))
        
        added_voices = set()
        for voice in VOICE_LIBRARY.values():
            if voice.name in category_info["voices"] and voice.name not in added_voices:
                display = f"  {voice.name} ({voice.gender}, {voice.accent})"
                result.append((display, voice.voice_id))
                added_voices.add(voice.name)
    
    return result


def get_voices_grouped_by_gender() -> Dict[str, List[VoiceInfo]]:
    """Получить голоса сгруппированные по полу"""
    return {
        "male": [v for v in VOICE_LIBRARY.values() if v.gender == "male"],
        "female": [v for v in VOICE_LIBRARY.values() if v.gender == "female"]
    }


def get_voices_grouped_by_accent() -> Dict[str, List[VoiceInfo]]:
    """Получить голоса сгруппированные по акценту"""
    result = {}
    for voice in VOICE_LIBRARY.values():
        if voice.accent not in result:
            result[voice.accent] = []
        result[voice.accent].append(voice)
    return result


def search_voices(query: str) -> List[VoiceInfo]:
    """Поиск голосов по имени, описанию или use_case"""
    query = query.lower()
    results = []
    
    for voice in VOICE_LIBRARY.values():
        if (query in voice.name.lower() or 
            query in voice.description.lower() or
            any(query in uc.lower() for uc in voice.use_case)):
            results.append(voice)
    
    return results


# === СТАТИСТИКА ===

def get_voice_stats() -> Dict:
    """Статистика по библиотеке голосов"""
    voices = list(VOICE_LIBRARY.values())
    return {
        "total": len(voices),
        "male": len([v for v in voices if v.gender == "male"]),
        "female": len([v for v in voices if v.gender == "female"]),
        "categories": len(VOICE_CATEGORIES),
        "accents": len(set(v.accent for v in voices))
    }
