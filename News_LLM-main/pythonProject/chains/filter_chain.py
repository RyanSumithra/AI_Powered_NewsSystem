import os
import time
import json
import re
from typing import List, Dict
import google.generativeai as genai

# ✅ Gemini configuration
GEMINI_API_KEY = "AIzaSyBDhlBbx_mDP6OKlXYjnoIkOx0HFQeaRCI"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="models/gemini-2.5-flash")

# ✅ Load prompt template
FILTER_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "filter_prompt.txt")
with open(FILTER_PROMPT_PATH, "r", encoding="utf-8") as f:
    FILTER_PROMPT_TEMPLATE = f.read()

# ✅ Pre-filter logic
def is_probably_indian(article: Dict) -> bool:
    url = article.get("link", "").lower()
    source = article.get("source", "").lower()
    keywords = ['india', '.in', 'timesofindia', 'hindustantimes', 'thehindu', 'jagran', 'ndtv', 'livemint']
    return any(k in url or k in source for k in keywords)

def is_probably_global(article: Dict) -> bool:
    return not is_probably_indian(article)

# ✅ Clean article to formatted text block
def clean_article_text(article: Dict) -> str:
    title = article.get("title", "").strip()
    summary = article.get("summary", "").strip()
    return f"Title: {title}\nSummary: {summary}"

# ✅ Build prompt with multiple articles
def build_batch_prompt(articles: List[Dict], topic: str) -> str:
    blocks = [f"[ARTICLE {i+1}]\n{clean_article_text(a)}" for i, a in enumerate(articles)]
    combined = "\n\n".join(blocks)
    return FILTER_PROMPT_TEMPLATE.replace("{{articles_block}}", combined).replace("{{topic}}", topic)


# ✅ Call Gemini API and return raw text
def call_gemini(prompt: str, retries=2) -> str:
    try:
        response = model.generate_content(prompt)

        # 🔍 Log full raw response for debugging
        with open("gemini_raw_log.txt", "a", encoding="utf-8") as log_file:
            log_file.write(f"\n--- Prompt ---\n{prompt}\n\n--- Response ---\n{response.text}\n\n")

        return response.text.strip()
    except Exception as e:
        if retries > 0:
            time.sleep(1)
            return call_gemini(prompt, retries - 1)
        print(f"❌ Gemini error: {e}")
        return ""

# ✅ Extract JSON list from raw text
def parse_batch_response(text: str, expected_count: int) -> List[Dict]:
    try:
        data = json.loads(text)
        if isinstance(data, list) and len(data) == expected_count:
            return data
    except Exception:
        pass

    try:
        match = re.search(r'\[\s*{.*}\s*\]', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception as e:
        print(f"⚠️ Parsing error: {e}")
    return []

# ✅ Main classification + scoring function
def classify_and_score_articles(
    articles: List[Dict],
    topic: str,
    batch_size: int = 10,
    use_prefilter: bool = True,
    min_score: int = 30,
    region: str = "India"  # 🔁 Added explicit region
) -> List[Dict]:
    print("\n🧠 Starting classification with Gemini (batch mode)...")

    # ✅ Region pre-filter
    if region.lower() == "india":
        articles = [a for a in articles if is_probably_indian(a)]
    elif region.lower() == "global":
        articles = [a for a in articles if is_probably_global(a)]

    if not articles:
        print("❌ No articles matched region filter before classification.")
        return []

    results = []

    for i in range(0, len(articles), batch_size):
        batch = articles[i:i + batch_size]
        print(f"\n🧠 Classifying batch {i // batch_size + 1} with {len(batch)} articles...")

        prompt = build_batch_prompt(batch, topic)
        response_text = call_gemini(prompt)
        parsed_outputs = parse_batch_response(response_text, len(batch))

        if not parsed_outputs or len(parsed_outputs) != len(batch):
            print("⚠️ Skipped batch due to parsing issues.")
            continue

        for article, output in zip(batch, parsed_outputs):
            score = 0
            reasons = []

            if output.get("is_relevant"):
                score += 60
                reasons.append(f"Matched topic: {topic}")
            if output.get("region", "").lower() == "india":
                score += 10
                reasons.append("Region = India")
            if output.get("content_type", "").lower() == "general":
                score += 10
                reasons.append("Content Type = General")

            output["relevance_score"] = score
            output["score_breakdown"] = ", ".join(reasons)
            output["ai_reasoning"] = output.get("reasoning", "")
            article["classification"] = output

            if score >= min_score:
                results.append(article)
                print(f"   ✅ {article['title'][:60]} → {score}")
            else:
                print(f"   ❌ Skipped (Score: {score})")

        time.sleep(1)

    return results