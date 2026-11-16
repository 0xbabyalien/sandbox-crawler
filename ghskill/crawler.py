import os, tarfile, tempfile, time
from pathlib import Path
from .github import GitHubClient
from .analyze import classify, inspect_text, digest, safe_path
from .db import Database


def repo_category(repo, cfg):
    text=' '.join([repo.get('name',''),repo.get('description') or '', ' '.join(repo.get('topics') or [])])
    return classify(text,cfg)

class Crawler:
    def __init__(self, cfg, data_dir):
        self.cfg=cfg; self.data=Path(data_dir); self.data.mkdir(parents=True,exist_ok=True)
        self.db=Database(self.data/'knowledge.sqlite3'); self.gh=GitHubClient(cfg.get('request_timeout',30))

    def discover(self):
        found={}
        for q in self.cfg['search_queries']:
            for page in range(1,int(self.cfg['max_pages_per_query'])+1):
                items,total,_=self.gh.search_repositories(q,page,int(self.cfg['per_page']))
                for r in items:
                    if r.get('fork') or r.get('archived') or r.get('disabled'): continue
                    found[r['full_name']]=r
                if page*int(self.cfg['per_page']) >= min(total,1000): break
                time.sleep(0.25)
        items=list(found.values())[:int(self.cfg['max_repos_per_run'])]
        for r in items: self.db.upsert_repo(r,repo_category(r,self.cfg))
        return items

    def crawl_repo(self, repo):
        name=repo['full_name']; branch=repo.get('default_branch') or 'main'
        try:
            with tempfile.TemporaryDirectory(prefix='ghskill-') as td:
                archive=Path(td)/'repo.tgz'
                size=self.gh.download_tarball(name,branch,archive)
                if size > int(self.cfg['max_repo_mb'])*1024*1024: raise RuntimeError('Repository archive exceeds configured size limit')
                with tarfile.open(archive,'r:gz') as tf:
                    members=[]
                    for m in tf.getmembers():
                        if not m.isfile() or not safe_path(m.name): continue
                        parts=Path(m.name).parts
                        if any(p in self.cfg['excluded_dirs'] for p in parts): continue
                        rel='/'.join(parts[1:])
                        if not rel: continue
                        ext=Path(rel).suffix.lower()
                        if ext not in self.cfg['allowed_extensions'] and Path(rel).name not in self.cfg['important_names']: continue
                        if m.size > int(self.cfg['max_file_bytes']): continue
                        members.append((m,rel,ext))
                    members=members[:int(self.cfg['max_files_per_repo'])]
                    for m,rel,ext in members:
                        f=tf.extractfile(m)
                        if not f: continue
                        raw=f.read(int(self.cfg['max_file_bytes'])+1)
                        if len(raw)>int(self.cfg['max_file_bytes']): continue
                        try: content=raw.decode('utf-8')
                        except UnicodeDecodeError: continue
                        cat=classify(rel+'\n'+content[:30000],self.cfg)
                        self.db.save_document(name,rel,ext,content,digest(raw),cat,inspect_text(content))
            self.db.mark_repo(name,'crawled')
            return True
        except Exception as e:
            self.db.mark_repo(name,'error',str(e)[:1000]); return False

    def run(self):
        repos=self.discover(); ok=0
        for i,r in enumerate(repos,1):
            if self.crawl_repo(r): ok+=1
            print(f'[{i}/{len(repos)}] {r["full_name"]}: {"ok" if self.db.conn.execute("SELECT status FROM repos WHERE full_name=?",(r["full_name"],)).fetchone()[0]=="crawled" else "error"}')
            time.sleep(0.15)
        return len(repos),ok
