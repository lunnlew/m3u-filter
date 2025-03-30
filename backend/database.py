import sqlite3
from queue import Queue
from contextlib import contextmanager
from typing import Optional
from datetime import datetime
from config import DATABASE_FILE

import logging
logger = logging.getLogger(__name__)
# 创建数据库连接池
db_pool = Queue(maxsize=5)

def init_db_pool():
    """初始化数据库连接池"""
    global db_pool
    for _ in range(5):
        conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
        db_pool.put(conn)
    
    # 初始化数据库结构
    init_db()

@contextmanager
def get_db_connection():
    """获取数据库连接的上下文管理器"""
    conn = db_pool.get()
    try:
        yield conn
    finally:
        db_pool.put(conn)

def cleanup():
    """清理数据库连接池"""
    while not db_pool.empty():
        conn = db_pool.get()
        conn.close()

def load_migration_scripts():
    """加载migrations目录下的SQL脚本"""
    import os
    import glob
    
    migrations_dir = os.path.join(os.path.dirname(__file__), 'database', 'migrations')
    if not os.path.exists(migrations_dir):
        return []
    
    migration_files = glob.glob(os.path.join(migrations_dir, '*.sql'))
    migration_files.sort()
    
    scripts = []
    for file_path in migration_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            scripts.append(f.read())
    return scripts

def init_db():
    """初始化数据库结构和版本控制"""
    with get_db_connection() as conn:
        c = conn.cursor()
        
        # 创建版本控制表
        c.execute('''
            CREATE TABLE IF NOT EXISTS db_version
            (version INTEGER PRIMARY KEY,
             applied_at TEXT NOT NULL);
        ''')
        
        # 检查当前版本
        c.execute("SELECT version FROM db_version ORDER BY version DESC LIMIT 1")
        current_version = c.fetchone()
        current_version = current_version[0] if current_version else 0
        
        # 加载migrations目录下的SQL脚本
        migration_scripts = load_migration_scripts()
        
        # 执行数据库升级
        for version, script in enumerate(migration_scripts, start=1):
            if version > current_version:
                try:
                    # Check if this version was partially applied
                    c.execute("SELECT COUNT(*) FROM db_version WHERE version = ?", (version,))
                    if c.fetchone()[0] > 0:
                        logger.warning(f"Skipping version {version} as it was already partially applied")
                        continue
                        
                    c.executescript(script)
                    c.execute(
                        "INSERT INTO db_version (version, applied_at) VALUES (?, ?)",
                        (version, datetime.now().isoformat())
                    )
                    conn.commit()
                    logger.info(f"Successfully applied database upgrade version {version}")
                except sqlite3.IntegrityError as e:
                    logger.error(f"Database integrity error in version {version}: {str(e)}")
                    conn.rollback()
                    # Continue with next migration instead of breaking
                    continue
                except Exception as e:
                    logger.error(f"Error applying upgrade script {version}: {str(e)}")
                    conn.rollback()
                    continue

# 初始化数据库连接池
init_db_pool()