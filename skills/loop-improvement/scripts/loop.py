#!/usr/bin/env python3
"""Repository-local milestone learning. No implicit model, network, or scheduler calls."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import time

SCHEMA = 1
LIMIT = 65536

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)

def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()

def safe_text(value, name, limit=4000):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(name + ' must be bounded nonempty text')
    if re.search(r'-----BEGIN .*PRIVATE KEY|\b(?:gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,})|(?:/Users/|/home/|file://)|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', value):
        raise ValueError(name + ' contains local/private material; sanitize before capture')
    return value

def identifier(value, name):
    value = safe_text(value, name, 120)
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]*', value):
        raise ValueError(name + ' must be a stable identifier')
    return value

def read_json(path):
    raw = Path(path).read_bytes()
    if len(raw) > LIMIT:
        raise ValueError('input exceeds 64 KiB')
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError('input must be an object')
    return value

def artifact(root, name):
    if not isinstance(name, str) or Path(name).is_absolute() or '..' in Path(name).parts:
        raise ValueError('artifact must be repository-relative')
    path = root / name
    if any(p.is_symlink() for p in [path, *path.parents] if p != root.parent):
        raise ValueError('symlink artifacts are not supported')
    resolved = path.resolve()
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError('artifact is outside project or missing')
    if resolved.stat().st_size > 4 * 1024 * 1024:
        raise ValueError('artifact exceeds 4 MiB')
    return resolved

def fingerprint(root, paths):
    if not isinstance(paths, list) or not paths or len(paths) > 32 or any(not isinstance(p,str) for p in paths) or len(set(paths)) != len(paths):
        raise ValueError('artifacts must name 1–32 distinct files')
    return {p: hashlib.sha256(artifact(root, p).read_bytes()).hexdigest() for p in sorted(paths)}

def connect(root, writable):
    directory = root / '.loop-improvement'
    path = directory / 'lessons.sqlite3'
    if directory.is_symlink() or path.is_symlink():
        raise ValueError('state must not be a symlink')
    if not writable and not path.exists():
        return None
    if writable:
        directory.mkdir(mode=0o700, exist_ok=True)
    con = sqlite3.connect(path if writable else path.as_uri() + '?mode=ro', uri=not writable, timeout=10)
    if writable:
        os.chmod(path, 0o600)
        con.execute('CREATE TABLE IF NOT EXISTS records (kind TEXT, id TEXT, body TEXT, PRIMARY KEY(kind,id))')
        con.commit()
    return con

def put(con, kind, value):
    key = digest(value)
    con.execute('INSERT OR IGNORE INTO records VALUES (?,?,?)', (kind, key, canonical(value)))
    con.commit()
    return key

def get(con, kind, key):
    row = con.execute('SELECT body FROM records WHERE kind=? AND id=?', (kind,key)).fetchone()
    if row is None:
        raise ValueError('record not found')
    return json.loads(row[0])

def entries(con, kind):
    if con is None:
        return []
    return [(key,json.loads(body)) for key,body in con.execute('SELECT id,body FROM records WHERE kind=? ORDER BY id', (kind,))]

def capture(con, root, data):
    allowed = {'milestone','task_key','revision','outcome','summary','artifacts'}
    if set(data) != allowed:
        raise ValueError('milestone fields must be exactly ' + ', '.join(sorted(allowed)))
    if data['outcome'] not in ['accepted','failed','blocked']:
        raise ValueError('invalid milestone outcome')
    value = {k: safe_text(data[k],k) for k in ['milestone','task_key','revision','summary']}
    value.update(outcome=data['outcome'], fingerprints=fingerprint(root,data['artifacts']))
    return {'milestone_id':put(con,'milestone',value)}

def propose(con, root, data, milestone_id):
    milestone = get(con,'milestone',milestone_id)
    # Consume only the documented sanitized SFE export fields; never raw evidence.
    if data.get('schema_version') != 1:
        raise ValueError('expected Skill Feedback Engine export schema_version 1')
    value = {'milestone_id':milestone_id,'task_key':milestone['task_key']}
    for key in ['proposal_id','skill','suggested_change','rationale']:
        value[key] = safe_text(data.get(key),key)
    return {'proposal_id':put(con,'proposal',value)}

def evaluate(con, root, data, proposal_id):
    proposal = get(con,'proposal',proposal_id)
    if set(data) != {'cases','lesson_artifacts','evaluator_revision'}:
        raise ValueError('experiment needs cases, lesson_artifacts, evaluator_revision')
    revision = safe_text(data['evaluator_revision'],'evaluator_revision')
    cases = data['cases']
    if not isinstance(cases,list) or not 2 <= len(cases) <= 20:
        raise ValueError('experiment needs 2–20 cases, including a regression guard')
    names = set()
    for case in cases:
        if not isinstance(case,dict) or set(case) != {'id','role','baseline','candidate','timeout_seconds','artifacts'}:
            raise ValueError('invalid case fields')
        name = identifier(case['id'],'case id')
        if name in names or case['role'] not in ['target','guard']:
            raise ValueError('duplicate id or invalid case role')
        names.add(name)
        timeout = case['timeout_seconds']
        if isinstance(timeout,bool) or not isinstance(timeout,(int,float)) or not math.isfinite(timeout) or not 0 < timeout <= 60:
            raise ValueError('timeout must be greater than 0 and at most 60 seconds')
        for mode in ['baseline','candidate']:
            argv = case[mode]
            if not isinstance(argv,list) or not argv or len(argv)>30 or any(not isinstance(a,str) or not a or len(a)>2000 for a in argv):
                raise ValueError('commands must be bounded argv arrays')
        fingerprint(root,case['artifacts'])
    if not any(c['role']=='target' for c in cases) or not any(c['role']=='guard' for c in cases):
        raise ValueError('target and guard cases are required')
    lesson_files = fingerprint(root,data['lesson_artifacts'])
    result = []
    for case in cases:
        before = fingerprint(root,case['artifacts'])
        codes = {}
        for mode in ['baseline','candidate']:
            # Explicit local commands, no shell expansion; output is not persisted.
            try:
                run = subprocess.run(case[mode],cwd=root,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                                     timeout=case['timeout_seconds'],check=False)
                codes[mode] = run.returncode
            except (subprocess.TimeoutExpired,OSError):
                codes[mode] = None
        if before != fingerprint(root,case['artifacts']):
            raise ValueError('case artifacts changed during comparison')
        result.append({'id':case['id'],'role':case['role'],'codes':codes,'fingerprints':before})
    if lesson_files != fingerprint(root,data['lesson_artifacts']):
        raise ValueError('lesson artifacts changed during comparison')
    passed = all(r['codes']['candidate']==0 for r in result)
    passed = passed and all(r['codes']['baseline']==0 for r in result if r['role']=='guard')
    passed = passed and any(r['codes']['baseline'] not in (0,None) and r['codes']['candidate']==0 for r in result if r['role']=='target')
    value = {'proposal_id':proposal_id,'task_key':proposal['task_key'],'evaluator_revision':revision,
             'contract_digest':digest(data),'cases':result,'lesson_fingerprints':lesson_files,'passed':passed}
    return {'experiment_id':put(con,'experiment',value),'passed':passed}

def accept(con, root, data, experiment_id):
    experiment = get(con,'experiment',experiment_id)
    if not experiment['passed']:
        raise ValueError('failed experiment cannot be accepted')
    if set(data) != {'reviewer','rationale','expires_at'}:
        raise ValueError('decision needs reviewer, rationale, expires_at')
    expiry = data['expires_at']
    if isinstance(expiry,bool) or not isinstance(expiry,(int,float)) or not math.isfinite(expiry) or expiry <= time.time():
        raise ValueError('expiry must be a future Unix timestamp')
    for case in experiment['cases']:
        if fingerprint(root,list(case['fingerprints'])) != case['fingerprints']:
            raise ValueError('experiment evidence changed; reevaluate before accepting')
    if fingerprint(root,list(experiment['lesson_fingerprints'])) != experiment['lesson_fingerprints']:
        raise ValueError('lesson artifacts changed; reevaluate before accepting')
    # Serialize the decision lookup and insert across competing writers.
    con.execute('BEGIN IMMEDIATE')
    if any(e['experiment_id']==experiment_id for _,e in entries(con,'lesson')):
        existing = next(k for k,e in entries(con,'lesson') if e['experiment_id']==experiment_id)
        con.commit()
        return {'lesson_id':existing,'already_recorded':True}
    value={'experiment_id':experiment_id,'reviewer':safe_text(data['reviewer'],'reviewer'),
           'rationale':safe_text(data['rationale'],'rationale'),'expires_at':expiry}
    return {'lesson_id':put(con,'lesson',value)}

def retrieve(con, root, task_key):
    retired={e['lesson_id'] for _,e in entries(con,'retirement')}
    lessons=[]
    for key,lesson in entries(con,'lesson'):
        if key in retired or lesson['expires_at']<=time.time():
            continue
        experiment=get(con,'experiment',lesson['experiment_id'])
        if experiment['task_key']!=task_key:
            continue
        try:
            if fingerprint(root,list(experiment['lesson_fingerprints']))!=experiment['lesson_fingerprints']:
                continue
        except (ValueError,OSError):
            continue
        proposal=get(con,'proposal',experiment['proposal_id'])
        lessons.append({'lesson_id':key,'skill':proposal['skill'],'suggested_change':proposal['suggested_change'],
                        'experiment_id':lesson['experiment_id'],'expires_at':lesson['expires_at'],
                        'evidence_class':'local_command_comparison','authority':'advisory_only'})
    return {'lessons':lessons,'count':len(lessons)}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root',required=True)
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('status')
    for command,ref in [('capture',None),('propose','milestone'),('evaluate','proposal'),('accept','experiment')]:
        p=sub.add_parser(command);p.add_argument('--input',required=True)
        if ref:p.add_argument('--'+ref,required=True)
    p=sub.add_parser('retrieve');p.add_argument('--task-key',required=True)
    p=sub.add_parser('retire');p.add_argument('--lesson',required=True);p.add_argument('--reason',required=True)
    args=parser.parse_args()
    root=Path(args.project_root).resolve(strict=True)
    if not root.is_dir():raise ValueError('project root must be a directory')
    readonly=args.command in ['status','retrieve']
    con=connect(root,not readonly)
    try:
        if args.command=='status':
            out={'schema_version':SCHEMA,'counts':{k:len(entries(con,k)) for k in ['milestone','proposal','experiment','lesson','retirement']},'monitoring':False}
        elif args.command=='retrieve':out=retrieve(con,root,args.task_key)
        elif args.command=='retire':
            get(con,'lesson',args.lesson)
            out={'retirement_id':put(con,'retirement',{'lesson_id':args.lesson,'reason':safe_text(args.reason,'reason')})}
        else:
            data=read_json(args.input)
            functions={'capture':capture,'propose':propose,'evaluate':evaluate,'accept':accept}
            ref={'propose':'milestone','evaluate':'proposal','accept':'experiment'}.get(args.command)
            out=functions[args.command](con,root,data,*([getattr(args,ref)] if ref else []))
        print(json.dumps(out,sort_keys=True,allow_nan=False))
    finally:
        if con:con.close()

if __name__=='__main__':
    try:main()
    except (ValueError,TypeError,KeyError,OSError,sqlite3.Error) as exc:
        print(json.dumps({'error':str(exc)}),file=sys.stderr);sys.exit(1)
