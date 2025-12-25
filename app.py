from flask import Flask, request, jsonify, send_from_directory
import re
import os
import requests
import yfinance as yf

app = Flask(__name__)

# ------------------ LOAD MODEL ------------------
# REFACTORED FOR VERCEL: Using Hugging Face Inference API instead of local model
# This drastically reduces the bundle size (< 250MB) 
import requests

# UPDATED: Old URL 'api-inference.huggingface.co' is deprecated.
# New URL is 'router.huggingface.co/hf-inference'
HF_API_URL = "https://router.huggingface.co/hf-inference/models/ProsusAI/finbert"
# Get API token from environment variable (Best practice for Vercel)
HF_API_TOKEN = os.environ.get("HF_API_TOKEN")

if not HF_API_TOKEN:
    print("WARNING: HF_API_TOKEN not found in environment variables. Sentiment analysis will fail.")

def query_hf_api(payload):
    """Send text to Hugging Face API for analysis"""
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload)
        
        # Check for non-200 status codes
        if response.status_code != 200:
            # Try to get JSON error if possible
            try:
                error_json = response.json()
                return {"error": f"API Error {response.status_code}: {error_json.get('error', str(error_json))}"}
            except:
                # Fallback to raw text (handling HTML responses etc)
                return {"error": f"API Error {response.status_code}: {response.text[:200]}"}

        return response.json()
    except Exception as e:
        print(f"API Error: {e}")
        return {"error": str(e)}

print("App initialized in Lightweight Mode (API)")

# ------------------ COMPANY TO TICKER MAPPING ------------------
COMPANY_TICKERS = {
    "apple": "AAPL", "aapl": "AAPL",
    "microsoft": "MSFT", "msft": "MSFT",
    "google": "GOOGL", "alphabet": "GOOGL", "googl": "GOOGL",
    "amazon": "AMZN", "amzn": "AMZN",
    "meta": "META", "facebook": "META",
    "tesla": "TSLA", "tsla": "TSLA",
    "nvidia": "NVDA", "nvda": "NVDA",
    "netflix": "NFLX", "nflx": "NFLX",
    "adobe": "ADBE", "intel": "INTC", "amd": "AMD",
    "ibm": "IBM", "oracle": "ORCL", "salesforce": "CRM",
    "paypal": "PYPL", "uber": "UBER", "spotify": "SPOT",
    "jpmorgan": "JPM", "jp morgan": "JPM",
    "goldman sachs": "GS", "goldman": "GS",
    "bank of america": "BAC", "wells fargo": "WFC",
    "visa": "V", "mastercard": "MA",
    "walmart": "WMT", "target": "TGT", "costco": "COST",
    "nike": "NKE", "starbucks": "SBUX",
    "mcdonald": "MCD", "mcdonalds": "MCD",
    "coca cola": "KO", "coca-cola": "KO", "coke": "KO",
    "pepsi": "PEP", "pepsico": "PEP",
    "disney": "DIS", "walt disney": "DIS",
    "pfizer": "PFE", "moderna": "MRNA", "merck": "MRK",
    "boeing": "BA", "ford": "F", "gm": "GM", "general motors": "GM",
    "exxon": "XOM", "chevron": "CVX",
    "berkshire": "BRK-B", "berkshire hathaway": "BRK-B",
}

# ------------------ IMPACT KEYWORDS ------------------
BULLISH_KEYWORDS = [
    'growth', 'earnings', 'profit', 'surge', 'soar', 'record', 'beat', 'exceed',
    'bullish', 'rally', 'gain', 'rise', 'boost', 'strong', 'outperform', 'upgrade',
    'buy', 'optimistic', 'revenue', 'success', 'innovation', 'expansion', 'dividend'
]

BEARISH_KEYWORDS = [
    'loss', 'decline', 'drop', 'fall', 'crash', 'plunge', 'miss', 'layoff',
    'bearish', 'sell', 'downgrade', 'weak', 'risk', 'debt', 'lawsuit', 'scandal',
    'recession', 'inflation', 'warning', 'bankruptcy', 'cut', 'slump', 'concern'
]

def extract_ticker(text):
    """Extract stock ticker from text"""
    text_lower = text.lower()
    
    ticker_pattern = r'\b([A-Z]{1,5})\b'
    explicit_tickers = re.findall(ticker_pattern, text)
    
    for ticker in explicit_tickers:
        if ticker in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 
                      'NFLX', 'JPM', 'BAC', 'WMT', 'DIS', 'KO', 'PEP', 'NKE']:
            return ticker
    
    for company, ticker in COMPANY_TICKERS.items():
        if company in text_lower:
            return ticker
    
    return None

def get_confidence_level(confidence):
    """Convert confidence % to human-readable level"""
    if confidence >= 80:
        return {"level": "Very High", "color": "#00d48a"}
    elif confidence >= 60:
        return {"level": "High", "color": "#667eea"}
    elif confidence >= 40:
        return {"level": "Medium", "color": "#ffb74d"}
    else:
        return {"level": "Low", "color": "#ff5252"}

def calculate_impact_score(text, sentiment, confidence):
    """Calculate Market Impact Score (-100 to +100)"""
    text_lower = text.lower()
    
    # Base score from sentiment
    if sentiment == 'positive':
        base_score = confidence
    elif sentiment == 'negative':
        base_score = -confidence
    else:
        base_score = 0
    
    # Keyword multiplier
    bullish_count = sum(1 for kw in BULLISH_KEYWORDS if kw in text_lower)
    bearish_count = sum(1 for kw in BEARISH_KEYWORDS if kw in text_lower)
    keyword_boost = (bullish_count - bearish_count) * 5
    
    # Text length factor (longer = more impactful, up to 20% boost)
    length_factor = min(len(text) / 500, 0.2)
    
    # Calculate final score
    score = base_score + keyword_boost
    score = score * (1 + length_factor)
    score = max(-100, min(100, score))  # Clamp to -100 to +100
    
    # Determine impact level
    abs_score = abs(score)
    if abs_score >= 70:
        level = "Strong"
    elif abs_score >= 40:
        level = "Moderate"
    else:
        level = "Mild"
    
    direction = "Bullish" if score > 0 else "Bearish" if score < 0 else "Neutral"
    
    return {
        "score": round(score, 1),
        "level": f"{level} {direction}",
        "bullish_signals": bullish_count,
        "bearish_signals": bearish_count
    }

def generate_investor_insight(sentiment, confidence, impact_score, prediction):
    """Generate AI investor insight text"""
    insights = {
        ("positive", "Very High"): f"Strong bullish sentiment detected with {confidence:.1f}% confidence. Market conditions favor upward momentum. Consider monitoring entry points while staying aware of macroeconomic factors.",
        ("positive", "High"): f"Positive market sentiment with solid confidence. Short-term outlook appears favorable, but prudent investors should maintain diversified positions.",
        ("positive", "Medium"): "Moderately positive signals present. Market sentiment leans bullish but with some uncertainty. Consider waiting for confirmation before major positions.",
        ("positive", "Low"): "Weak positive sentiment detected. Insufficient confidence for actionable insights. Recommend further research.",
        ("negative", "Very High"): f"Strong bearish signals detected with {confidence:.1f}% confidence. Consider risk mitigation strategies and review portfolio exposure.",
        ("negative", "High"): "Significant negative sentiment identified. Short-term headwinds expected. Defensive positioning may be warranted.",
        ("negative", "Medium"): "Moderate bearish indicators present. Exercise caution and monitor for trend confirmation.",
        ("negative", "Low"): "Mild negative sentiment with low confidence. Market impact likely minimal. Continue regular monitoring.",
        ("neutral", "Very High"): "Market sentiment is neutral with high confidence. Sideways movement expected. Range-bound trading strategies may be appropriate.",
        ("neutral", "High"): "Balanced sentiment signals. No strong directional bias detected. Hold current positions pending clearer signals.",
        ("neutral", "Medium"): "Mixed market signals. Insufficient data for directional call. Await further developments.",
        ("neutral", "Low"): "Unclear market sentiment. Recommend gathering additional data points before making decisions.",
    }
    
    conf_level = get_confidence_level(confidence)["level"]
    key = (sentiment, conf_level)
    return insights.get(key, "Analysis complete. Monitor market conditions for updates.")

def analyze_sentiment_trend(text):
    """Analyze sentiment trend across paragraphs"""
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    if len(paragraphs) < 2:
        paragraphs = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 20]
    
    if len(paragraphs) < 2:
        return None
    
    sentiments = []
    for para in paragraphs[:5]:  # Analyze up to 5 paragraphs
        try:
            # API Call
            api_output = query_hf_api({"inputs": para[:512]})
            
            # Handle API list response (it returns a list of lists usually)
            if isinstance(api_output, list) and len(api_output) > 0:
                if isinstance(api_output[0], list): # Nested list [[{...}]]
                   result = api_output[0][0]
                else: # Flat list [{...}]
                   result = api_output[0]
                
                sentiments.append(result['label'].lower())
            else:
                continue
        except:
            continue
    
    if len(sentiments) < 2:
        return None
    
    sentiment_values = {'positive': 1, 'neutral': 0, 'negative': -1}
    values = [sentiment_values.get(s, 0) for s in sentiments]
    
    first_half = sum(values[:len(values)//2]) / max(1, len(values)//2)
    second_half = sum(values[len(values)//2:]) / max(1, len(values) - len(values)//2)
    
    diff = second_half - first_half
    
    if diff > 0.3:
        trend = "Improving"
        emoji = "📈"
    elif diff < -0.3:
        trend = "Declining"
        emoji = "📉"
    else:
        trend = "Stable"
        emoji = "➡️"
    
    return {
        "trend": trend,
        "emoji": emoji,
        "previous": sentiments[0].capitalize() if sentiments else "Unknown",
        "current": sentiments[-1].capitalize() if sentiments else "Unknown",
        "segments_analyzed": len(sentiments)
    }

# ------------------ ROUTES ------------------
@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('frontend', path)

# ------------------ ANALYZE API ------------------
@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()

    if not data or 'text' not in data or not data['text'].strip():
        return jsonify({"error": "Text input is required"}), 400

    text = data['text']
    
    # Check for API Token
    if not HF_API_TOKEN:
        return jsonify({"error": "Configuration Error: HF_API_TOKEN is missing on server."}), 500

    # Call API
    api_response = query_hf_api({"inputs": text[:512]})
    
    # Error handling for API limits or loading
    if isinstance(api_response, dict) and 'error' in api_response:
        return jsonify({"error": f"Model API Error: {api_response.get('error')}"}), 503
        
    # Parse Response
    # API usually returns [[{'label': 'positive', 'score': 0.9}]] or similar
    try:
        if isinstance(api_response, list) and len(api_response) > 0:
             if isinstance(api_response[0], list):
                 result = api_response[0][0]
             else:
                 result = api_response[0]
                 
             label = result['label'].lower()
             score = result['score']
        else:
             return jsonify({"error": "Invalid response from AI Model"}), 500
    except Exception as e:
         return jsonify({"error": f"Parsing Error: {str(e)}"}), 500

    confidence = round(score * 100, 2)

    if label == 'positive':
        prediction = 'Bullish'
    elif label == 'negative':
        prediction = 'Bearish'
    else:
        prediction = 'Neutral'

    sentiment_scores = {"positive": 0.0, "neutral": 0.0, "negative": 0.0}
    sentiment_scores[label] = score

    # Advanced AI metrics
    confidence_info = get_confidence_level(confidence)
    impact = calculate_impact_score(text, label, confidence)
    insight = generate_investor_insight(label, confidence, impact["score"], prediction)
    trend = analyze_sentiment_trend(text)

    # Stock data
    detected_ticker = extract_ticker(text)
    stock_data = None
    
    if detected_ticker:
        try:
            ticker = yf.Ticker(detected_ticker)
            info = ticker.info
            
            current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
            previous_close = info.get('previousClose', current_price)
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close else 0
            
            hist = ticker.history(period='1mo')
            
            if not hist.empty:
                stock_data = {
                    "symbol": detected_ticker,
                    "name": info.get('shortName', detected_ticker),
                    "price": round(current_price, 2),
                    "change": round(change, 2),
                    "changePercent": round(change_percent, 2),
                    "dates": hist.index.strftime('%Y-%m-%d').tolist(),
                    "prices": hist['Close'].round(2).tolist(),
                    "volume": hist['Volume'].tolist(),
                    "high": hist['High'].round(2).tolist(),
                    "low": hist['Low'].round(2).tolist()
                }
        except Exception as e:
            print(f"Error fetching stock data: {e}")

    return jsonify({
        "sentiment": label.capitalize(),
        "confidence": confidence,
        "confidenceLevel": confidence_info,
        "prediction": prediction,
        "scores": sentiment_scores,
        "impact": impact,
        "insight": insight,
        "trend": trend,
        "stock": stock_data
    })

def get_related_stocks(symbol, sector):
    """Get related stocks based on symbol or sector"""
    # Hardcoded popular peers for better quality
    peers = {
        'AAPL': ['MSFT', 'GOOGL', 'AMZN', 'META'],
        'MSFT': ['AAPL', 'GOOGL', 'AMZN', 'ORCL'],
        'GOOGL': ['MSFT', 'META', 'AMZN', 'AAPL'],
        'AMZN': ['WMT', 'GOOGL', 'MSFT', 'TGT'],
        'TSLA': ['F', 'GM', 'RIVN', 'LCID'],
        'NVDA': ['AMD', 'INTC', 'TSM', 'QCOM'],
        'AMD': ['NVDA', 'INTC', 'TSM', 'QCOM'],
        'INTC': ['AMD', 'NVDA', 'TSM', 'QCOM'],
        'NFLX': ['DIS', 'CMCSA', 'WBD', 'PARA'],
        'META': ['GOOGL', 'SNAP', 'PINS', 'TWTR'],
        'JPM': ['BAC', 'WFC', 'C', 'GS'],
        'BAC': ['JPM', 'WFC', 'C', 'GS'],
        'WMT': ['TGT', 'COST', 'AMZN', 'HD'],
        'DIS': ['NFLX', 'CMCSA', 'WBD', 'PARA'],
    }
    
    if symbol in peers:
        return peers[symbol]
    
    # Fallback based on sector if available (simplified)
    if sector == 'Technology':
        return ['AAPL', 'MSFT', 'NVDA', 'ORCL']
    elif sector == 'Financial Services':
        return ['JPM', 'BAC', 'GS', 'MS']
    elif sector == 'Healthcare':
        return ['JNJ', 'PFE', 'UNH', 'LLY']
    elif sector == 'Consumer Cyclical':
        return ['AMZN', 'TSLA', 'HD', 'MCD']
    
    return ['AAPL', 'MSFT', 'GOOGL', 'AMZN'] # Generic fallback

# ------------------ STOCK API ------------------
@app.route('/stock/<symbol>')
def get_stock(symbol):
    period = request.args.get('period', '1mo')
    
    # improved interval selection for different periods
    interval = '1d'
    if period == '1d':
        interval = '5m'
    elif period == '5d':
        interval = '15m'
    elif period == '1mo':
        interval = '90m'
    
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        
        current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
        previous_close = info.get('previousClose', current_price)
        change = current_price - previous_close
        change_percent = (change / previous_close * 100) if previous_close else 0
        
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            return jsonify({"error": "No data found for symbol"}), 404
        
        stock_info = {
            "symbol": symbol.upper(),
            "name": info.get('shortName', symbol.upper()),
            "price": round(current_price, 2),
            "change": round(change, 2),
            "changePercent": round(change_percent, 2),
            "dates": (hist.index.astype('int64') // 10**9).tolist(), # Unix timestamps for JS compatibility
            "prices": hist['Close'].round(2).tolist(),
            "open": hist['Open'].round(2).tolist(),
            "volume": hist['Volume'].tolist(),
            "high": hist['High'].round(2).tolist(),
            "low": hist['Low'].round(2).tolist(),
            # Extended Stats
            "open": info.get('open'),
            "dayHigh": info.get('dayHigh'),
            "dayLow": info.get('dayLow'),
            "mktCap": info.get('marketCap'),
            "peRatio": info.get('trailingPE'),
            "dividendYield": info.get('dividendYield'),
            "fiftyTwoWeekHigh": info.get('fiftyTwoWeekHigh'),
            "fiftyTwoWeekLow": info.get('fiftyTwoWeekLow'),
            "volumeAvg": info.get('averageVolume'),
            "sector": info.get('sector'),
            "industry": info.get('industry'),
            "website": info.get('website'),
            "description": info.get('longBusinessSummary'),
            # Lists
            "news": ticker.news[:5] if hasattr(ticker, 'news') else [],
            "earnings": ticker.calendar.get('Earnings Date', []) if hasattr(ticker, 'calendar') and isinstance(ticker.calendar, dict) else [],
            "related": get_related_stocks(symbol.upper(), info.get('sector')),
             # Risk Metrics
            "volatility": hist['Close'].pct_change().std() * (252 ** 0.5) * 100 if len(hist) > 1 else 0 # Annualized volatility
        }
        
        return jsonify(stock_info)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ------------------ RUN SERVER ------------------
if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(host="127.0.0.1", port=5000, debug=True)
