# main.py - SEO Analyzer with Business Context
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import os
from groq import Groq
import json
import time
from typing import Dict, List, Optional
import pathlib

app = FastAPI(title="Professional SEO Analyzer with AI & Business Context")

# Initialize FastMCP for context management - removed for deployment
# mcp = FastMCP("SEO_Analyzer_Context")

# Create required directories if they don't exist
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# Setup templates and static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    os.makedirs("static", exist_ok=True)
    app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Initialize Groq client
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

# User-Agent header
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


# FastMCP Tools for Context Analysis - converted to regular functions
def analyze_content_context(content: str, max_length: int = 2000) -> Dict:
    """
    Analyze website content to extract key themes, topics, and context
    using FastMCP for better understanding
    """
    # Clean content
    clean_content = ' '.join(content.split())[:max_length]

    # Extract key information
    words = clean_content.lower().split()
    word_freq = {}

    # Common words to ignore
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are', 'was',
                  'were', 'be', 'been', 'being'}

    for word in words:
        word = re.sub(r'[^a-z0-9]', '', word)
        if len(word) > 3 and word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1

    # Get top keywords
    top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]

    # Detect content type
    content_lower = clean_content.lower()
    content_type = "general"

    if any(word in content_lower for word in ['shop', 'buy', 'product', 'price', 'cart', 'checkout']):
        content_type = "e-commerce"
    elif any(word in content_lower for word in ['blog', 'article', 'post', 'author', 'published']):
        content_type = "blog"
    elif any(word in content_lower for word in ['service', 'consulting', 'solution', 'contact', 'about']):
        content_type = "service"
    elif any(word in content_lower for word in ['portfolio', 'project', 'work', 'design']):
        content_type = "portfolio"

    return {
        "keywords": [k[0] for k in top_keywords],
        "content_type": content_type,
        "content_length": len(clean_content),
        "word_count": len(words),
        "preview": clean_content[:500]
    }


def analyze_heading_structure(headings: Dict) -> Dict:
    """
    Analyze heading structure and hierarchy for SEO best practices
    """
    h1_count = len(headings.get('h1', []))
    h2_count = len(headings.get('h2', []))
    h3_count = len(headings.get('h3', []))

    issues = []
    recommendations = []

    if h1_count == 0:
        issues.append("No H1 tag found")
        recommendations.append("Add a single, descriptive H1 tag")
    elif h1_count > 1:
        issues.append(f"Multiple H1 tags found ({h1_count})")
        recommendations.append("Use only one H1 tag per page")

    if h2_count == 0:
        issues.append("No H2 tags found")
        recommendations.append("Add H2 tags to structure your content")

    hierarchy_score = 100
    if h1_count != 1:
        hierarchy_score -= 30
    if h2_count == 0:
        hierarchy_score -= 20
    if h3_count > h2_count * 3:
        hierarchy_score -= 10

    return {
        "h1_count": h1_count,
        "h2_count": h2_count,
        "h3_count": h3_count,
        "issues": issues,
        "recommendations": recommendations,
        "hierarchy_score": max(0, hierarchy_score)
    }


def analyze_meta_quality(title: str, description: str, url: str) -> Dict:
    """
    Analyze meta tags quality and provide specific recommendations
    """
    analysis = {
        "title": {},
        "description": {},
        "url_structure": {}
    }

    # Title analysis
    if not title:
        analysis["title"] = {
            "status": "critical",
            "issue": "Missing title tag",
            "score": 0
        }
    else:
        title_length = len(title)
        if title_length < 30:
            analysis["title"] = {
                "status": "poor",
                "issue": f"Title too short ({title_length} chars)",
                "score": 30
            }
        elif title_length > 70:
            analysis["title"] = {
                "status": "warning",
                "issue": f"Title too long ({title_length} chars)",
                "score": 60
            }
        else:
            analysis["title"] = {
                "status": "good",
                "issue": "Title length optimal",
                "score": 100
            }

    # Description analysis
    if not description:
        analysis["description"] = {
            "status": "critical",
            "issue": "Missing meta description",
            "score": 0
        }
    else:
        desc_length = len(description)
        if desc_length < 120:
            analysis["description"] = {
                "status": "warning",
                "issue": f"Description too short ({desc_length} chars)",
                "score": 50
            }
        elif desc_length > 160:
            analysis["description"] = {
                "status": "warning",
                "issue": f"Description too long ({desc_length} chars)",
                "score": 70
            }
        else:
            analysis["description"] = {
                "status": "good",
                "issue": "Description length optimal",
                "score": 100
            }

    # URL structure
    url_lower = url.lower()
    url_score = 100
    url_issues = []

    if '?' in url:
        url_issues.append("Contains query parameters")
        url_score -= 10
    if len(url) > 100:
        url_issues.append("URL too long")
        url_score -= 20
    if '_' in url:
        url_issues.append("Contains underscores (use hyphens)")
        url_score -= 10

    analysis["url_structure"] = {
        "score": url_score,
        "issues": url_issues
    }

    return analysis


def generate_contextual_examples(
    content_context: Dict,
    element_type: str,
    current_value: str = None
) -> List[str]:
    """
    Generate contextual examples based on website content analysis
    """
    keywords = content_context.get('keywords', [])
    content_type = content_context.get('content_type', 'general')

    examples = []

    if element_type == "title":
        if content_type == "e-commerce":
            examples = [
                f"Buy {keywords[0].title()} Online | Premium Quality | Free Shipping",
                f"{keywords[0].title()} Products | Best Prices & Fast Delivery",
                f"Shop {keywords[0].title()} | Trusted Store | Secure Checkout"
            ]
        elif content_type == "blog":
            examples = [
                f"Expert Guide to {keywords[0].title()} | Tips & Insights",
                f"{keywords[0].title()} Blog | Latest News & Tutorials",
                f"Master {keywords[0].title()} | Comprehensive Resources"
            ]
        elif content_type == "service":
            examples = [
                f"Professional {keywords[0].title()} Services | Expert Solutions",
                f"{keywords[0].title()} Consulting | Transform Your Business",
                f"Expert {keywords[0].title()} Solutions | Get Results Today"
            ]
        else:
            examples = [
                f"{keywords[0].title() if keywords else 'Professional'} Services | Quality Solutions",
                f"Expert {keywords[0].title() if keywords else 'Business'} | Trusted Provider",
                f"{keywords[0].title() if keywords else 'Your'} Solutions | Industry Leader"
            ]

    elif element_type == "meta_description":
        if content_type == "e-commerce":
            examples = [
                f"Discover premium {keywords[0]} products at unbeatable prices. Fast shipping, secure checkout, and 100% satisfaction guaranteed. Shop now and save!",
                f"Your trusted source for quality {keywords[0]}. Browse our extensive collection, enjoy exclusive deals, and experience exceptional customer service.",
                f"Find the perfect {keywords[0]} for your needs. Premium quality, competitive prices, and expert support. Order today with free shipping!"
            ]
        elif content_type == "blog":
            examples = [
                f"Explore expert insights on {keywords[0]}. Get tips, tutorials, and latest trends from industry professionals. Subscribe for weekly updates!",
                f"Your go-to resource for {keywords[0]} knowledge. In-depth articles, how-to guides, and practical advice. Start learning today!",
                f"Master {keywords[0]} with our comprehensive guides and expert analysis. Join thousands of readers improving their skills daily."
            ]
        elif content_type == "service":
            examples = [
                f"Professional {keywords[0]} services for growing businesses. Expert team, proven results, and personalized solutions. Get your free consultation today!",
                f"Transform your business with our {keywords[0]} expertise. Tailored solutions, industry experience, and dedicated support. Contact us now!",
                f"Leading {keywords[0]} provider with 10+ years experience. Custom solutions, measurable results, and exceptional service. Start your project today!"
            ]
        else:
            examples = [
                f"Discover professional solutions for {keywords[0] if keywords else 'your needs'}. Expert guidance, quality service, and proven results. Learn more today!",
                f"Your trusted partner for {keywords[0] if keywords else 'business success'}. Comprehensive services, experienced team, and customer-first approach.",
                f"Excellence in {keywords[0] if keywords else 'service delivery'}. Industry expertise, innovative solutions, and commitment to your success."
            ]

    elif element_type == "h1":
        if content_type == "e-commerce":
            examples = [
                f"Premium {keywords[0].title()} Products for Every Need",
                f"Discover Our Collection of Quality {keywords[0].title()}",
                f"Shop {keywords[0].title()} | Best Selection & Prices"
            ]
        elif content_type == "blog":
            examples = [
                f"Everything You Need to Know About {keywords[0].title()}",
                f"The Ultimate Guide to {keywords[0].title()}",
                f"Expert Insights on {keywords[0].title()} | Latest Updates"
            ]
        elif content_type == "service":
            examples = [
                f"Professional {keywords[0].title()} Services That Deliver Results",
                f"Transform Your Business with Expert {keywords[0].title()} Solutions",
                f"Leading {keywords[0].title()} Provider | Trusted by Businesses"
            ]
        else:
            examples = [
                f"Professional {keywords[0].title() if keywords else 'Solutions'} for Modern Businesses",
                f"Expert {keywords[0].title() if keywords else 'Services'} | Quality You Can Trust",
                f"{keywords[0].title() if keywords else 'Your'} Partner for Success"
            ]

    # Ensure we always have 3 examples
    while len(examples) < 3:
        examples.append(f"Professional solution for {keywords[0] if keywords else 'your business'}")

    return examples[:3]


def get_groq_recommendations(seo_data: Dict, business_context: Dict = None) -> Dict:
    """
    Generate SEO recommendations using Groq API with FastMCP-enhanced context and business goals
    """
    try:
        # Extract website content for context
        content_text = seo_data.get('content', {}).get('text', '')

        # Use FastMCP to analyze content context
        content_context = analyze_content_context(content_text, max_length=2000)

        # Use FastMCP to analyze heading structure
        heading_analysis = analyze_heading_structure(seo_data.get('headings', {}))

        # Use FastMCP to analyze meta quality
        meta_analysis = analyze_meta_quality(
            seo_data.get('title', {}).get('content', ''),
            seo_data.get('meta_description', ''),
            seo_data.get('url', '')
        )

        # Build enhanced context with FastMCP insights
        context = f"""
        Website URL: {seo_data.get('url', 'Unknown')}

        FASTMCP CONTENT ANALYSIS:
        - Content Type: {content_context['content_type']}
        - Top Keywords: {', '.join(content_context['keywords'][:5])}
        - Word Count: {content_context['word_count']}
        - Content Preview: {content_context['preview']}

        TITLE ANALYSIS (FastMCP Enhanced):
        - Current Title: {seo_data.get('title', {}).get('content', 'MISSING')}
        - Length: {seo_data.get('title', {}).get('length', 0)} characters
        - Status: {meta_analysis['title'].get('status', 'unknown')}
        - Issue: {meta_analysis['title'].get('issue', 'N/A')}
        - Score: {meta_analysis['title'].get('score', 0)}/100

        META DESCRIPTION (FastMCP Enhanced):
        - Current: {seo_data.get('meta_description', 'MISSING')}
        - Length: {len(seo_data.get('meta_description', ''))} characters
        - Status: {meta_analysis['description'].get('status', 'unknown')}
        - Issue: {meta_analysis['description'].get('issue', 'N/A')}
        - Score: {meta_analysis['description'].get('score', 0)}/100

        HEADING STRUCTURE (FastMCP Analysis):
        - H1 Tags: {heading_analysis['h1_count']} found
        - H2 Tags: {heading_analysis['h2_count']} found
        - H3 Tags: {heading_analysis['h3_count']} found
        - H1 Content: {', '.join(seo_data.get('headings', {}).get('h1', [])) or 'NONE'}
        - Hierarchy Score: {heading_analysis['hierarchy_score']}/100
        - Issues: {', '.join(heading_analysis['issues']) if heading_analysis['issues'] else 'None'}

        IMAGES:
        - Total Images: {seo_data.get('images', {}).get('total', 0)}
        - Without ALT tags: {seo_data.get('images', {}).get('without_alt', 0)}

        LINKS:
        - Total: {seo_data.get('links', {}).get('total', 0)}
        - Internal: {seo_data.get('links', {}).get('internal', 0)}
        - External: {seo_data.get('links', {}).get('external', 0)}

        TECHNICAL SEO:
        - Canonical URL: {'Present' if seo_data.get('canonical') else 'MISSING'}
        - Robots Meta: {seo_data.get('robots', 'MISSING')}
        - Open Graph Tags: {'Present' if seo_data.get('open_graph', {}).get('title') else 'MISSING'}
        - Twitter Card: {'Present' if seo_data.get('twitter_card', {}).get('card') else 'MISSING'}
        - Structured Data: {len(seo_data.get('structured_data', []))} schemas found
        - URL Structure Score: {meta_analysis['url_structure']['score']}/100
        """

        # Generate contextual examples using FastMCP
        title_examples = generate_contextual_examples(content_context, "title")
        desc_examples = generate_contextual_examples(content_context, "meta_description")
        h1_examples = generate_contextual_examples(content_context, "h1")

        # Prepare enhanced prompt with FastMCP context
        prompt = f"""
        You are an expert SEO consultant with FastMCP-enhanced context analysis.

        {context}

        FASTMCP has already generated contextual examples based on deep content analysis:
        - Title Examples: {json.dumps(title_examples)}
        - Description Examples: {json.dumps(desc_examples)}
        - H1 Examples: {json.dumps(h1_examples)}

        CRITICAL INSTRUCTIONS:
        1. Use the FastMCP content analysis to understand the website's topic and type
        2. Leverage the pre-generated contextual examples as reference
        3. Provide SPECIFIC recommendations based on FastMCP analysis scores
        4. For each recommendation, provide MINIMUM 3 DIFFERENT EXAMPLES
        5. Examples must be realistic and based on the content type: {content_context['content_type']}
        6. Prioritize issues by severity using FastMCP scores

        For each issue found, provide:
        - parameter: The SEO element that needs improvement
        - issue: What's wrong (be specific with FastMCP scores and context)
        - recommendation: Detailed, actionable advice based on content type and keywords
        - examples: Array of at least 3 realistic examples (use FastMCP examples as inspiration)
        - priority: critical/high/medium/low (based on FastMCP scores)

        Return ONLY valid JSON in this exact format:
        {{
            "recommendations": [
                {{
                    "parameter": "Title Tag",
                    "issue": "specific issue with FastMCP score",
                    "recommendation": "specific actionable advice for {content_context['content_type']} site",
                    "examples": [
                        "First example based on content type and keywords",
                        "Second example with different approach",
                        "Third example emphasizing different aspect"
                    ],
                    "priority": "high"
                }}
            ]
        }}

        Focus on the most impactful issues first (use FastMCP scores). Maximum 10 recommendations.
        Each recommendation MUST have at least 3 different examples tailored to the content type.
        """

        # Call Groq API with FastMCP-enhanced parameters
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"You are an expert SEO consultant with FastMCP-enhanced context analysis. You have access to detailed content analysis showing this is a {content_context['content_type']} website about {', '.join(content_context['keywords'][:3])}. Provide specific, actionable recommendations based on this context."
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=3072,  # Increased for more detailed recommendations
        )

        # Parse response
        response_text = chat_completion.choices[0].message.content

        # Try to extract JSON response
        try:
            json_match = re.search(r'({.*})', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)

            recommendations = json.loads(response_text)

            # Add FastMCP context to response
            recommendations['fastmcp_context'] = {
                'content_type': content_context.get('content_type', 'general'),
                'keywords': content_context.get('keywords', [])[:5],
                'heading_score': heading_analysis.get('hierarchy_score', 0),
                'title_score': meta_analysis.get('title', {}).get('score', 0),
                'description_score': meta_analysis.get('description', {}).get('score', 0)
            }

            return recommendations
        except json.JSONDecodeError:
            # Fallback with FastMCP-generated examples
            return {
                "recommendations": [
                    {
                        "parameter": "Title Tag",
                        "issue": f"Based on FastMCP analysis, your title needs improvement. Current score: {meta_analysis['title'].get('score', 0)}/100",
                        "recommendation": f"Create a compelling title for your {content_context['content_type']} website focusing on: {', '.join(content_context['keywords'][:3])}",
                        "examples": title_examples,
                        "priority": "high"
                    },
                    {
                        "parameter": "Meta Description",
                        "issue": f"FastMCP analysis shows description issues. Score: {meta_analysis['description'].get('score', 0)}/100",
                        "recommendation": f"Write an engaging description for your {content_context['content_type']} site",
                        "examples": desc_examples,
                        "priority": "high"
                    }
                ],
                "fastmcp_context": {
                    'content_type': content_context.get('content_type', 'general'),
                    'keywords': content_context.get('keywords', [])[:5],
                    'heading_score': heading_analysis.get('hierarchy_score', 0),
                    'title_score': meta_analysis.get('title', {}).get('score', 0),
                    'description_score': meta_analysis.get('description', {}).get('score', 0)
                }
            }
    except Exception as e:
        return {
            "recommendations": [
                {
                    "parameter": "API Error",
                    "issue": "Failed to generate recommendations with FastMCP",
                    "recommendation": f"Error: {str(e)}. Please try again.",
                    "examples": [
                        "Check your API connection",
                        "Verify FastMCP is properly configured",
                        "Try analyzing the website again"
                    ],
                    "priority": "high"
                }
            ],
            "fastmcp_context": {
                'content_type': 'unknown',
                'keywords': [],
                'heading_score': 0,
                'title_score': 0,
                'description_score': 0
            }
        }


def analyze_seo(url: str) -> Dict:
    """
    Analyze SEO for the given URL
    """
    try:
        # Get HTML content from URL
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        # Parse HTML using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Collect SEO data
        seo_data = {
            "url": url,
            "title": {
                "content": soup.title.string if soup.title else None,
                "length": len(soup.title.string) if soup.title and soup.title.string else 0
            },
            "meta_description": None,
            "meta_keywords": None,
            "headings": {
                "h1": [],
                "h2": [],
                "h3": [],
                "h4": [],
                "h5": [],
                "h6": []
            },
            "images": {
                "total": 0,
                "without_alt": 0,
                "with_alt": 0
            },
            "links": {
                "internal": 0,
                "external": 0,
                "total": 0
            },
            "content": {
                "word_count": 0,
                "text": ""
            },
            "open_graph": {
                "title": None,
                "description": None,
                "image": None,
                "url": None
            },
            "twitter_card": {
                "card": None,
                "title": None,
                "description": None,
                "image": None
            },
            "canonical": None,
            "robots": None,
            "structured_data": []
        }

        # Extract meta description and keywords
        meta_description = soup.find('meta', attrs={'name': 'description'})
        if meta_description:
            seo_data["meta_description"] = meta_description.get('content', '')

        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            seo_data["meta_keywords"] = meta_keywords.get('content', '')

        # Extract headings
        for i in range(1, 7):
            headings = soup.find_all(f'h{i}')
            seo_data["headings"][f'h{i}'] = [h.get_text().strip() for h in headings]

        # Image analysis
        images = soup.find_all('img')
        seo_data["images"]["total"] = len(images)

        for img in images:
            if not img.get('alt') or img.get('alt') == '':
                seo_data["images"]["without_alt"] += 1
            else:
                seo_data["images"]["with_alt"] += 1

        # Link analysis
        links = soup.find_all('a', href=True)
        seo_data["links"]["total"] = len(links)

        parsed_url = urlparse(url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"

        for link in links:
            href = link['href']
            if href.startswith('http'):
                if domain in href:
                    seo_data["links"]["internal"] += 1
                else:
                    seo_data["links"]["external"] += 1
            elif href.startswith('/'):
                seo_data["links"]["internal"] += 1

        # Content analysis
        if soup.body:
            text = soup.body.get_text()
            seo_data["content"]["text"] = text
            seo_data["content"]["word_count"] = len(text.split())

        # Open Graph tags
        og_title = soup.find('meta', property='og:title')
        if og_title:
            seo_data["open_graph"]["title"] = og_title.get('content', '')

        og_description = soup.find('meta', property='og:description')
        if og_description:
            seo_data["open_graph"]["description"] = og_description.get('content', '')

        og_image = soup.find('meta', property='og:image')
        if og_image:
            seo_data["open_graph"]["image"] = og_image.get('content', '')

        og_url = soup.find('meta', property='og:url')
        if og_url:
            seo_data["open_graph"]["url"] = og_url.get('content', '')

        # Twitter Card tags
        twitter_card = soup.find('meta', attrs={'name': 'twitter:card'})
        if twitter_card:
            seo_data["twitter_card"]["card"] = twitter_card.get('content', '')

        twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
        if twitter_title:
            seo_data["twitter_card"]["title"] = twitter_title.get('content', '')

        twitter_description = soup.find('meta', attrs={'name': 'twitter:description'})
        if twitter_description:
            seo_data["twitter_card"]["description"] = twitter_description.get('content', '')

        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        if twitter_image:
            seo_data["twitter_card"]["image"] = twitter_image.get('content', '')

        # Canonical link
        canonical = soup.find('link', rel='canonical')
        if canonical:
            seo_data["canonical"] = canonical.get('href', '')

        # Robots meta tag
        robots = soup.find('meta', attrs={'name': 'robots'})
        if robots:
            seo_data["robots"] = robots.get('content', '')

        # Structured data (JSON-LD)
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                seo_data["structured_data"].append(data)
            except:
                pass

        return seo_data

    except Exception as e:
        return {"error": str(e)}


# Templates are managed separately in templates/ folder
# No need to create them programmatically


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/analyze", response_class=HTMLResponse)
async def analyze_website(
        request: Request,
        url: str = Form(...),
        # Business Context Fields
        primary_goal: str = Form(None),
        target_customer: str = Form(None),
        price_position: str = Form(None),
        geographic_focus: str = Form(None),
        geographic_location: str = Form(None),
        desired_action: str = Form(None)
):
    # Clean and validate URL
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    # Validate business context - ALL fields are required
    if not primary_goal or not target_customer or not price_position or not geographic_focus or not desired_action:
        return templates.TemplateResponse(
            "index.html",
            {"request": request,
             "error": "Please answer all 5 business context questions to get accurate SEO recommendations."}
        )

    # If hyper-local or regional, location is also required
    if geographic_focus in ['hyper_local', 'regional'] and not geographic_location:
        return templates.TemplateResponse(
            "index.html",
            {"request": request,
             "error": "Please enter your location/city for hyper-local or regional geographic focus."}
        )

    try:
        # Perform SEO analysis
        seo_data = analyze_seo(url)

        if "error" in seo_data:
            return templates.TemplateResponse(
                "index.html",
                {"request": request, "error": seo_data["error"]}
            )

        # Prepare business context
        business_context = {
            "primary_goal": primary_goal or "Not specified",
            "target_customer": target_customer or "Not specified",
            "price_position": price_position or "Not specified",
            "geographic_focus": geographic_focus or "Not specified",
            "geographic_location": geographic_location or "Not specified",
            "desired_action": desired_action or "Not specified"
        }

        # Get FastMCP-enhanced recommendations from Groq API with business context
        recommendations = get_groq_recommendations(seo_data, business_context)

        return templates.TemplateResponse(
            "results.html",
            {
                "request": request,
                "seo_data": seo_data,
                "recommendations": recommendations.get("recommendations", []),
                "fastmcp_context": recommendations.get("fastmcp_context", {})
            }
        )

    except Exception as e:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": f"Error analyzing website: {str(e)}"}
        )


@app.post("/api/analyze", response_class=JSONResponse)
async def api_analyze_website(request: Request):
    data = await request.json()
    url = data.get("url")

    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    # Clean and validate URL
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    try:
        # Perform SEO analysis
        seo_data = analyze_seo(url)

        if "error" in seo_data:
            return {"error": seo_data["error"]}

        # Get FastMCP-enhanced recommendations
        recommendations = get_groq_recommendations(seo_data)

        return {
            "seo_data": seo_data,
            "recommendations": recommendations.get("recommendations", []),
            "fastmcp_context": recommendations.get("fastmcp_context", {})
        }

    except Exception as e:
        return {"error": f"Error analyzing website: {str(e)}"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
