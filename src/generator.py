from google import genai
from google.genai import types

class GeminiGenerator:
    def __init__(self, api_key, model_name, system_prompt):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.system_prompt = system_prompt

    def generate_article(self, title, search_results):
        """
        Generates an article based on the title and aggregated search results.
        search_results: Dict {Genre: [results]}
        """
        print(f"[INFO] Generating content for: {title}")
        
        # Construct context from search results
        context = ""
        for genre, results in search_results.items():
            context += f"\n## {genre}\n"
            if results:
                for i, res in enumerate(results, 1):
                    context += f"{i}. {res['title']}: {res['snippet']}\n"
            else:
                context += "(ニュースなし)\n"

        prompt = f"""
        Title: {title}
        
        Search Results (Context):
        {context}
        
        Please generate the report based on the system instructions.
        """

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_prompt,
                    temperature=0.7
                )
            )
            return response.text
        except Exception as e:
            print(f"[ERROR] Gemini generation failed: {e}")
            return None
