#!/usr/bin/env python3
"""Netflix subtitle processor - validate and fix SRT files to Netflix specs."""

import re
import sys
from pathlib import Path

# Netflix Timed Text Style Guide specs
LANG_CONFIG = {
    'en': {'max_chars': 42, 'max_cps': 17, 'max_cps_kids': 15, 'name': 'English'},
    'zh': {'max_chars': 16, 'max_cps': 9, 'max_cps_kids': 7, 'name': 'Chinese'},
}
TIMING = {'min_ms': 833, 'max_ms': 7000, 'gap_ms': 83}

def time_to_ms(ts):
    h, m, rest = ts.split(':')
    s, ms = rest.split(',')
    return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)

def ms_to_time(ms):
    h = ms // 3600000
    m = (ms % 3600000) // 60000
    s = (ms % 60000) // 1000
    ms_part = ms % 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms_part:03d}"

def parse_srt(path):
    content = Path(path).read_text(encoding='utf-8')
    entries = []
    for block in re.split(r'\n\n+', content.strip()):
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        m = re.match(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', lines[1])
        if not m:
            continue
        entries.append({'index': int(lines[0]), 'start': m.group(1), 'end': m.group(2),
                        'text': '\n'.join(lines[2:])})
    return entries

def write_srt(entries, path):
    lines = []
    for i, e in enumerate(entries, 1):
        lines.extend([str(i), f"{e['start']} --> {e['end']}", e['text'], ''])
    Path(path).write_text('\n'.join(lines), encoding='utf-8')

def count_chars(text, lang):
    text = re.sub(r'<[^>]+>', '', text).replace('\n', ' ').strip()
    if lang == 'zh':
        return sum(2 if ord(c) > 127 else 1 for c in text)
    return len(text)

def calc_cps(text, duration_ms):
    if duration_ms <= 0:
        return float('inf')
    return count_chars(text, 'en') / (duration_ms / 1000)

def validate_entry(e, lang, cfg):
    issues = []
    start_ms, end_ms = time_to_ms(e['start']), time_to_ms(e['end'])
    duration = end_ms - start_ms

    if duration < TIMING['min_ms']:
        issues.append(f"Duration {duration}ms < {TIMING['min_ms']}ms minimum")
    if duration > TIMING['max_ms']:
        issues.append(f"Duration {duration}ms > {TIMING['max_ms']}ms maximum")

    cps = calc_cps(e['text'], duration)
    if cps > cfg['max_cps']:
        issues.append(f"CPS {cps:.1f} > {cfg['max_cps']} maximum")

    for line in e['text'].split('\n'):
        chars = count_chars(line, lang)
        if chars > cfg['max_chars']:
            issues.append(f"Line '{line[:20]}...' has {chars} chars > {cfg['max_chars']} max")

    if e['text'].count('\n') >= 2:
        issues.append(f"Has {e['text'].count(chr(10)) + 1} lines, max is 2")

    return issues

def validate(entries, lang):
    cfg = LANG_CONFIG.get(lang, LANG_CONFIG['en'])
    all_issues = []

    for i, e in enumerate(entries):
        issues = validate_entry(e, lang, cfg)
        if issues:
            all_issues.append((e['index'], e['start'], e['end'], issues))

    # Check gaps
    for i in range(1, len(entries)):
        prev_end = time_to_ms(entries[i-1]['end'])
        curr_start = time_to_ms(entries[i]['start'])
        gap = curr_start - prev_end
        if 0 < gap < TIMING['gap_ms']:
            all_issues.append((entries[i]['index'], entries[i]['start'], entries[i]['end'],
                              [f"Gap {gap}ms < {TIMING['gap_ms']}ms minimum"]))

    return all_issues

def fix_line_breaks(text, lang, max_chars):
    lines = text.split('\n')
    result = []
    for line in lines:
        if count_chars(line, lang) <= max_chars:
            result.append(line)
            continue
        # Split at punctuation or midpoint
        words = line.split() if lang == 'en' else list(line)
        mid = len(words) // 2
        if lang == 'en':
            result.extend([' '.join(words[:mid]), ' '.join(words[mid:])])
        else:
            result.extend([''.join(words[:mid]), ''.join(words[mid:])])
    return '\n'.join(result[:2])  # Max 2 lines

def fix_timing(e, min_ms=TIMING['min_ms']):
    start_ms, end_ms = time_to_ms(e['start']), time_to_ms(e['end'])
    duration = end_ms - start_ms
    if duration < min_ms:
        e['end'] = ms_to_time(start_ms + min_ms)
    return e

def fix_gaps(entries):
    for i in range(1, len(entries)):
        prev_end = time_to_ms(entries[i-1]['end'])
        curr_start = time_to_ms(entries[i]['start'])
        gap = curr_start - prev_end
        if 0 < gap < TIMING['gap_ms']:
            entries[i-1]['end'] = ms_to_time(prev_end - (TIMING['gap_ms'] - gap))
    return entries

def fix_entries(entries, lang):
    cfg = LANG_CONFIG.get(lang, LANG_CONFIG['en'])
    fixed = []
    for e in entries:
        e = fix_timing(e.copy())
        e['text'] = fix_line_breaks(e['text'], lang, cfg['max_chars'])
        fixed.append(e)
    return fix_gaps(fixed)

def print_report(path, lang, issues):
    cfg = LANG_CONFIG.get(lang, LANG_CONFIG['en'])
    entries = parse_srt(path)

    print(f"\n{'='*50}")
    print(f"Netflix Subtitle Validation Report")
    print(f"{'='*50}")
    print(f"File: {path}")
    print(f"Language: {cfg['name']} ({cfg['max_cps']} CPS max, {cfg['max_chars']} chars/line)")
    print(f"\nSummary:")
    print(f"  Total entries: {len(entries)}")
    print(f"  Issues found: {len(issues)}")

    if issues:
        # Categorize issues
        cats = {'Duration': 0, 'CPS': 0, 'Line': 0, 'Gap': 0, 'lines': 0}
        for _, _, _, errs in issues:
            for err in errs:
                if 'Duration' in err: cats['Duration'] += 1
                elif 'CPS' in err: cats['CPS'] += 1
                elif 'chars' in err: cats['Line'] += 1
                elif 'Gap' in err: cats['Gap'] += 1
                elif 'lines' in err: cats['lines'] += 1

        print(f"\nIssue breakdown:")
        if cats['Duration']: print(f"  Duration problems: {cats['Duration']}")
        if cats['CPS']: print(f"  Reading speed (CPS): {cats['CPS']}")
        if cats['Line']: print(f"  Line too long: {cats['Line']}")
        if cats['Gap']: print(f"  Gap too short: {cats['Gap']}")
        if cats['lines']: print(f"  Too many lines: {cats['lines']}")

        print(f"\nDetails (first 10):")
        for idx, start, end, errs in issues[:10]:
            print(f"  #{idx} [{start} --> {end}]")
            for err in errs:
                print(f"    - {err}")
    else:
        print("\n✓ All entries pass Netflix specifications!")

    print(f"{'='*50}\n")

def main():
    if len(sys.argv) < 3:
        print("Netflix Subtitle Processor")
        print("\nUsage:")
        print("  netflix_subs.py validate <input.srt> --lang <en|zh>")
        print("  netflix_subs.py fix <input.srt> <output.srt> --lang <en|zh>")
        print("  netflix_subs.py report <input.srt> --lang <en|zh>")
        print("\nNetflix specs:")
        print("  English: 42 chars/line, 17 CPS, 833ms-7s duration, 83ms gap")
        print("  Chinese: 16 chars/line, 9 CPS, 833ms-7s duration, 83ms gap")
        sys.exit(1)

    cmd = sys.argv[1]
    lang = 'en'
    for i, arg in enumerate(sys.argv):
        if arg == '--lang' and i + 1 < len(sys.argv):
            lang = sys.argv[i + 1]

    if cmd == 'validate':
        entries = parse_srt(sys.argv[2])
        issues = validate(entries, lang)
        if issues:
            print(f"Found {len(issues)} entries with issues")
            for idx, start, end, errs in issues[:5]:
                print(f"  #{idx}: {', '.join(errs)}")
            sys.exit(1)
        else:
            print(f"✓ All {len(entries)} entries pass Netflix specs")

    elif cmd == 'fix':
        if len(sys.argv) < 4:
            print("Usage: netflix_subs.py fix <input.srt> <output.srt> --lang <en|zh>")
            sys.exit(1)
        entries = parse_srt(sys.argv[2])
        fixed = fix_entries(entries, lang)
        out_path = sys.argv[3]
        write_srt(fixed, out_path)

        # Validate fixed output
        new_issues = validate(fixed, lang)
        print(f"Fixed {len(entries)} entries -> {out_path}")
        if new_issues:
            print(f"  Note: {len(new_issues)} issues remain (may need manual review)")
        else:
            print(f"  ✓ Output passes all Netflix specs")

    elif cmd == 'report':
        entries = parse_srt(sys.argv[2])
        issues = validate(entries, lang)
        print_report(sys.argv[2], lang, issues)

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

if __name__ == '__main__':
    main()
