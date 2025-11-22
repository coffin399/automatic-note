from google import genai
from google.genai import types

from google import genai
from google.genai import types

class GeminiGenerator:
    def __init__(self, api_key, model_name, system_prompt):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.system_prompt = system_prompt

    def generate_article(self, genres):
        """
        Generates a news report using Gemini with Google Search Grounding.
        """
        print("[INFO] Generating report with Gemini Grounding...")
        
        genre_list = ", ".join(genres)
        prompt = f"""
        今日の {genre_list} に関する最新ニュースを検索し、以下の指示に従ってレポートを作成してください。
        
        {self.system_prompt}
        """

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            
            if response.text:
                return response.text
            else:
                print("[ERROR] No content generated.")
                return None

        except Exception as e:
            print(f"[ERROR] Generation failed: {e}")
            return None
