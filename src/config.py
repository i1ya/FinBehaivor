import os
import pathlib
from datetime import datetime

current_data = datetime.today().strftime('%Y-%m-%d')

SQLITE_DATABASE_NAME = "fin_behaivor.db"
SQLITE_DATABASE_BACKUP_NAME = 'se_backup_' + current_data + '.db'
SECRET_KEY_FILE = os.path.join(pathlib.Path(__file__).parent, "secret.conf")
SECRET_KEY = ""

with open(SECRET_KEY_FILE, 'r') as file:
    SECRET_KEY = file.read().rstrip()
