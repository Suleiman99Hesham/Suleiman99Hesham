#!/usr/bin/env python3
import os
import requests
from collections import defaultdict
from datetime import datetime, timezone

TOKEN = os.environ.get('GITHUB_TOKEN', '')
USERNAME = 'Suleiman99Hesham'

HEADERS = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json',
}

QUERY = """
query($login: String!, $from: DateTime!) {
  user(login: $login) {
    pullRequests { totalCount }
    issues { totalCount }
    repositories(ownerAffiliations: [OWNER], isFork: false, first: 100) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node { name color }
          }
        }
      }
    }
    contributionsCollection(from: $from) {
      totalCommitContributions
      restrictedContributionsCount
    }
  }
}
"""

CARD_BG     = '#0D1117'
BORDER      = '#30363D'
TEXT        = '#E6EDF3'
MUTED       = '#8B949E'
FONT        = 'Segoe UI, Ubuntu, sans-serif'


def fetch_stats():
    year_start = datetime(datetime.now(timezone.utc).year, 1, 1, tzinfo=timezone.utc).isoformat()
    resp = requests.post(
        'https://api.github.com/graphql',
        json={'query': QUERY, 'variables': {'login': USERNAME, 'from': year_start}},
        headers=HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    result = resp.json()
    if 'errors' in result:
        raise RuntimeError(result['errors'])

    user  = result['data']['user']
    repos = user['repositories']['nodes']

    total_stars = sum(r['stargazerCount'] for r in repos)
    cc = user['contributionsCollection']
    total_commits = cc['totalCommitContributions'] + cc['restrictedContributionsCount']

    lang_data = defaultdict(lambda: {'size': 0, 'color': '#858585'})
    for repo in repos:
        for edge in repo['languages']['edges']:
            name  = edge['node']['name']
            color = edge['node']['color'] or '#858585'
            lang_data[name]['size']  += edge['size']
            lang_data[name]['color']  = color

    total_size = sum(v['size'] for v in lang_data.values()) or 1
    top_langs  = sorted(lang_data.items(), key=lambda x: x[1]['size'], reverse=True)[:8]

    return {
        'stars':   total_stars,
        'commits': total_commits,
        'prs':     user['pullRequests']['totalCount'],
        'issues':  user['issues']['totalCount'],
        'repos':   user['repositories']['totalCount'],
        'year':    datetime.now(timezone.utc).year,
        'langs': [
            {
                'name':    name,
                'percent': round(info['size'] / total_size * 100, 1),
                'color':   info['color'],
            }
            for name, info in top_langs
        ],
    }


def stats_svg(stats):
    rows = [
        ('Total Stars Earned',                   stats['stars'],   '#FFA500'),
        (f'Total Commits ({stats["year"]})',      stats['commits'], '#4EC9B0'),
        ('Total Pull Requests',                  stats['prs'],     '#58A6FF'),
        ('Total Issues',                         stats['issues'],  '#F85149'),
        ('Public Repositories',                  stats['repos'],   '#BC8CFF'),
    ]
    w, row_h = 495, 33
    h = 80 + len(rows) * row_h + 16

    lines = []
    for i, (label, value, color) in enumerate(rows):
        y = 75 + i * row_h
        lines.append(
            f'<text x="32" y="{y}" fill="{MUTED}" font-size="13">{label}:</text>'
            f'<text x="{w - 32}" y="{y}" fill="{color}" font-size="13"'
            f' font-weight="600" text-anchor="end">{value:,}</text>'
        )

    return f'''<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">
  <rect width="{w}" height="{h}" rx="10" fill="{CARD_BG}" stroke="{BORDER}" stroke-width="1"/>
  <text x="32" y="38" fill="{TEXT}" font-size="16" font-weight="700"
        font-family="{FONT}">Suleiman&#39;s GitHub Stats</text>
  <line x1="32" y1="50" x2="{w - 32}" y2="50" stroke="{BORDER}"/>
  <g font-family="{FONT}">
    {''.join(lines)}
  </g>
</svg>'''


def langs_svg(langs):
    if not langs:
        return (
            f'<svg width="300" height="60" xmlns="http://www.w3.org/2000/svg">'
            f'<rect width="300" height="60" rx="10" fill="{CARD_BG}" stroke="{BORDER}" stroke-width="1"/>'
            f'<text x="150" y="36" fill="{MUTED}" font-size="13" text-anchor="middle"'
            f' font-family="{FONT}">No language data available</text></svg>'
        )

    total = sum(l['percent'] for l in langs) or 1
    for l in langs:
        l['percent'] = round(l['percent'] / total * 100, 1)

    w      = 300
    bar_y  = 58
    bar_h  = 8
    bar_w  = w - 48
    row_h  = 26
    h      = bar_y + bar_h + 16 + len(langs) * row_h + 16

    segments = []
    x = 24.0
    for lang in langs:
        seg_w = max(bar_w * lang['percent'] / 100, 1)
        segments.append(
            f'<rect x="{x:.1f}" y="{bar_y}" width="{seg_w:.1f}"'
            f' height="{bar_h}" fill="{lang["color"]}"/>'
        )
        x += seg_w

    legend = []
    for i, lang in enumerate(langs):
        y = bar_y + bar_h + 20 + i * row_h
        legend.append(
            f'<circle cx="32" cy="{y - 4}" r="5" fill="{lang["color"]}"/>'
            f'<text x="44" y="{y}" fill="{MUTED}" font-size="12"'
            f' font-family="{FONT}">{lang["name"]}</text>'
            f'<text x="{w - 24}" y="{y}" fill="{TEXT}" font-size="12" font-weight="600"'
            f' text-anchor="end" font-family="{FONT}">{lang["percent"]}%</text>'
        )

    body = '\n  '.join(segments + legend)
    return f'''<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">
  <rect width="{w}" height="{h}" rx="10" fill="{CARD_BG}" stroke="{BORDER}" stroke-width="1"/>
  <text x="24" y="32" fill="{TEXT}" font-size="16" font-weight="700"
        font-family="{FONT}">Top Languages</text>
  <line x1="24" y1="44" x2="{w - 24}" y2="44" stroke="{BORDER}"/>
  <rect x="24" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="4" fill="{BORDER}"/>
  {body}
</svg>'''


def main():
    os.makedirs('stats', exist_ok=True)
    stats = fetch_stats()

    with open('stats/github-stats.svg', 'w', encoding='utf-8') as f:
        f.write(stats_svg(stats))
    print(f'generated stats/github-stats.svg  ({stats["stars"]} stars, {stats["commits"]} commits)')

    with open('stats/github-langs.svg', 'w', encoding='utf-8') as f:
        f.write(langs_svg(stats['langs']))
    print(f'generated stats/github-langs.svg  ({len(stats["langs"])} languages)')


if __name__ == '__main__':
    main()
