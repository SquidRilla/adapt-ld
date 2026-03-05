import os
from datetime import timedelta

SECRET_KEY = os.environ.get("ADAPT_LD_SECRET_KEY", "change-this-secret-for-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

def get_access_token_expires():
    return timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
