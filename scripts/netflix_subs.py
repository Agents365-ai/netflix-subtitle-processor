#!/usr/bin/env python3
"""Netflix subtitle processor - validate and fix SRT files to Netflix specs."""

import re
import sys
import json
from pathlib import Path

VERSION = "1.1.0"

# Netflix Timed Text Style Guide specs
LANG_CONFIG = {
    'en': {'max_chars': 42, 'max_cps': 17, 'max_cps_kids': 15, 'name': 'English'},
    'zh': {'max_chars': 16, 'max_cps': 9, 'max_cps_kids': 7, 'name': 'Chinese'},
    'ja': {'max_chars': 13, 'max_cps': 4, 'max_cps_kids': 4, 'name': 'Japanese'},
    'ko': {'max_chars': 16, 'max_cps': 12, 'max_cps_kids': 10, 'name': 'Korean'},
    'es': {'max_chars': 42, 'max_cps': 17, 'max_cps_kids': 15, 'name': 'Spanish'},
}
TIMING = {'min_ms': 833, 'max_ms': 7000, 'gap_ms': 83}
CJK_PUNCTUATION = '，。！？、；：""''）》】…'

def time_to_ms(ts):
    h, m, rest = ts.split(':')
    s, ms = rest.split(',')
    return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)

def ms_to_time(ms):
    if ms < 0:
        ms = 0
    h = ms // 3600000
    m = (ms % 3600000) // 60000
    s = (ms % 60000) // 1000
    ms_part = ms % 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms_part:03d}"

def parse_srt(path):
    if path == '-':
        content = sys.stdin.read()
    else:
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
    output = '\n'.join(lines)
    if path == '-':
        print(output)
    else:
        Path(path).write_text(output, encoding='utf-8')

def is_cjk(lang):
    return lang in ('zh', 'ja', 'ko')

def count_chars(text, lang):
    text = re.sub(r'<[^>]+>', '', text).replace('\n', ' ').strip()
    if is_cjk(lang):
        return sum(2 if ord(c) > 127 else 1 for c in text)
    return len(text)

def calc_cps(text, duration_ms, lang):
    if duration_ms <= 0:
        return float('inf')
    return count_chars(text, lang) / (duration_ms / 1000)

def detect_language(entries):
    """Auto-detect language based on content."""
    if not entries:
        return 'en'
    sample = ' '.join(e['text'] for e in entries[:10])
    cjk_count = sum(1 for c in sample if ord(c) > 0x4E00)
    if cjk_count > len(sample) * 0.3:
        # Detect specific CJK language
        if any(c in sample for c in 'のはがでを'):
            return 'ja'
        if any(c in sample for c in '는이가을를'):
            return 'ko'
        return 'zh'
    if any(c in sample for c in 'áéíóúñ¿¡'):
        return 'es'
    return 'en'

def validate_entry(e, lang, cfg, kids=False):
    issues = []
    start_ms, end_ms = time_to_ms(e['start']), time_to_ms(e['end'])
    duration = end_ms - start_ms

    if duration < TIMING['min_ms']:
        issues.append(f"Duration {duration}ms < {TIMING['min_ms']}ms minimum")
    if duration > TIMING['max_ms']:
        issues.append(f"Duration {duration}ms > {TIMING['max_ms']}ms maximum")

    max_cps = cfg['max_cps_kids'] if kids else cfg['max_cps']
    cps = calc_cps(e['text'], duration, lang)
    if cps > max_cps:
        issues.append(f"CPS {cps:.1f} > {max_cps} maximum")

    for line in e['text'].split('\n'):
        chars = count_chars(line, lang)
        if chars > cfg['max_chars']:
            issues.append(f"Line '{line[:20]}...' has {chars} chars > {cfg['max_chars']} max")

    if e['text'].count('\n') >= 2:
        issues.append(f"Has {e['text'].count(chr(10)) + 1} lines, max is 2")

    return issues

def validate(entries, lang, kids=False):
    cfg = LANG_CONFIG.get(lang, LANG_CONFIG['en'])
    all_issues = []

    for i, e in enumerate(entries):
        issues = validate_entry(e, lang, cfg, kids)
        if issues:
            all_issues.append((e['index'], e['start'], e['end'], issues))

    # Check gaps and overlaps
    for i in range(1, len(entries)):
        prev_end = time_to_ms(entries[i-1]['end'])
        curr_start = time_to_ms(entries[i]['start'])
        gap = curr_start - prev_end

        if gap < 0:
            all_issues.append((entries[i]['index'], entries[i]['start'], entries[i]['end'],
                              [f"Overlaps with previous by {-gap}ms"]))
        elif 0 < gap < TIMING['gap_ms']:
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

        if is_cjk(lang):
            # Try to break at CJK punctuation first
            best_break = -1
            for i, c in enumerate(line):
                if c in CJK_PUNCTUATION and i > 0:
                    left = count_chars(line[:i+1], lang)
                    if left <= max_chars:
                        best_break = i + 1
            if best_break > 0:
                result.extend([line[:best_break], line[best_break:].strip()])
            else:
                # Fall back to midpoint
                mid = len(line) // 2
                result.extend([line[:mid], line[mid:]])
        else:
            # English: split by words
            words = line.split()
            mid = len(words) // 2
            result.extend([' '.join(words[:mid]), ' '.join(words[mid:])])

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

        if gap < 0:
            # Overlap: shorten previous subtitle to end before current starts
            new_end = curr_start - TIMING['gap_ms']
            prev_start = time_to_ms(entries[i-1]['start'])
            if new_end > prev_start + TIMING['min_ms']:
                entries[i-1]['end'] = ms_to_time(new_end)
        elif 0 < gap < TIMING['gap_ms']:
            # Gap too short: shorten previous subtitle slightly
            needed = TIMING['gap_ms'] - gap
            new_end = prev_end - needed
            prev_start = time_to_ms(entries[i-1]['start'])
            if new_end > prev_start + TIMING['min_ms']:
                entries[i-1]['end'] = ms_to_time(new_end)

    return entries

def fix_entries(entries, lang):
    cfg = LANG_CONFIG.get(lang, LANG_CONFIG['en'])
    fixed = []
    for e in entries:
        e = fix_timing(e.copy())
        e['text'] = fix_line_breaks(e['text'], lang, cfg['max_chars'])
        fixed.append(e)
    return fix_gaps(fixed)

def clean_entries(entries, lang, kids=False):
    """Remove entries that have unfixable issues."""
    cfg = LANG_CONFIG.get(lang, LANG_CONFIG['en'])
    cleaned = []
    removed = []
    for e in entries:
        e_copy = fix_timing(e.copy())
        e_copy['text'] = fix_line_breaks(e_copy['text'], lang, cfg['max_chars'])
        issues = validate_entry(e_copy, lang, cfg, kids)
        if not issues:
            cleaned.append(e_copy)
        else:
            removed.append((e['index'], issues))
    return fix_gaps(cleaned), removed

def print_report(path, lang, issues, kids=False):
    cfg = LANG_CONFIG.get(lang, LANG_CONFIG['en'])
    entries = parse_srt(path)
    max_cps = cfg['max_cps_kids'] if kids else cfg['max_cps']

    print(f"\n{'='*50}")
    print(f"Netflix Subtitle Validation Report")
    print(f"{'='*50}")
    print(f"File: {path}")
    print(f"Language: {cfg['name']} ({max_cps} CPS max, {cfg['max_chars']} chars/line)")
    if kids:
        print(f"Mode: Children's content")
    print(f"\nSummary:")
    print(f"  Total entries: {len(entries)}")
    print(f"  Issues found: {len(issues)}")

    if issues:
        cats = {'Duration': 0, 'CPS': 0, 'Line': 0, 'Gap': 0, 'lines': 0, 'Overlap': 0}
        for _, _, _, errs in issues:
            for err in errs:
                if 'Duration' in err: cats['Duration'] += 1
                elif 'CPS' in err: cats['CPS'] += 1
                elif 'chars' in err: cats['Line'] += 1
                elif 'Gap' in err: cats['Gap'] += 1
                elif 'Overlap' in err: cats['Overlap'] += 1
                elif 'lines' in err: cats['lines'] += 1

        print(f"\nIssue breakdown:")
        if cats['Duration']: print(f"  Duration problems: {cats['Duration']}")
        if cats['CPS']: print(f"  Reading speed (CPS): {cats['CPS']}")
        if cats['Line']: print(f"  Line too long: {cats['Line']}")
        if cats['Gap']: print(f"  Gap too short: {cats['Gap']}")
        if cats['Overlap']: print(f"  Overlapping: {cats['Overlap']}")
        if cats['lines']: print(f"  Too many lines: {cats['lines']}")

        print(f"\nDetails (first 10):")
        for idx, start, end, errs in issues[:10]:
            print(f"  #{idx} [{start} --> {end}]")
            for err in errs:
                print(f"    - {err}")
    else:
        print("\n✓ All entries pass Netflix specifications!")

    print(f"{'='*50}\n")

def output_json(data, path=None):
    output = json.dumps(data, ensure_ascii=False, indent=2)
    if path and path != '-':
        Path(path).write_text(output, encoding='utf-8')
    else:
        print(output)

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(f"Netflix Subtitle Processor v{VERSION}")
        print("\nUsage:")
        print("  netflix_subs.py validate <input.srt> [--lang <code>] [--kids] [--json]")
        print("  netflix_subs.py fix <input.srt> <output.srt> [--lang <code>]")
        print("  netflix_subs.py clean <input.srt> <output.srt> [--lang <code>] [--kids]")
        print("  netflix_subs.py report <input.srt> [--lang <code>] [--kids]")
        print("\nCommands:")
        print("  validate  Check compliance, exit 1 if issues found")
        print("  fix       Repair timing/lines, keep all entries")
        print("  clean     Remove unfixable entries, output only valid ones")
        print("  report    Detailed validation report")
        print("\nOptions:")
        print("  --lang    Language code: en, zh, ja, ko, es (auto-detect if omitted)")
        print("  --kids    Use children's content limits (lower CPS)")
        print("  --json    Output results as JSON")
        print("  -         Use stdin/stdout instead of file")
        print("\nNetflix specs:")
        for code, cfg in LANG_CONFIG.items():
            print(f"  {code}: {cfg['max_chars']} chars, {cfg['max_cps']}/{cfg['max_cps_kids']} CPS (adult/kids)")
        sys.exit(0)

    if sys.argv[1] in ('-v', '--version'):
        print(f"netflix_subs.py v{VERSION}")
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    # Parse flags
    lang = None
    kids = '--kids' in args
    json_out = '--json' in args
    args = [a for a in args if a not in ('--kids', '--json')]

    for i, arg in enumerate(args):
        if arg == '--lang' and i + 1 < len(args):
            lang = args[i + 1]
            args = args[:i] + args[i+2:]
            break

    if cmd == 'validate':
        if not args:
            print("Usage: netflix_subs.py validate <input.srt> [--lang <code>] [--kids] [--json]")
            sys.exit(1)
        entries = parse_srt(args[0])
        if lang is None:
            lang = detect_language(entries)
        issues = validate(entries, lang, kids)

        if json_out:
            output_json({
                'file': args[0],
                'language': lang,
                'kids_mode': kids,
                'total_entries': len(entries),
                'issues': [{'index': idx, 'start': s, 'end': e, 'errors': errs}
                           for idx, s, e, errs in issues]
            })
        else:
            if issues:
                print(f"Found {len(issues)} entries with issues")
                for idx, start, end, errs in issues[:5]:
                    print(f"  #{idx}: {', '.join(errs)}")
                sys.exit(1)
            else:
                print(f"✓ All {len(entries)} entries pass Netflix specs ({lang})")

    elif cmd == 'fix':
        if len(args) < 2:
            print("Usage: netflix_subs.py fix <input.srt> <output.srt> [--lang <code>]")
            sys.exit(1)
        entries = parse_srt(args[0])
        if lang is None:
            lang = detect_language(entries)
        fixed = fix_entries(entries, lang)
        write_srt(fixed, args[1])

        new_issues = validate(fixed, lang, kids)
        print(f"Fixed {len(entries)} entries -> {args[1]}")
        if new_issues:
            print(f"  Note: {len(new_issues)} issues remain (may need manual review)")
        else:
            print(f"  ✓ Output passes all Netflix specs")

    elif cmd == 'clean':
        if len(args) < 2:
            print("Usage: netflix_subs.py clean <input.srt> <output.srt> [--lang <code>] [--kids]")
            sys.exit(1)
        entries = parse_srt(args[0])
        if lang is None:
            lang = detect_language(entries)
        cleaned, removed = clean_entries(entries, lang, kids)
        write_srt(cleaned, args[1])

        print(f"Cleaned {len(entries)} entries -> {args[1]}")
        print(f"  Kept: {len(cleaned)} entries")
        print(f"  Removed: {len(removed)} entries")
        if removed:
            print(f"\nRemoved entries:")
            for idx, errs in removed[:10]:
                print(f"  #{idx}: {', '.join(errs)}")
            if len(removed) > 10:
                print(f"  ... and {len(removed) - 10} more")

        new_issues = validate(cleaned, lang, kids)
        if new_issues:
            print(f"\nWarning: {len(new_issues)} issues remain after clean")
        else:
            print(f"\n✓ Output passes all Netflix specs")

    elif cmd == 'report':
        if not args:
            print("Usage: netflix_subs.py report <input.srt> [--lang <code>] [--kids]")
            sys.exit(1)
        entries = parse_srt(args[0])
        if lang is None:
            lang = detect_language(entries)
        issues = validate(entries, lang, kids)
        print_report(args[0], lang, issues, kids)

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

if __name__ == '__main__':
    main()
