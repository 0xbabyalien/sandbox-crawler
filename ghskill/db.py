import sqlite3
from pathlib import Path

SCHEMA = '''
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS repos (
 id INTEGER PRIMARY KEY, full_name TEXT UNIQUE, html_url TEXT, description TEXT,
 stars INTEGER, forks INTEGER, language TEXT, license TEXT, default_branch TEXT,
 updated_at TEXT, pushed_at TEXT, category TEXT, topics TEXT, status TEXT DEFAULT 'discovered',
 crawled_at TEXT, error TEXT
);
CREATE TABLE IF NOT EXISTS documents (
 id INTEGER PRIMARY KEY, repo_full_name TEXT, path TEXT, extension TEXT,
 content TEXT, sha256 TEXT, category TEXT, risk_notes TEXT,
 UNIQUE(repo_full_name,path)
);
CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(repo_full_name UNINDEXED, path UNINDEXED, category UNINDEXED, content);
'''

class Database:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def upsert_repo(self, r, category):
        lic = (r.get('license') or {}).get('spdx_id') or 'NOASSERTION'
        topics = ','.join(r.get('topics') or [])
        self.conn.execute('''INSERT INTO repos(full_name,html_url,description,stars,forks,language,license,default_branch,updated_at,pushed_at,category,topics)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(full_name) DO UPDATE SET html_url=excluded.html_url,description=excluded.description,stars=excluded.stars,forks=excluded.forks,language=excluded.language,license=excluded.license,default_branch=excluded.default_branch,updated_at=excluded.updated_at,pushed_at=excluded.pushed_at,category=excluded.category,topics=excluded.topics''',
        (r['full_name'],r['html_url'],r.get('description') or '',r.get('stargazers_count',0),r.get('forks_count',0),r.get('language') or '',lic,r.get('default_branch') or 'main',r.get('updated_at') or '',r.get('pushed_at') or '',category,topics))
        self.conn.commit()

    def save_document(self, repo, path, ext, content, sha, category, risks):
        self.conn.execute('INSERT OR REPLACE INTO documents(repo_full_name,path,extension,content,sha256,category,risk_notes) VALUES(?,?,?,?,?,?,?)',(repo,path,ext,content,sha,category,risks))
        self.conn.execute('DELETE FROM documents_fts WHERE repo_full_name=? AND path=?',(repo,path))
        self.conn.execute('INSERT INTO documents_fts(repo_full_name,path,category,content) VALUES(?,?,?,?)',(repo,path,category,content))
        self.conn.commit()

    def mark_repo(self, name, status, error=None):
        self.conn.execute('UPDATE repos SET status=?, crawled_at=CURRENT_TIMESTAMP, error=? WHERE full_name=?',(status,error,name)); self.conn.commit()

    def search(self, query, limit=10):
        return self.conn.execute('SELECT repo_full_name,path,category,snippet(documents_fts,3,"[", "]","…",18) AS excerpt FROM documents_fts WHERE documents_fts MATCH ? LIMIT ?', (query,limit)).fetchall()
