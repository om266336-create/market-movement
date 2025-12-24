# Market Movement Prediction using Sentiment Analysis

A web application that predicts market movement (Bullish, Bearish, Neutral) based on sentiment analysis of financial news or headlines.

## Features

- Input financial news or headlines
- Sentiment analysis using pre-trained FinBERT model
- Market movement prediction
- Confidence score display
- Visual sentiment polarity chart

## Tech Stack

- Backend: Flask (Python)
- NLP: HuggingFace Transformers (FinBERT)
- Frontend: HTML, CSS, JavaScript
- Dataset: Financial PhraseBank (HuggingFace)

## Installation

1. Clone or download the project.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the Application

1. Run the Flask app:
   ```
   python app.py
   ```
2. Open your browser and go to `http://127.0.0.1:5000/`

## How It Works

The application uses the FinBERT model, pre-trained on financial texts, to analyze sentiment. The sentiment labels (positive, negative, neutral) are mapped directly to market predictions:

- Positive sentiment → Bullish
- Negative sentiment → Bearish
- Neutral sentiment → Neutral

The confidence level is the model's probability score for the predicted label.

## Sample Input & Output

**Input:** "Apple Inc. reports record quarterly profits, stock surges."

**Output:**
- Sentiment: Positive
- Score: 0.9876
- Confidence: 98.76%
- Market Prediction: Bullish

## Project Structure

- `app.py`: Main Flask application
- `frontend/`: HTML, CSS, JS files
- `requirements.txt`: Python dependencies
- `dataset/`: (Auto-loaded)
- `model/`: (Auto-cached)

## Notes

- The model and dataset are automatically downloaded on first run.
- No manual training required.
- Everything runs locally.
