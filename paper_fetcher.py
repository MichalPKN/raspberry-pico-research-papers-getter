import urequests
import ujson
import time
import os
from gemini_summary import get_llm_summary

class PaperFetcher:
    def __init__(self, keywords, max_papers):
        self.keywords = keywords
        self.max_papers = max_papers
        self.papers = []
        self.paper_ids = set()  # Track already fetched papers
        
        try:
            os.mkdir("papers")
            print("Creating papers directory")
        except OSError:
            try:
                with open("papers", "r") as f:
                    print("'papers' exists as a file")
                os.remove("papers")
                os.mkdir("papers")
            except:
                pass
            pass # Directory already exists
        
        self._load_papers()
    
    def _load_papers(self):
        try:
            with open("papers/papers.json", "r") as f:
                self.papers = ujson.load(f)
                self.paper_ids = {paper['id'] for paper in self.papers}
        except (OSError, ValueError):
            self.papers = []
            self.paper_ids = set()
    
    def save_papers(self, new_papers=None):
        if new_papers:
            # Add new papers to the list
            self.papers.extend(new_papers)
            self.papers = self.papers[-self.max_papers:]
        
        with open("papers/papers.json", "w") as f:
            ujson.dump(self.papers, f)
    
    def get_papers(self):
        return self.papers
    
    def fetch_papers(self):
        new_papers = []
        
        # arXiv API for each keyword
        for keyword in self.keywords:
            try:
                query = keyword.replace(" ", "+")
                print(f"Fetching papers for keyword '{keyword}'...")
                url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={self.max_papers // len(self.keywords)}&sortBy=submittedDate&sortOrder=descending"

                response = urequests.get(url)
                
                if response.status_code != 200:
                    print(f"Response status: {response.status_code}")
                    print(f"Response headers: {response.headers}")
                    print(f"Response content: {response.text}")
                    print(f"Response content type: {response.headers['Content-Type']}")
                
                content = response.text
                response.close()
                print(f"Feth complete")
                
                entries = content.split("<entry>")
                for entry in entries[1:]:
                    try:
                        id_start = entry.find("<id>") + 4
                        id_end = entry.find("</id>")
                        paper_id = entry[id_start:id_end].strip()
                        
                        if paper_id in self.paper_ids:
                            continue
                        
                        title_start = entry.find("<title>") + len("<title>")
                        title_end = entry.find("</title>")
                        title = entry[title_start:title_end].strip()
                        
                        summary_start = entry.find("<summary>") + len("<summary>")
                        summary_end = entry.find("</summary>")
                        summary = entry[summary_start:summary_end].strip()
                        
                        published_start = entry.find("<published>") + len("<published>")
                        published_end = entry.find("</published>")
                        published = entry[published_start:published_end].strip()
                        
                        print(f"Found new paper: {title}")
                        summary = get_llm_summary(summary)
                        
                        paper = {
                            "id": paper_id,
                            "title": title,
                            "summary": summary,
                            "published": published,
                            "url": paper_id,
                            "keyword": keyword
                        }
                        
                        new_papers.append(paper)
                        self.paper_ids.add(paper_id)
                        time.sleep(5) # avoid gemini rate limits
                    except Exception as e:
                        print(f"Error parsing paper: {e}")
                
            except Exception as e:
                print(f"Error fetching papers for keyword '{keyword}': {e}")
        
        return new_papers
