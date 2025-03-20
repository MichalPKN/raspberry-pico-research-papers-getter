from config_file import API_KEY
import ujson
import urequests

def get_llm_summary(abstract):
    try:
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        api_key = API_KEY  # Store securely
        
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "contents": [{
                "parts": [{
                    "text": f"Summarize or explain this research paper abstract in about two sentences: {abstract}"
                }]
            }]
        }
        
        request_url = f"{url}?key={api_key}"
        
        response = urequests.post(request_url, headers=headers, data=ujson.dumps(data))
        result = ujson.loads(response.text)
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Response content: {response.text}")
            print(f"Response content type: {response.headers['Content-Type']}")
        response.close()
        
        summary = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "Summary unavailable")
        if summary == "Summary unavailable":
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Response content: {response.text}")
            print(f"Response content type: {response.headers['Content-Type']}")
        return summary
    except Exception as e:
        print(f"Error getting LLM summary: {e}")
        return f"Summary unavailable"