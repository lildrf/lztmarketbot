import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    LOLZTEAM_TOKEN = os.getenv('LOLZTEAM_TOKEN')
    API_BASE_URL = os.getenv('API_BASE_URL', 'https://prod-api.lzt.market')

    RATE_LIMITS_PER_MIN = {
        'GET':    300,
        'POST':   30,
        'PUT':    30,
        'DELETE': 300,
    }

    REQUEST_TIMEOUT = 300

    @classmethod
    def validate(cls):
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не найден в .env файле")
        if not cls.LOLZTEAM_TOKEN:
            raise ValueError("LOLZTEAM_TOKEN не найден в .env файле")
        return True

config = Config()
