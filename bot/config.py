import os

# Core
ENV = os.getenv("ENV", "production").lower()
MODE = os.getenv("MODE", "polling").lower()  # polling | webhook
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # for webhook mode (optional)

# Admin
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")  # numeric chat_id of admin
ADMIN_IDS = os.getenv("ADMIN_IDS")  # optional: comma-separated ids

# Infra
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")

# SLH / Wallets (optional)
FOUNDER_WALLET = os.getenv("FOUNDER_WALLET")
TON_WALLET = os.getenv("TON_WALLET")
SLH_TOKEN_ADDRESS = os.getenv("SLH_TOKEN_ADDRESS")
ZUZ_TOKEN_ADDRESS = os.getenv("ZUZ_TOKEN_ADDRESS")

# AI (optional)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
