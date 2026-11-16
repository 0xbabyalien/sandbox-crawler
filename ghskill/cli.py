import argparse, json, os
from pathlib import Path
from .config import load_config
from .crawler import Crawler
from .db import Database
from .exporter import export_skills


def main():
    p=argparse.ArgumentParser(prog='ghskill',description='GitHub Skill Crawler')
    p.add_argument('--config'); p.add_argument('--data',default='data'); p.add_argument('--output',default='exports')
    sub=p.add_subparsers(dest='cmd',required=True)
    sub.add_parser('crawl',help='Discover and crawl relevant public repositories')
    sub.add_parser('export',help='Export category SKILL.md files and agent adapters')
    s=sub.add_parser('search',help='Search crawled documents'); s.add_argument('query'); s.add_argument('-n','--limit',type=int,default=10)
    sub.add_parser('stats',help='Show local index statistics')
    args=p.parse_args(); data=Path(args.data)
    if args.cmd=='crawl':
        cfg=load_config(args.config); total,ok=Crawler(cfg,data).run(); print(json.dumps({'discovered':total,'crawled':ok,'database':str(data/'knowledge.sqlite3')},indent=2))
    elif args.cmd=='export':
        db=Database(data/'knowledge.sqlite3'); count,cats=export_skills(db,args.output); print(f'Exported index of {count} documents across {cats} categories to {args.output}')
    elif args.cmd=='search':
        db=Database(data/'knowledge.sqlite3')
        for r in db.search(args.query,args.limit): print(f"\n[{r['category']}] {r['repo_full_name']} :: {r['path']}\n{r['excerpt']}")
    elif args.cmd=='stats':
        db=Database(data/'knowledge.sqlite3')
        for table in ('repos','documents'):
            print(f'{table}: {db.conn.execute("SELECT COUNT(*) FROM "+table).fetchone()[0]}')
        for r in db.conn.execute('SELECT category,COUNT(*) n FROM repos GROUP BY category'): print(f"  {r['category']}: {r['n']}")

if __name__=='__main__': main()
