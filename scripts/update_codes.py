"""Collect publicly published voucher codes; never touches personal usage state."""
import argparse
import copy
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ['https://www.taptap.cn/app/732885/topic?type=official',
           'https://www.taptap.cn/app/732885/topic?page=2&type=official']
CODE = re.compile(r'^[A-Za-z0-9]{5,24}$')

class Articles(HTMLParser):
    def __init__(self):
        super().__init__()
        self.current = None
        self.rows = {}
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('script', 'style'):
            self.skip += 1
        if tag == 'a':
            match = re.match(r'(?:https://www\.taptap\.cn)?/moment/(\d+)', attrs.get('href', ''))
            self.current = [match.group(1), []] if match else None
        if self.current and tag in ('p', 'br', 'div'):
            self.current[1].append('\n')

    def handle_data(self, data):
        if self.current and not self.skip:
            self.current[1].append(data)

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip = max(0, self.skip - 1)
        if tag == 'a' and self.current:
            key, chunks = self.current
            text = ''.join(chunks).strip()
            if len(text) > len(self.rows.get(key, '')):
                self.rows[key] = text
            self.current = None
        elif self.current and tag in ('p', 'div'):
            self.current[1].append('\n')

def expiry(text):
    if re.search(r'(?:兑换码|礼包码|福利码)[^\n]*长期有效', text):
        return None
    boundary = r'(?:^|[\n。；;，,]|(?:兑换码|礼包码|福利码)\s*[：:]?\s*[A-Za-z0-9]{5,24})'
    matches = re.findall(boundary + r'\s*(?:有效时间|兑换时间|兑换截止时间|有效期|兑换期限)\s*[：:]?\s*(20\d{2})年\s*(\d{1,2})月\s*(\d{1,2})日\s*(\d{1,2})(?::(\d{2})|点)\s*(?:过期|截止|失效)', text)
    if len(set(matches)) != 1:
        return None
    y, m, d, hour, minute = matches[0]
    try:
        return datetime(int(y), int(m), int(d), int(hour), int(minute or 0), tzinfo=timezone(timedelta(hours=8))).isoformat()
    except ValueError:
        return None

def parse_page(html):
    parser = Articles()
    parser.feed(html)
    if '保卫向日葵' not in html or not any(len(t) > 30 for t in parser.rows.values()):
        raise ValueError('公告页无法识别，未更新成功时间')
    result = []
    for post, text in parser.rows.items():
        if not re.search(r'兑换码|礼包码|福利码', text):
            continue
        codes, awaiting, in_list = [], 0, False
        for line in text.splitlines():
            candidate = line.strip()
            if not candidate:
                continue
            explicit = re.findall(r'(?:兑换码|礼包码|福利码)\s*[：:]?\s*([A-Za-z0-9]{5,24})(?![A-Za-z0-9])', candidate)
            if explicit:
                codes.extend(explicit)
                awaiting = 0
                in_list = bool(re.fullmatch(r'(?:兑换码|礼包码|福利码)\s*[：:]?\s*[A-Za-z0-9]{5,24}', candidate))
            elif re.search(r'客服|微信|QQ|活动编号|评论|回复|抽奖|之后公布|敬请期待|时间|有效期|使用提示|兑换方式', candidate):
                awaiting, in_list = 0, False
            elif re.search(r'兑换码|礼包码|福利码', candidate):
                awaiting, in_list = 2, False
            elif (awaiting or in_list) and CODE.fullmatch(candidate) and re.search('[A-Za-z]', candidate) and re.search('[0-9]', candidate):
                codes.append(candidate)
                awaiting, in_list = 0, True
            else:
                awaiting = max(0, awaiting - 1)
                in_list = False
        for code in dict.fromkeys(codes):
            if not re.search('[A-Za-z]', code):
                continue
            result.append({'code': code, 'sourceType': 'official',
                           'sourceLabel': 'TapTap 官方公告',
                           'sourceUrl': f'https://www.taptap.cn/moment/{post}',
                           'expiresAt': expiry(text) if len(set(codes)) == 1 else None,
                           'channel': '微信渠道待验证'})
    return result

def merge_catalog(existing, incoming, now):
    result = copy.deepcopy(existing)
    rows = {r['code']: dict(r) for r in result.get('codes', [])}
    for item in incoming:
        code = item['code']
        old = rows.get(code, {})
        updated = {**old, **{k: v for k, v in item.items() if v is not None and k != 'used'}}
        updated['firstSeen'] = old.get('firstSeen', now)
        updated.setdefault('expiresAt', None)
        updated.pop('used', None)
        rows[code] = updated
    result.update(schemaVersion=1, codes=list(rows.values()), lastAttemptAt=now,
                  lastSuccessfulCheck=now, checkStatus='success', errors=[], sources=SOURCES)
    return result

def record_failure(existing, now, errors):
    return {**copy.deepcopy(existing), 'lastAttemptAt': now, 'checkStatus': 'failed', 'errors': errors}

def save_atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as file:
            json.dump(value, file, ensure_ascii=False, indent=2)
            file.write('\n')
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, default=ROOT / 'dist/data/codes.json')
    args = parser.parse_args()
    old = json.loads(args.catalog.read_text(encoding='utf-8'))
    incoming, errors = [], []
    for url in SOURCES:
        try:
            request = Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; SunflowerCodeHelper/1.0)'})
            with urlopen(request, timeout=25) as response:
                html = response.read(3_000_001)
                if len(html) > 3_000_000:
                    raise ValueError('公告内容超过读取上限')
            incoming.extend(parse_page(html.decode('utf-8')))
        except Exception as error:
            errors.append(f'{url}: {type(error).__name__}: {error}')
    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    if errors:
        result = record_failure(old, now, errors)
    else:
        result = merge_catalog(old, incoming, now)
    save_atomic(args.catalog, result)
    print(json.dumps({'status': result['checkStatus'], 'total': len(result['codes']),
                      'added': len(result['codes']) - len(old['codes']),
                      'lastSuccessfulCheck': result.get('lastSuccessfulCheck'), 'errors': errors}, ensure_ascii=True))
    return 1 if errors else 0

if __name__ == '__main__':
    sys.exit(main())
