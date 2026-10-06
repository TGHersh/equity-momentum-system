import os 
from dotenv import load_dotenv
load_dotenv()


ak = os.getenv("MASSIVE_ACCESS_KEY_ID")
sk = os.getenv("MASSIVE_SECRET_ACCESS_KEY")
print(repr(ak))
print(repr(sk[:4] + "..." if sk else sk))

print(len(ak), repr(ak[-6:]))
print(len(sk), repr(sk[-6:]))