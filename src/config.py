import os
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_COUNT = int(os.getenv("ACCOUNT_COUNT", 10))
CONTACTS_PER_ACCOUNT = int(os.getenv("CONTACTS_PER_ACCOUNT", 3))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")