from google import genai
from google.genai import types

from google import genai
from google.genai import types

class GeminiGenerator:
    def __init__(self, api_key, model_name, system_prompt, use_search=True):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.use_search = use_search

    def generate_article(self, genres):
        """
        Generates a news report using Gemini with Google Search Grounding.
        """
        if self.use_search:
            print("[INFO] Generating report with Gemini Grounding...")
            prompt = f"""
            今日の {", ".join(genres)} に関する最新ニュースを検索し、以下の指示に従ってレポートを作成してください。
            
            {self.system_prompt}
            """
            tools = [types.Tool(google_search=types.GoogleSearch())]
        else:
            print("[INFO] Generating report (No Search)...")
            prompt = f"""
            以下の指示に従って記事を作成してください。
            テーマ: {", ".join(genres)}
            
            {self.system_prompt}
            """
            tools = None

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=tools
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

    def generate_image_prompt(self, article_content):
        """
        Generates a prompt for Stable Diffusion based on the article content.
        """
        print("[INFO] Generating image prompt...")
        prompt = f"""
        以下の記事の内容を元に、AI画像生成(Stable Diffusion)のための英語のプロンプトを作成してください。
        
        【記事内容】
        {article_content[:1000]}... (省略)
        
        【指示】
        - 記事のトピックを象徴する、抽象的または具体的なシーンを描写してください。
        - 英語で出力してください。
        - カンマ区切りのキーワード羅列形式で出力してください。
        - 余計な説明や「Here is the prompt:」などの前置きは一切不要です。プロンプトのみを出力してください。
        - 例: futuristic city, cyberpunk, neon lights, high quality, 4k, detailed
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            if response.text:
                return response.text.strip()
            else:
                return "abstract news background, digital art, high quality"
        except Exception as e:
            print(f"[ERROR] Image prompt generation failed: {e}")
            return "abstract news background, digital art, high quality"
