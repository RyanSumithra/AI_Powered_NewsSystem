import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()  # Load .env variables

EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))


def send_email(articles, topic="News", recipients=None):
    if not recipients:
        print("❌ No recipients provided. Skipping email.")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📰 Top {len(articles)} {topic.title()} Articles"
    msg["From"] = EMAIL_FROM
    msg["To"] = ", ".join(recipients)

    html_body = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Newsletter</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #1a1a1a;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            
            .container {{
                max-width: 680px;
                margin: 0 auto;
                background: #ffffff;
                border-radius: 16px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            
            .header {{
                background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
                padding: 40px 30px;
                text-align: center;
                position: relative;
                overflow: hidden;
            }}
            
            .header::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.1"/><circle cx="50" cy="10" r="0.5" fill="white" opacity="0.15"/><circle cx="20" cy="60" r="0.5" fill="white" opacity="0.15"/><circle cx="80" cy="30" r="0.5" fill="white" opacity="0.15"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
            }}
            
            .header h1 {{
                color: white;
                font-size: 28px;
                font-weight: 700;
                margin-bottom: 8px;
                position: relative;
                z-index: 1;
            }}
            
            .header p {{
                color: rgba(255,255,255,0.9);
                font-size: 16px;
                font-weight: 400;
                position: relative;
                z-index: 1;
            }}
            
            .content {{
                padding: 40px 30px;
            }}
            
            .article {{
                background: #ffffff;
                border-radius: 12px;
                margin-bottom: 30px;
                border: 1px solid #e5e7eb;
                transition: all 0.3s ease;
                overflow: hidden;
            }}
            
            .article:hover {{
                box-shadow: 0 8px 25px rgba(0,0,0,0.1);
                transform: translateY(-2px);
            }}
            
            .article-image {{
                width: 100%;
                height: 200px;
                object-fit: cover;
                display: block;
            }}
            
            .article-content {{
                padding: 24px;
            }}
            
            .article-title {{
                color: #1a1a1a;
                font-size: 20px;
                font-weight: 600;
                margin-bottom: 12px;
                line-height: 1.4;
            }}
            
            .article-summary {{
                color: #6b7280;
                font-size: 15px;
                line-height: 1.6;
                margin-bottom: 16px;
            }}
            
            .read-more {{
                display: inline-flex;
                align-items: center;
                background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
                color: white;
                text-decoration: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: 500;
                font-size: 14px;
                transition: all 0.3s ease;
            }}
            
            .read-more:hover {{
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4);
            }}
            
            .read-more::after {{
                content: '→';
                margin-left: 8px;
                transition: transform 0.3s ease;
            }}
            
            .read-more:hover::after {{
                transform: translateX(2px);
            }}
            
            .footer {{
                background: #f8fafc;
                padding: 30px;
                text-align: center;
                border-top: 1px solid #e5e7eb;
            }}
            
            .footer p {{
                color: #6b7280;
                font-size: 14px;
                margin-bottom: 8px;
            }}
            
            .footer .timestamp {{
                color: #9ca3af;
                font-size: 12px;
            }}
            
            .divider {{
                height: 1px;
                background: linear-gradient(90deg, transparent, #e5e7eb, transparent);
                margin: 20px 0;
            }}
            
            @media (max-width: 600px) {{
                .container {{
                    margin: 10px;
                    border-radius: 12px;
                }}
                
                .header {{
                    padding: 30px 20px;
                }}
                
                .header h1 {{
                    font-size: 24px;
                }}
                
                .content {{
                    padding: 30px 20px;
                }}
                
                .article-content {{
                    padding: 20px;
                }}
                
                .article-title {{
                    font-size: 18px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📰 Top {len(articles)} {topic.title()} Articles</h1>
                <p>Your curated news digest, delivered fresh</p>
            </div>
            
            <div class="content">
    """

    for i, article in enumerate(articles):
        title = article.get("title", "Untitled")
        link = article.get("link", "#")
        summary = article.get("summary", "No summary available.")
        image = article.get("image", "")

        html_body += f"""
                <div class="article">
        """
        
        if image:
            html_body += f"""
                    <img src="{image}" alt="Article Image" class="article-image">
            """
        
        html_body += f"""
                    <div class="article-content">
                        <h2 class="article-title">{title}</h2>
                        <p class="article-summary">{summary}</p>
                        <a href="{link}" class="read-more">Read Full Article</a>
                    </div>
                </div>
        """
        
        if i < len(articles) - 1:
            html_body += '<div class="divider"></div>'

    from datetime import datetime
    current_time = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    html_body += f"""
            </div>
            
            <div class="footer">
                <p>Thank you for reading our newsletter!</p>
                <p class="timestamp">Sent on {current_time}</p>
            </div>
        </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.sendmail(EMAIL_FROM, recipients, msg.as_string())
        print(f"📧 Email sent successfully to: {', '.join(recipients)}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")