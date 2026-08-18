# 🌍 GeoPulse AI

GeoPulse AI is a Telegram bot that monitors geopolitical news and uses AI-based sentiment analysis to classify news as positive, negative, or neutral.

The project was created as a practical application of my learning in Artificial Intelligence and Python development.

## 🚀 Features

- 📰 Fetches recent geopolitical news
- 🤖 Analyzes the sentiment of news headlines
- 📊 Classifies news as:
  - 🟢 Positive
  - 🔴 Negative
  - ⚪ Neutral
- 📱 Sends results directly through Telegram
- 🔄 Can automatically check for new news
- 🔐 Uses environment variables to protect API keys and bot credentials

## 🧠 How It Works

1. The bot requests recent news from a news API.
2. It filters the news for geopolitical topics.
3. The news headline and description are analyzed.
4. The AI/sentiment analysis determines whether the news is positive, negative, or neutral.
5. The result is sent to the user through Telegram.

## 🛠️ Technologies

- Python
- Telegram Bot API
- News API
- Natural Language Processing / Sentiment Analysis
- Python-Telegram-Bot

## 📂 Project Structure

```text
GeoPulse-AI/
│
├── main.py
├── README.md
└── .gitignore
