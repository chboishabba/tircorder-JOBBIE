import sqlite3
import logging
from queue import Queue, Empty
from threading import Thread, Event
from rate_limit import RateLimiter

DB_PATH = 'state.db'
MAX_RETRIES = 5
DELAY = 1  # in seconds

class DBWorker(Thread):
    def __init__(self, db_path=DB_PATH):
        super().__init__()
        self.db_path = db_path
        self.task_queue = Queue()
        self.stop_event = Event()

    def run(self):
        while not self.stop_event.is_set() or not self.task_queue.empty():
            try:
                task, args, result_queue = self.task_queue.get(timeout=0.1)
                if task == 'shutdown':
                    break
                try:
                    result = task(*args)
                    if result_queue:
                        result_queue.put(result)
                except Exception as e:
                    logging.error(f"Error executing DB task: {e}")
                    if result_queue:
                        result_queue.put(e)
            except Empty:
                continue

    def execute_with_retry(self, query, params=None):
        rate_limiter = RateLimiter(max_interval=60)
        for attempt in range(MAX_RETRIES):
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    logging.debug(f"Executing query: {query} | Params: {params}")
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                    conn.commit()
                    return cursor
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower():
                    logging.warning(f"Database is locked, retrying in {DELAY} seconds... (attempt {attempt + 1})")
                    rate_limiter.increment()
                    rate_limiter.sleep()
                else:
                    raise
        raise sqlite3.OperationalError("Max retries reached. Database is still locked.")

    def execute_query(self, query, params=None, result_queue=None):
        self.task_queue.put((self.execute_with_retry, (query, params), result_queue))

    def fetch_all(self, query, params=None, result_queue=None):
        self.task_queue.put((self._fetch_all, (query, params), result_queue))

    def _fetch_all(self, query, params=None):
        cursor = self.execute_with_retry(query, params)
        return cursor.fetchall()

    def stop(self):
        self.stop_event.set()
        self.task_queue.put(('shutdown', [], None))

# Functions that interact with DBWorker
def insert_known_file(db_worker, file_name, folder_id, extension_id, datetimes):
    query = '''
    INSERT INTO known_files (file_name, folder_id, extension_id, datetimes)
    VALUES (?, ?, ?, ?)
    '''
    result_queue = Queue()
    db_worker.execute_query(query, (file_name, folder_id, extension_id, datetimes), result_queue)
    result_queue.get()

def insert_extension(db_worker, extension):
    query = 'INSERT OR IGNORE INTO extensions (extension) VALUES (?)'
    result_queue = Queue()
    db_worker.execute_query(query, (extension,), result_queue)
    result_queue.get()

    query = 'SELECT id FROM extensions WHERE extension = ?'
    result_queue = Queue()
    db_worker.fetch_all(query, (extension,), result_queue)
    result = result_queue.get()
    return result[0][0]

def insert_transcribe_queue(db_worker, known_file_id):
    query = 'INSERT INTO transcribe_queue (known_file_id) VALUES (?)'
    result_queue = Queue()
    db_worker.execute_query(query, (known_file_id,), result_queue)
    result_queue.get()

def insert_convert_queue(db_worker, known_file_id):
    query = 'INSERT INTO convert_queue (known_file_id) VALUES (?)'
    result_queue = Queue()
    db_worker.execute_query(query, (known_file_id,), result_queue)
    result_queue.get()

def insert_skip_file(db_worker, known_file_id, reason):
    query = 'INSERT INTO skip_files (known_file_id, reason) VALUES (?, ?)'
    result_queue = Queue()
    db_worker.execute_query(query, (known_file_id, reason), result_queue)
    result_queue.get()

def clear_tables(db_worker):
    tables = ['known_files', 'transcribe_queue', 'convert_queue', 'skip_files', 'skip_reasons']
    for table in tables:
        query = f'DELETE FROM {table}'
        result_queue = Queue()
        db_worker.execute_query(query, None, result_queue)
        result_queue.get()

