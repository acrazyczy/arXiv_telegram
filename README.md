# 📚 ArXiv Daily Telegram Bot

A smart, automated Python bot that fetches the latest research papers from [arXiv](https://arxiv.org/) and pushes them to your Telegram.

Powered by **GitHub Actions**, this bot runs automatically every day, ensuring you stay updated with your favorite research fields without getting spammed.

## ✨ Features

* **📅 Daily Updates**: Automatically fetches papers published "today" (filters out old or weekend duplicates).
* **🧠 Dual Notification Modes**:
    * **Detailed Mode**: Sends full abstracts for your core interest categories (e.g., `cs.GT`).
    * **Digest Mode**: Consolidates broad interest categories (e.g., `cs.AI`) into a single "Daily Digest" list (Title + Authors + Link) to keep your chat clean.
* **🎯 Keyword Radar**: automatically "upgrades" a paper from Digest mode to Detailed mode if its title or abstract matches your custom keywords (e.g., "LLM", "Diffusion").
* **⚙️ Configurable**: Easily manage categories and keywords via `config.json`.
* **🔒 Secure**: Uses GitHub Secrets to protect your Bot Token.

---

## 📂 Directory Structure

```text
.
├── .github/
│   └── workflows/
│       └── daily_arxiv.yml   # GitHub Actions configuration
├── src/
│   ├── __init__.py           # Package marker
│   └── main.py               # Main bot logic
├── config.json               # User configuration
├── .env                      # Secrets for local development (do not commit!)
├── requirements.txt
└── README.md
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
    - **Value**: Paste your Telegram Bot Token here

- **Name**: `TG_CHAT_ID`
    - **Value**: Paste your User or Group ID here

### Subscription Settings (`config.json`)
You can customize the bot's behavior by editing the `config.json` file in the root directory.

```json
{
  "detailed_categories": ["cs.GT", "cs.DS"],
  "digest_categories": ["cs.AI", "cs.LG"],
  "keywords": ["Large Language Model", "Nash Equilibrium"],
  "summary_length": 1000
}
```

#### Field Explanations

| Field | Type | Description | Behavior |
| :--- | :--- | :--- | :--- |
| `detailed_categories` | `List[str]` | High-priority categories. | Papers in these categories are **always** sent individually with full abstracts. |
| `digest_categories` | `List[str]` | Low-priority / Broad categories. | Papers here are grouped into a single **Daily Digest** message (Title/Authors only), unless they match a keyword. |
| `keywords` | `List[str]` | A list of specific terms to watch for **(case-insensitive)**. | **The Radar**: If a paper in a *Digest* category contains any of these keywords, it is promoted to **Detailed Mode** immediately. |
| `summary_length` | `int` | Max characters for abstracts. | Default: `800`. Truncates the abstract if it exceeds this length. |
