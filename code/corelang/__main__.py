import sys, json, argparse
from pathlib import Path
from .analyzer import analyze

def main():
    ap = argparse.ArgumentParser(
        prog='corelang',
        description='Structural code analysis via d_Λ (kernel distance).')
    ap.add_argument('path', help='file to analyze')
    ap.add_argument('--lang', choices=['auto', 'py', 'js'], default='auto')
    ap.add_argument('--threshold', type=int, default=2)
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()

    p = Path(args.path)
    if not p.exists():
        print(f'error: {p} not found', file=sys.stderr); sys.exit(1)
    lang = args.lang
    if lang == 'auto':
        lang = 'py' if p.suffix in ('.py','.pyw') else 'js'

    result = analyze(str(p), lang, args.threshold)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f'{p.name} ({lang}): {result["units_count"]} units, '
              f'{result["clusters_found"]} clusters, '
              f'{result["worth_extracting"]} worth extracting')
        for c in result['clusters'][:10]:
            m = '★' if c['worth_extracting'] else ' '
            print(f'  [{m}] size={c["size"]} L={c["avg_length"]} '
                  f'Δ={c["projected_delta"]:+d} {c["members"][:3]}')

if __name__ == '__main__':
    main()
