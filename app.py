from flask import Flask, request, jsonify, send_from_directory
from transformers import pipeline
import yfinance as yf
import re
import os

app = Flask(__name__)

# ------------------ LOAD MODEL ------------------
print("Loading FinBERT model... Please wait (first run may take several minutes)")
sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="ProsusAI/finbert"
)
print("FinBERT model loaded successfully")

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
            result = sentiment_pipeline(para[:512])[0]
            sentiments.append(result['label'].lower())
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
    result = sentiment_pipeline(text[:512])[0]
    label = result['label'].lower()
    score = result['score']
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

# ------------------ STOCK API ------------------
@app.route('/stock/<symbol>')
def get_stock(symbol):
    period = request.args.get('period', '1mo')
    
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        
        current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
        previous_close = info.get('previousClose', current_price)
        change = current_price - previous_close
        change_percent = (change / previous_close * 100) if previous_close else 0
        
        hist = ticker.history(period=period)
        
        if hist.empty:
            return jsonify({"error": "No data found for symbol"}), 404
        
        return jsonify({
            "symbol": symbol.upper(),
            "name": info.get('shortName', symbol.upper()),
            "price": round(current_price, 2),
            "change": round(change, 2),
            "changePercent": round(change_percent, 2),
            "dates": hist.index.strftime('%Y-%m-%d').tolist(),
            "prices": hist['Close'].round(2).tolist(),
            "volume": hist['Volume'].tolist(),
            "high": hist['High'].round(2).tolist(),
            "low": hist['Low'].round(2).tolist()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ------------------ RUN SERVER ------------------
if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(host="127.0.0.1", port=5000, debug=True)
