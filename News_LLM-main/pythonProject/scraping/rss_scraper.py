import feedparser
import requests
import re
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import html

GOOGLE_NEWS_API_KEY = "41c2a568555d44e1aae14071fe43a3d7"

def clean_title(title: str) -> str:
    if not title:
        return None
    title = re.sub(r'\s+', ' ', title.strip())
    if len(title) < 10 or len(title) > 200:
        return None
    skip_words = ['subscribe', 'login', 'register', 'advertisement', 'menu', 'search', 'newsletter']
    if any(word in title.lower() for word in skip_words):
        return None
    return title

def is_valid_image_url(url: str) -> bool:
    if not url:
        return False
    
    clean_url = url.split('?')[0].lower()
    
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']
    has_extension = any(clean_url.endswith(ext) for ext in image_extensions)
    
    image_patterns = [
        'images', 'img', 'photo', 'pics', 'media', 'upload', 'cdn', 'static',
        'thumb', 'resize', 'crop', 'avatar', 'logo', 'banner'
    ]
    has_pattern = any(pattern in url.lower() for pattern in image_patterns)
    
    try:
        parsed = urlparse(url)
        return (has_extension or has_pattern) and bool(parsed.netloc)
    except:
        return False

def extract_image_from_entry(entry, base_url: str = None) -> str:
    image_url = None
    
    try:
        if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            for thumb in entry.media_thumbnail:
                url = thumb.get('url') or thumb.get('href')
                if is_valid_image_url(url):
                    image_url = url
                    break
        
        if not image_url and hasattr(entry, 'media_content') and entry.media_content:
            for media in entry.media_content:
                url = media.get('url') or media.get('href')
                media_type = media.get('type', '').lower()
                if 'image' in media_type and is_valid_image_url(url):
                    image_url = url
                    break
        
        if not image_url and hasattr(entry, 'enclosures') and entry.enclosures:
            for enc in entry.enclosures:
                url = enc.get('href') or enc.get('url')
                enc_type = enc.get('type', '').lower()
                if 'image' in enc_type and is_valid_image_url(url):
                    image_url = url
                    break
        
        if not image_url:
            content_fields = [
                entry.get('summary', ''),
                entry.get('content', ''),
                entry.get('description', '')
            ]
            
            for content in content_fields:
                if not content:
                    continue
                
                content = html.unescape(str(content))
                
                img_patterns = [
                    r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>',
                    r'<img[^>]+src=([^\s>]+)',
                    r'src=["\']([^"\']*\.(?:jpg|jpeg|png|gif|webp|bmp)(?:\?[^"\']*)?)["\']',
                    r'background-image:\s*url\(["\']?([^"\')\s]+)["\']?\)',
                    r'data-src=["\']([^"\']+)["\']',
                    r'data-lazy-src=["\']([^"\']+)["\']'
                ]
                
                for pattern in img_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        url = match.strip()
                        if is_valid_image_url(url):
                            if base_url and url.startswith('/'):
                                url = urljoin(base_url, url)
                            image_url = url
                            break
                    if image_url:
                        break
                if image_url:
                    break
        
        if not image_url and hasattr(entry, 'links') and entry.links:
            for link in entry.links:
                if link.get('rel') == 'enclosure' and 'image' in link.get('type', ''):
                    url = link.get('href')
                    if is_valid_image_url(url):
                        image_url = url
                        break
        
        if not image_url and hasattr(entry, 'tags') and entry.tags:
            for tag in entry.tags:
                if 'image' in tag.get('term', '').lower():
                    for attr in ['href', 'url', 'src']:
                        url = tag.get(attr)
                        if is_valid_image_url(url):
                            image_url = url
                            break
                if image_url:
                    break
        
        if image_url:
            image_url = image_url.strip('\'"')
            
            if base_url and not image_url.startswith(('http://', 'https://')):
                image_url = urljoin(base_url, image_url)
            
            if not is_valid_image_url(image_url):
                image_url = None
    
    except Exception as e:
        print(f"⚠️ Error extracting image: {e}")
        image_url = None
    
    return image_url

def get_all_available_sources() -> Dict[str, Dict[str, List[Dict]]]:
    """Return all available sources organized by topic and region"""
    return {
        "education": {
            "india": [
                {"name": "Indian Express Education", "url": "https://indianexpress.com/section/education/feed/"},
                {"name": "Hindustan Times Education", "url": "https://www.hindustantimes.com/feeds/rss/education/rssfeed.xml"},
                {"name": "Jagran Josh Education", "url": "https://www.jagranjosh.com/rss-feeds/rssfeed-education.xml"}
            ],
            "global": [
                {"name": "Edutopia", "url": "https://www.edutopia.org/rss.xml"},
                {"name": "BBC Education", "url": "https://feeds.bbci.co.uk/news/education/rss.xml"},
                {"name": "Inside Higher Ed", "url": "https://www.insidehighered.com/rss/news"}
            ]
        },
        "technology": {
            "india": [
                {"name": "Gadgets 360", "url": "https://www.gadgets360.com/rss/news"},
                {"name": "Hindustan Times Tech", "url": "https://tech.hindustantimes.com/rss/tech/news"},
                {"name": "Indian Express Technology", "url": "https://indianexpress.com/section/technology/feed/"}
            ],
            "global": [
                {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml"},
                {"name": "TechCrunch", "url": "https://techcrunch.com/feed/"},
                {"name": "ZDNet", "url": "https://www.zdnet.com/news/rss.xml"}
            ]
        },
        "science": {
            "india": [
                {"name": "The Hindu Science", "url": "https://www.thehindu.com/sci-tech/science/feeder/default.rss"},
                {"name": "Current Affairs", "url": "https://currentaffairs.adda247.com/feed/"},
                {"name": "Down To Earth Science", "url": "https://www.downtoearth.org.in/rss/science"}
            ],
            "global": [
                {"name": "Science Daily", "url": "https://www.sciencedaily.com/rss/top/science.xml"},
                {"name": "Scientific American", "url": "https://rss.sciam.com/ScientificAmerican-News"},
                {"name": "Nature Science", "url": "https://www.nature.com/subjects/science.rss"}
            ]
        },
        "general": [
            {"name": "Times of India Top Stories", "url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"},
            {"name": "The Hindu National News", "url": "https://www.thehindu.com/news/national/feeder/default.rss"},
            {"name": "BBC World News", "url": "https://feeds.bbci.co.uk/news/world/rss.xml"}
        ]
    }

def get_topic_feeds(topic: str, region: str, custom_sources: Optional[List[str]] = None) -> List[str]:
    topic = topic.lower()
    region = region.lower()
    all_sources = get_all_available_sources()

    topic_feeds = all_sources.get(topic, {})
    region_feeds = [feed["url"] for feed in topic_feeds.get(region, [])]
    general_feeds = [feed["url"] for feed in all_sources.get("general", [])]

    if custom_sources:
        # Filter both topic and general feeds by selected sources
        selected_feeds = []
        for feed in topic_feeds.get(region, []) + all_sources.get("general", []):
            if feed["name"] in custom_sources:
                selected_feeds.append(feed["url"])
        return selected_feeds
    
    return region_feeds + general_feeds

def fetch_rss_articles(topic: str, region: str, custom_sources: Optional[List[str]] = None) -> List[Dict]:
    rss_urls = get_topic_feeds(topic, region, custom_sources)
    articles = []
    successful_feeds = 0
    total_images_found = 0

    for url in rss_urls:
        try:
            print(f"📡 Parsing RSS feed: {url}")
            feed = feedparser.parse(url)
            
            if not feed.entries:
                print(f"⚠️ No entries found in {url}")
                continue
                
            successful_feeds += 1
            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            
            for entry in feed.entries:
                title = clean_title(entry.get("title", ""))
                if not title:
                    continue

                image_url = extract_image_from_entry(entry, base_url)
                if image_url:
                    total_images_found += 1

                summary = entry.get("summary", "")
                clean_summary = re.sub(r"<[^<]+?>", "", html.unescape(summary))

                articles.append({
                    "title": title,
                    "link": entry.get("link", ""),
                    "summary": clean_summary,
                    "content": summary,
                    "image": image_url,
                    "source": f"RSS Feed - {urlparse(url).netloc}"
                })

            print(f"✅ Successfully parsed {len(feed.entries)} entries from {urlparse(url).netloc}")

        except Exception as e:
            print(f"❌ Error parsing RSS from {url}: {e}")
            continue

    print(f"📊 RSS Summary: {successful_feeds}/{len(rss_urls)} feeds successful, {total_images_found} images found")
    return articles

def fetch_google_news_articles(topic: str, region: str) -> List[Dict]:
    print("🌐 Fetching from Google News API...")
    try:
        url = f"https://newsapi.org/v2/everything?q={topic}&language=en&pageSize=50&apiKey={GOOGLE_NEWS_API_KEY}"
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            print(f"❌ Google News API error {response.status_code}: {response.text}")
            return []

        data = response.json()
        articles = []
        images_found = 0
        
        for item in data.get("articles", []):
            title = clean_title(item.get("title", ""))
            if not title:
                continue
            
            image_url = item.get("urlToImage", "")
            if image_url and is_valid_image_url(image_url):
                images_found += 1
            else:
                image_url = None
            
            articles.append({
                "title": title,
                "link": item.get("url", ""),
                "summary": item.get("description", ""),
                "content": item.get("content", ""),
                "image": image_url,
                "source": f"Google News - {item.get('source', {}).get('name', 'Unknown')}"
            })
        
        print(f"✅ Google News: {len(articles)} articles, {images_found} with images")
        return articles

    except Exception as e:
        print(f"❌ Exception during Google News fetch: {e}")
        return []

def fetch_articles(topic: str, region: str, custom_sources: Optional[List[str]] = None) -> List[Dict]:
    print(f"\n🚀 Starting article fetching for: {topic} [{region.title()}]")

    rss_articles = fetch_rss_articles(topic, region, custom_sources)
    rss_articles = rss_articles[:200]
    print(f"📡 RSS articles: {len(rss_articles)}")

    google_news_articles = fetch_google_news_articles(topic, region)
    print(f"🌐 Google News articles: {len(google_news_articles)}")

    all_articles = rss_articles + google_news_articles

    seen = set()
    unique_articles = []
    total_with_images = 0
    
    for article in all_articles:
        key = article.get("title", "") + article.get("link", "")
        if key not in seen:
            seen.add(key)
            unique_articles.append(article)
            if article.get("image"):
                total_with_images += 1

    print(f"✅ Final unique articles: {len(unique_articles)}")
    print(f"🖼️ Articles with images: {total_with_images}/{len(unique_articles)} ({total_with_images/len(unique_articles)*100:.1f}%)")
    
    return unique_articles