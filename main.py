import os
import json
import hashlib
import requests

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

NEWS_URL = "https://newsapi.org/v2/everything"

CHECK_INTERVAL = 600  # 10 minutes
MAX_ARTICLES = 10

SEEN_FILE = "seen_news.json"
SUBSCRIBERS_FILE = "subscribers.json"


# =========================================================
# GEOPOLITICAL QUERY
# =========================================================

QUERY = (
    '(war OR conflict OR ceasefire OR sanctions OR '
    'diplomacy OR missile OR military OR invasion OR '
    'NATO OR Russia OR Ukraine OR China OR Iran OR '
    'Israel OR Gaza OR "United States" OR Europe OR '
    'election OR treaty OR escalation)'
)


# =========================================================
# SENTIMENT WORDS
# =========================================================

POSITIVE_WORDS = {
    "peace",
    "ceasefire",
    "agreement",
    "deal",
    "diplomacy",
    "cooperation",
    "reconciliation",
    "truce",
    "negotiation",
    "negotiations",
    "settlement",
    "stability",
    "support",
    "alliance",
    "treaty",
}

NEGATIVE_WORDS = {
    "war",
    "attack",
    "attacked",
    "strike",
    "strikes",
    "missile",
    "bomb",
    "bombing",
    "conflict",
    "invasion",
    "sanctions",
    "killed",
    "death",
    "crisis",
    "escalation",
    "threat",
    "threatens",
    "violence",
    "military",
    "explosion",
    "offensive",
}


# =========================================================
# SENTIMENT ANALYSIS
# =========================================================

def analyze_news(text):

    words = text.lower().split()

    positive = 0
    negative = 0

    for word in words:

        clean = word.strip(
            ".,!?;:\"'()[]{}"
        )

        if clean in POSITIVE_WORDS:
            positive += 1

        if clean in NEGATIVE_WORDS:
            negative += 1

    score = positive - negative

    if score >= 2:
        label = "🟢 POSITIVE"

    elif score <= -2:
        label = "🔴 NEGATIVE"

    else:
        label = "🟡 NEUTRAL"

    return label, score


# =========================================================
# SEEN NEWS DATABASE
# =========================================================

def load_seen():

    if not os.path.exists(SEEN_FILE):
        return set()

    try:

        with open(SEEN_FILE, "r") as file:
            return set(json.load(file))

    except Exception:
        return set()


def save_seen(seen):

    # Keep database from becoming huge
    latest = list(seen)[-1000:]

    with open(SEEN_FILE, "w") as file:
        json.dump(latest, file)


# =========================================================
# SUBSCRIBERS DATABASE
# =========================================================

def load_subscribers():

    if not os.path.exists(SUBSCRIBERS_FILE):
        return set()

    try:

        with open(SUBSCRIBERS_FILE, "r") as file:
            return set(json.load(file))

    except Exception:
        return set()


def save_subscribers(subscribers):

    with open(SUBSCRIBERS_FILE, "w") as file:
        json.dump(list(subscribers), file)


def add_subscriber(chat_id):

    subscribers = load_subscribers()

    subscribers.add(chat_id)

    save_subscribers(subscribers)


def remove_subscriber(chat_id):

    subscribers = load_subscribers()

    subscribers.discard(chat_id)

    save_subscribers(subscribers)


# =========================================================
# NEWS API
# =========================================================

def get_news():

    if not NEWS_API_KEY:
        raise Exception("NEWS_API_KEY is missing")

    headers = {
        "X-Api-Key": NEWS_API_KEY
    }

    params = {
        "q": QUERY,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": MAX_ARTICLES,
        "page": 1,
    }

    response = requests.get(
        NEWS_URL,
        headers=headers,
        params=params,
        timeout=30
    )

    data = response.json()

    if response.status_code != 200:

        error_code = data.get(
            "code",
            "unknown"
        )

        error_message = data.get(
            "message",
            "Unknown News API error"
        )

        raise Exception(
            f"{error_code}: {error_message}"
        )

    if data.get("status") != "ok":

        raise Exception(
            data.get(
                "message",
                "News API returned an error"
            )
        )

    return data.get(
        "articles",
        []
    )


# =========================================================
# CREATE MESSAGE
# =========================================================

def create_news_message(article):

    title = article.get(
        "title",
        "Unknown headline"
    )

    description = article.get(
        "description"
    ) or ""

    url = article.get(
        "url",
        ""
    )

    source = article.get(
        "source",
        {}
    )

    source_name = source.get(
        "name",
        "Unknown"
    )

    published = article.get(
        "publishedAt",
        ""
    )

    # Analyze headline + description
    text_to_analyze = (
        title + " " + description
    )

    sentiment, score = analyze_news(
        text_to_analyze
    )

    message = (
        "🌍 *GEOPULSE AI*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        f"📰 *{title}*\n\n"

        f"📊 Impact: {sentiment}\n"
        f"🧮 Analysis score: `{score}`\n\n"

        f"🌐 Source: `{source_name}`\n"
    )

    if published:

        message += (
            f"🕒 `{published}`\n"
        )

    if description:

        short_description = (
            description[:500]
        )

        message += (
            f"\n📝 {short_description}\n"
        )

    if url:

        message += (
            f"\n🔗 [Read full article]({url})"
        )

    return message


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id

    add_subscriber(chat_id)

    keyboard = [
        [
            InlineKeyboardButton(
                "📰 Check News",
                callback_data="check"
            )
        ],
        [
            InlineKeyboardButton(
                "⏹ Stop Alerts",
                callback_data="stop"
            )
        ],
    ]

    await update.message.reply_text(

        "🌍 *GEOPULSE AI*\n\n"

        "✅ Automatic geopolitical alerts are ON.\n\n"

        "I monitor recent geopolitical news "
        "and classify its potential sentiment "
        "as Positive, Negative, or Neutral.\n\n"

        "⏱ Automatic check: every 10 minutes.\n\n"

        "Commands:\n"
        "/check — Check news now\n"
        "/stop — Stop alerts\n"
        "/start — Enable alerts",

        parse_mode="Markdown",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# STOP
# =========================================================

async def stop(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id

    remove_subscriber(chat_id)

    await update.message.reply_text(

        "⏹ *Automatic alerts stopped.*\n\n"
        "Use /start to enable them again.",

        parse_mode="Markdown"
    )


# =========================================================
# CHECK NOW
# =========================================================

async def check_command(
    update,
    context
):

    await update.message.reply_text(
        "🔄 Checking geopolitical news..."
    )

    await send_news(
        update.effective_chat.id,
        context.bot
    )


# =========================================================
# SEND NEWS
# =========================================================

async def send_news(
    chat_id,
    bot
):

    try:

        articles = get_news()

        if not articles:

            await bot.send_message(
                chat_id,
                "ℹ️ No geopolitical articles found."
            )

            return

        seen = load_seen()

        new_articles = []

        for article in articles:

            title = article.get(
                "title",
                ""
            )

            url = article.get(
                "url",
                ""
            )

            news_id = hashlib.sha256(
                (
                    title + url
                ).encode("utf-8")
            ).hexdigest()

            if news_id not in seen:

                new_articles.append(
                    (
                        article,
                        news_id
                    )
                )

        if not new_articles:

            await bot.send_message(
                chat_id,
                "✅ No new geopolitical news."
            )

            return

        # Send maximum 5
        for article, news_id in new_articles[:5]:

            message = create_news_message(
                article
            )

            await bot.send_message(
                chat_id,
                message,
                parse_mode="Markdown",
                disable_web_page_preview=False
            )

            seen.add(news_id)

        save_seen(seen)

    except Exception as error:

        print(
            "NEWS ERROR:",
            error
        )

        await bot.send_message(
            chat_id,
            "❌ News API error.\n\n"
            f"`{str(error)[:500]}`",
            parse_mode="Markdown"
        )


# =========================================================
# BUTTONS
# =========================================================

async def button_handler(
    update,
    context
):

    query = update.callback_query

    await query.answer()

    chat_id = query.message.chat.id

    if query.data == "check":

        await query.edit_message_text(
            "🔄 Checking geopolitical news..."
        )

        await send_news(
            chat_id,
            context.bot
        )

    elif query.data == "stop":

        remove_subscriber(chat_id)

        await query.edit_message_text(
            "⏹ *Automatic alerts stopped.*\n\n"
            "Use /start to enable them again.",
            parse_mode="Markdown"
        )


# =========================================================
# AUTOMATIC NEWS CHECK
# =========================================================

async def automatic_check(
    context
):

    subscribers = load_subscribers()

    if not subscribers:
        return

    print(
        f"🔎 Checking news for "
        f"{len(subscribers)} subscriber(s)..."
    )

    try:

        articles = get_news()

        if not articles:
            return

        seen = load_seen()

        new_articles = []

        for article in articles:

            title = article.get(
                "title",
                ""
            )

            url = article.get(
                "url",
                ""
            )

            news_id = hashlib.sha256(
                (
                    title + url
                ).encode("utf-8")
            ).hexdigest()

            if news_id not in seen:

                new_articles.append(
                    (
                        article,
                        news_id
                    )
                )

        if not new_articles:

            print(
                "ℹ️ No new articles."
            )

            return

        # Mark as seen
        for _, news_id in new_articles:
            seen.add(news_id)

        save_seen(seen)

        for chat_id in subscribers:

            for article, _ in new_articles[:5]:

                try:

                    message = create_news_message(
                        article
                    )

                    await context.bot.send_message(
                        chat_id,
                        message,
                        parse_mode="Markdown",
                        disable_web_page_preview=False
                    )

                except Exception as error:

                    print(
                        f"Telegram send error "
                        f"{chat_id}: {error}"
                    )

    except Exception as error:

        print(
            "AUTOMATIC NEWS ERROR:",
            error
        )


# =========================================================
# MAIN
# =========================================================

def main():

    if not BOT_TOKEN:

        print(
            "❌ BOT_TOKEN is missing."
        )

        print(
            "Run:"
        )

        print(
            "export BOT_TOKEN='YOUR_BOT_TOKEN'"
        )

        return

    if not NEWS_API_KEY:

        print(
            "❌ NEWS_API_KEY is missing."
        )

        print(
            "Run:"
        )

        print(
            "export NEWS_API_KEY='YOUR_NEWS_API_KEY'"
        )

        return

    application = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CommandHandler(
            "stop",
            stop
        )
    )

    application.add_handler(
        CommandHandler(
            "check",
            check_command
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )

    # Automatic check every 10 minutes
    application.job_queue.run_repeating(
        automatic_check,
        interval=CHECK_INTERVAL,
        first=10
    )

    print(
        "🌍 GeoPulse AI is running..."
    )

    print(
        "📰 News API monitoring: ON"
    )

    application.run_polling()


if __name__ == "__main__":
    main()
