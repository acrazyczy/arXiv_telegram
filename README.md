# 📚 ArXiv Daily Telegram Bot

A lightweight, automated Python bot that fetches the latest research papers from [arXiv](https://arxiv.org/) and pushes them directly to your Telegram chat or channel.

Powered by **GitHub Actions**, this bot runs automatically every day, ensuring you never miss an update in your favorite Computer Science categories (e.g., `cs.GT`, `cs.DS`).

## ✨ Features

* **📅 Daily Updates**: Automatically fetches papers published "today" (filters out old or weekend duplicates).
* **🤖 Serverless**: Runs entirely on GitHub Actions (no VPS required).
* **🧹 Smart Formatting**:
    * Cleans raw HTML/LaTeX from arXiv summaries.
    * Distinguishes between **New** (🆕) and **Updated** (🔄) papers.
    * Displays categories tags (e.g., `cs.GT`).
* **⚙️ Configurable**: Customize categories and summary length via `config.json`.
* **🔒 Secure**: Uses GitHub Secrets to protect your Bot Token and Chat ID.

---

## 📂 Directory Structure

```text
.
├── .github/
│   └── workflows/
│       └── daily_arxiv.yml   # GitHub Actions configuration (Cron schedule)
├── src/
│   ├── __init__.py           # Package marker
│   └── main.py               # Main bot logic
├── config.json               # User configuration (categories, length)
├── .env                      # Secrets for local development (do not commit!)
├── .gitignore                # Git ignore rules
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

---

## ⚙️ Configuration

To run this bot, you need to configure your sensitive secrets (Token/ID) and your preferences (Categories/Length).

### Secrets Setup (Token & Chat ID)

⚠️ Important: Never commit your actual token or chat ID to GitHub!

**For Local Development (.env)**

Create a file named .env in the root directory and add your credentials. This file is ignored by Git to keep your secrets safe.

```ini
# .env
TG_BOT_TOKEN=[YOUR TOKEN]
TG_CHAT_ID=[YOUR ID]
```

**For GitHub Actions (Deployment)**

To run this automatically on GitHub, you must add these secrets to your repository settings:

1. Go to your GitHub repository.
2. Navigate to **Settings > Secrets and variables > Actions**.
3. Click **New repository secret**.
4. Add the following secrets:
- **Name**: `TG_BOT_TOKEN`
- - **Value**: Paste your Telegram Bot Token here

- **Name**: `TG_CHAT_ID`
- - **Value**: Paste your User or Group ID here

### Customization (`config.json`)
You can customize the bot's behavior by editing the `config.json` file in the root directory.

```json
{
  "categories": [
    "cs.GT",
    "cs.DS",
    "cs.DM",
    "cs.CC"
  ],
  "max_items": 0,
  "summary_length": 1000
}
```

| Field | Type | Description | Default Behavior |
| :--- | :--- | :--- | :--- |
| `categories` | `List[str]` | A list of arXiv categories to subscribe to (e.g., `cs.AI`, `math.CO`). | **Required**. Must be a non-empty list. |
| `max_items` | `int` | The maximum number of papers to push per run. | **Default**: `0` (Unlimited). <br><br>If set to `0`, the bot pushes **all** papers published today. |
| `summary_length` | `int` | The maximum number of characters for the abstract. | **Default**: `800`. <br><br>If this field is omitted, abstracts are truncated to 800 characters. |
