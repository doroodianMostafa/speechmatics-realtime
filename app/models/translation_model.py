import openai
from typing import Dict, List
from ..config import Config

class TranslationModel:
    def __init__(self):
        self.api_key = Config.OPENAI_API_KEY
        openai.api_key = self.api_key

    def translate(self, text: str, source_lang: str = None, target_langs: List[str] = None) -> Dict[str, str]:
        """
        Translate text from source language to multiple target languages using GPT-4
        Returns a dictionary of {lang_code: translation}
        """
        source_lang = source_lang or Config.SOURCE_LANGUAGE
        target_langs = target_langs or Config.TARGET_LANGUAGES

        try:
            langs_str = ", ".join(target_langs)
            system_prompt = (
                f"Translate this {source_lang} text to {langs_str}. "
                f"Output format: 'lang_code: translation' per line. "
                f"No extra text."
            )
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.0,
            )
            translated_output = response["choices"][0]["message"]["content"].strip()
            return self._parse_translations(translated_output, target_langs)
        except Exception as e:
            return {lang: f"<Error: {e}>" for lang in target_langs}

    def _parse_translations(self, output: str, target_langs: List[str]) -> Dict[str, str]:
        """Parse GPT's response into translation dictionary"""
        translations = {}
        for line in output.split('\n'):
            if ': ' in line:
                lang, trans = line.split(': ', 1)
                lang = lang.strip().lower()
                if lang in target_langs:
                    translations[lang] = trans.strip()
        # Add missing languages
        for lang in target_langs:
            if lang not in translations:
                translations[lang] = f"<Missing {lang} translation>"
        return translations 