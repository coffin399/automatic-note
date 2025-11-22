import google.generativeai as genai
import os

class GeminiGenerator:
    def __init__(self, api_key, system_prompt):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            'gemini-pro',
            system_instruction=system_prompt
        )

    def generate_article(self, title, search_results_dict):
        """
        Generates an article based on the title and a dictionary of search results.
        search_results_dict: { "Genre": [ {title, snippet, url}, ... ] }
        """
        context = "以下の検索結果を参考に、レポートを作成してください：\n\n"
        
        for genre, results in search_results_dict.items():
            context += f"### ジャンル: {genre}\n"
            if not results:
                context += "（関連ニュースなし）\n\n"
                continue
                
            for i, result in enumerate(results):
                context += f"- Source {i+1}: {result['title']}\n  {result['snippet']}\n  URL: {result['url']}\n"
            context += "\n"

        prompt = f"タイトル: {title}\n\n{context}"
        
        print(f"[INFO] Generating report for: {title}...")
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"[ERROR] Generation failed: {e}")
            return None

if __name__ == "__main__":
    # Mock test
    pass
