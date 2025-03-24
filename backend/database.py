import sqlite3
from queue import Queue
from contextlib import contextmanager
from typing import Optional
from datetime import datetime

# 创建数据库连接池
db_pool = Queue(maxsize=5)

def init_db_pool():
    """初始化数据库连接池"""
    global db_pool
    for _ in range(5):
        conn = sqlite3.connect('data/epg.db', check_same_thread=False)
        db_pool.put(conn)

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
                    c.executescript(script)
                    c.execute(
                        "INSERT INTO db_version (version, applied_at) VALUES (?, ?)",
                        (version, datetime.now().isoformat())
                    )
                    conn.commit()
                except Exception as e:
                    print(f"Error applying upgrade script {version}: {str(e)}")
                    conn.rollback()
                    break

# 初始化数据库连接池
init_db_pool()