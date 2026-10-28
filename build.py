#!/usr/bin/env python3
"""Generate a country-first M3U from public iptv-org playlists."""
import urllib.request
import re
from pathlib import Path

COUNTRIES = [
 ('sy','01 | سوريا'),('lb','02 | لبنان'),('iq','03 | العراق'),
 ('ps','04 | فلسطين'),('jo','05 | الأردن'),('eg','06 | مصر'),
 ('sa','07 | السعودية'),('ae','08 | الإمارات'),('kw','09 | الكويت'),
 ('qa','10 | قطر'),('bh','11 | البحرين'),('om','12 | عُمان'),
 ('ye','13 | اليمن'),('sd','14 | السودان'),('ly','15 | ليبيا'),
 ('tn','16 | تونس'),('dz','17 | الجزائر'),('ma','18 | المغرب'),
 ('mr','19 | موريتانيا'),('so','20 | الصومال'),('dj','21 | جيبوتي'),
 ('km','22 | جزر القمر')]
BASE='https://iptv-org.github.io/iptv/countries/{}.m3u'
HEADERS={'User-Agent':'ArabicTVPlaylistBuilder/1.0'}

def fetch(url):
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=30) as response:
        return response.read().decode('utf-8-sig',errors='replace')

def parse(text):
    lines=text.splitlines(); entries=[]; pending=[]
    for line in lines:
        line=line.strip()
        if line.startswith('#EXTINF:'):
            pending=[line]
        elif pending and line.startswith('#'):
            pending.append(line)
        elif pending and line and not line.startswith('#'):
            entries.append((pending,line)); pending=[]
    return entries

def rewrite_group(extinf,group):
    extinf=re.sub(r'\s+group-title="[^"]*"','',extinf)
    # M3U attributes must follow the duration (usually -1).
    return re.sub(r'^(#EXTINF:\s*-?\d+(?:\.\d+)?)',
                  lambda match: f'{match.group(1)} group-title="{group}"',
                  extinf, count=1)

def main():
    output=['#EXTM3U']; seen=set(); count=0; failures=[]
    for code,group in COUNTRIES:
        try:
            entries=parse(fetch(BASE.format(code)))
        except Exception as exc:
            failures.append((code,str(exc))); continue
        for tags,url in entries:
            # Dedupe identical channel streams across country playlists.
            if url in seen: continue
            seen.add(url)
            output.append(rewrite_group(tags[0],group))
            output.extend(tags[1:]); output.append(url)
            count+=1
    if not count:
        raise RuntimeError("No channels were fetched; refusing to overwrite the playlist. Failures: " + str(failures))
    # Skip unavailable countries, but report them in the workflow log.
    if failures:
        print("Skipped unavailable playlists:", failures)
    Path('arabic-tv.m3u').write_text('\n'.join(output)+'\n',encoding='utf-8')
    print(f'Generated {count} entries in {len(COUNTRIES)} country groups')

if __name__=='__main__': main()
