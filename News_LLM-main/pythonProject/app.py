# app.py - Gemini-enhanced AI News Aggregator
import json
import yaml
import os
import time
from typing import List, Dict  # ✅ ADD THIS LINE
from scraping.rss_scraper import fetch_articles
from chains.filter_chain import classify_and_score_articles
from delivery.emailer import send_email

# Load configuration
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, "config.yaml")
with open(config_path, encoding="utf-8") as f:
    config = yaml.safe_load(f)


USER_FILTER = config["user_filter"]

# app.py or your utils file

def filter_and_rank_articles(
    articles: List[Dict],
    user_filter: Dict,
    max_articles: int = 10
) -> List[Dict]:
    print("\n🎯 Filtering articles based on user preferences...")
    filtered = []

    target_region = user_filter.get("region", "").lower()
    target_content_type = user_filter.get("content_type", "").lower()
    target_topic = user_filter.get("topic", "").lower()

    for article in articles:
        classification = article.get("classification", {})
        article_region = classification.get("region", "").lower()
        article_type = classification.get("content_type", "").lower()
        article_topic_match = classification.get("is_relevant", False)

        if article_region != target_region:
            print(f"🚫 Skipped: {article['title'][:60]} - ❌ Region mismatch")
            continue
        if article_type != target_content_type:
            print(f"🚫 Skipped: {article['title'][:60]} - ❌ Content type mismatch")
            continue
        if not article_topic_match:
            print(f"🚫 Skipped: {article['title'][:60]} - ❌ Topic mismatch")
            continue

        filtered.append(article)

    print(f"📊 Filter results: {len(filtered)} articles match criteria")
    return sorted(filtered, key=lambda x: x['classification']['relevance_score'], reverse=True)[:max_articles]


def display_results_with_scores(results):
    print(f"\n📰 TOP {len(results)} ARTICLES (Ranked by Relevance)")
    print("=" * 80)

    for i, result in enumerate(results, 1):
        score = result['relevance_score']
        score_emoji = "🥇" if score >= 80 else "🥈" if score >= 60 else "🥉" if score >= 40 else "📰"
        print(f"\n{score_emoji} {i}. [{score}/100] {result['title']}")
        print(f"   🔗 {result['link']}")
        print(f"   📰 Source: {result['source']}")
        print(f"   📊 Score Breakdown: {result.get('score_breakdown', 'N/A')}")
        if result['ai_reasoning']:
            print(f"   🧠 AI Reasoning: {result['ai_reasoning']}")
        if result['summary']:
            print(f"   📝 Summary: {result['summary'][:100]}...")

def show_scoring_analytics(results):
    if not results:
        return

    scores = [r['relevance_score'] for r in results]
    print(f"\n📊 SCORING ANALYTICS")
    print("=" * 40)
    print(f"Total Articles: {len(results)}")
    print(f"Highest Score: {max(scores)}")
    print(f"Lowest Score: {min(scores)}")
    print(f"Average Score: {sum(scores)/len(scores):.1f}")

    quality_buckets = {
        "🥇 Excellent (80-100)": len([s for s in scores if s >= 80]),
        "🥈 Good (60-79)": len([s for s in scores if 60 <= s < 80]),
        "🥉 Average (40-59)": len([s for s in scores if 40 <= s < 60]),
        "📰 Below Average (<40)": len([s for s in scores if s < 40])
    }

    print(f"\n🎯 QUALITY DISTRIBUTION:")
    for label, count in quality_buckets.items():
        print(f"  {label}: {count} articles")

    source_scores = {}
    for result in results:
        source = result['source']
        source_scores.setdefault(source, []).append(result['relevance_score'])

    print(f"\n📈 TOP SOURCES BY AVERAGE SCORE:")
    top_sources = sorted(
        [(src, sum(scores)/len(scores), len(scores)) for src, scores in source_scores.items()],
        key=lambda x: x[1], reverse=True
    )[:5]
    for source, avg, count in top_sources:
        print(f"  {source}: {avg:.1f} avg ({count} articles)")

def main():
    print("🤖 Starting AI-Powered News Aggregator with Gemini Scoring")
    print("=" * 80)
    start_time = time.time()

    print("🔍 Fetching articles from RSS + Google News...")
    selected_topic = USER_FILTER.get('topic', 'education')
    articles = fetch_articles(topic=selected_topic)
    print(f"✅ Fetched {len(articles)} articles")

    if not articles:
        print("⚠️ No articles fetched. Check topic or sources.")
        return

    print(f"\n🧠 Starting Gemini classification and scoring...")
    scoring_config = config.get("scoring", {})

    scored_articles = classify_and_score_articles(articles, **scoring_config)
    print(f"✅ Gemini scoring complete. {len(scored_articles)} articles above threshold.")

    print(f"\n🎯 Filtering and ranking results...")
    max_articles = config.get('max_articles', 50)
    top_articles = filter_and_rank_articles(scored_articles, USER_FILTER, max_articles)

    total_time = time.time() - start_time
    print("\n" + "=" * 80)
    print(f"📊 PROCESSING SUMMARY")
    print(f"Total fetched: {len(articles)}")
    print(f"AI passed: {len(scored_articles)}")
    print(f"Filtered: {len(top_articles)}")
    print(f"⏱️ Total time: {total_time:.2f}s")

    if articles:
        print(f"Avg time per article: {total_time / len(articles):.2f}s")

    if top_articles:
        show_scoring_analytics(top_articles)
        display_results_with_scores(top_articles)

        if config['delivery']['method'] == 'email':
            print(f"\n📧 Sending top {len(top_articles)} articles via email...")
            email_articles = [ {
                'title': f"[{a['relevance_score']}/100] {a['title']}",
                'link': a['link'],
                'summary': a.get('summary', ''),
                'source': a['source'],
                'score_info': f"Relevance Score: {a['relevance_score']}/100"
            } for a in top_articles ]
            send_email(email_articles, topic=selected_topic)

        print(f"\n🎉 Successfully processed and delivered {len(top_articles)} articles.")
    else:
        print("\n⚠️ No articles matched your filter criteria today.")
        print("Tips: Adjust threshold, region, or content type.")

    print(f"\n✅ All done in {total_time:.2f}s.")

if __name__ == "__main__":
    main()