from duckduckgo_search import DDGS
import time

class WebScraper:
    def __init__(self):
        self.ddgs = DDGS()

    def search(self, keywords, max_results=5):
        """
        Searches DuckDuckGo for the given keywords.
        Returns a list of results (title, href, body).
        """
        query = " ".join(keywords)
        print(f"[INFO] Searching for: {query}")
        
        results = []
        try:
            # Using 'text' method for standard search
            # backend="api" is often more reliable for automated requests
            search_results = self.ddgs.text(query, max_results=max_results)
            
            if search_results:
                for r in search_results:
                    results.append({
                        "title": r.get("title"),
                        "url": r.get("href"),
                        "snippet": r.get("body")
                    })
            else:
                print("[WARN] No results found.")
                
        except Exception as e:
            print(f"[ERROR] Search failed: {e}")

        return results

if __name__ == "__main__":
    # Simple test
    scraper = WebScraper()
    results = scraper.search(["AI副業", "2024", "おすすめ"])
    for r in results:
        print(f"- {r['title']}: {r['url']}")
