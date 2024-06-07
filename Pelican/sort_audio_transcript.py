import re
from datetime import datetime
import os

def extract_date(filename):
    match = re.search(r'\d{8}-\d{6}', filename)
    if match:
        return datetime.strptime(match.group(), '%Y%m%d-%H%M%S')
    else:
        return datetime.fromtimestamp(os.path.getctime(filename))

