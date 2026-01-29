#!/usr/bin/env python3
"""
Interaktives Matching von Markern zu WordPress Posts
Erstellt automatisch RST-Dateien mit den Verknüpfungen
"""

import requests
import tomli
import yaml
import os
from typing import Dict, List, Tuple
from difflib import SequenceMatcher


def load_config():
    with open('config.toml', 'rb') as f:
        return tomli.load(f)


def get_markers_from_travels() -> Dict[str, Dict]:
    """Lade alle Marker aus travels.yml"""
    if not os.path.exists('travels.yml'):
        return {}
    
    markers = {}
    
    with open('travels.yml', 'r') as f:
        travels = yaml.safe_load(f)
    
    for travel_key, travel_data in travels.items():
        standstills = travel_data.get('standstills', [])
        for standstill in standstills:
            key = standstill.get('key')
            if key:
                markers[key] = {
                    'address': standstill.get('address', ''),
                    'lat': standstill.get('lat', 0),
                    'lng': standstill.get('lng', 0),
                    'von': standstill.get('von', ''),
                    'bis': standstill.get('bis', ''),
                    'travel': travel_key
                }
    
    return markers


def get_all_wordpress_posts(config) -> List[Dict]:
    """Hole alle WordPress Posts"""
    wp_url = config['wordpress_url']
    wp_user = config['wordpress_user']
    wp_pass = config['wordpress_app_password']
    
    posts_url = f"{wp_url}/wp-json/wp/v2/posts"
    all_posts = []
    page = 1
    
    print("Lade WordPress Posts...")
    
    while True:
        try:
            response = requests.get(
                posts_url,
                auth=(wp_user, wp_pass),
                params={'per_page': 100, 'page': page, 'status': 'publish'},
                timeout=30
            )
            
            if response.status_code != 200:
                break
            
            posts = response.json()
            if not posts:
                break
            
            all_posts.extend(posts)
            print(f"  Seite {page}: {len(posts)} Posts")
            page += 1
            
        except Exception as e:
            print(f"  Fehler: {e}")
            break
    
    print(f"✅ {len(all_posts)} Posts geladen\n")
    return all_posts


def get_existing_rst_markers() -> set:
    """Hole alle Marker die bereits RST-Files haben"""
    import glob
    rst_files = glob.glob('documents/marker*.rst')
    return {os.path.basename(f).replace('.rst', '') for f in rst_files}


def similarity(a: str, b: str) -> float:
    """Berechne String-Ähnlichkeit (0-1)"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def find_matching_posts(marker_data: Dict, posts: List[Dict]) -> List[Tuple[Dict, float]]:
    """
    Finde WordPress Posts die zu einem Marker passen könnten
    Returns: [(post, score), ...]
    """
    address = marker_data['address']
    
    # Extrahiere Ort aus Adresse
    # z.B. "Camping Norina, Via Panoramica, 61034 Pesaro" → ["Camping Norina", "Pesaro"]
    address_parts = [part.strip() for part in address.split(',')]
    
    matches = []
    
    for post in posts:
        title = post['title']['rendered']
        content = post['content']['rendered']
        
        # Berechne Score
        score = 0
        
        # Check Titel
        for part in address_parts:
            if len(part) > 3:  # Ignoriere kurze Teile
                title_sim = similarity(part, title)
                if title_sim > 0.5:
                    score += title_sim * 2  # Titel ist wichtiger
                
                # Check auch im Content
                if part.lower() in content.lower():
                    score += 0.5
        
        # Datums-Match (wenn vorhanden)
        if marker_data.get('von'):
            marker_date = marker_data['von'][:10]  # YYYY-MM-DD
            post_date = post['date'][:10]
            
            if marker_date == post_date:
                score += 1.5
            elif abs((marker_date - post_date).days) < 7:  # Innerhalb 1 Woche
                score += 0.5
        
        if score > 0.5:  # Nur relevante Matches
            matches.append((post, score))
    
    # Sortiere nach Score
    matches.sort(key=lambda x: x[1], reverse=True)
    
    return matches[:5]  # Top 5


def create_rst_file(marker_key: str, marker_data: Dict, post_url: str, post_title: str):
    """Erstelle RST-Datei mit WordPress-Link"""
    filepath = f'documents/{marker_key}.rst'
    
    address = marker_data.get('address', marker_key)
    
    content = f'{address}\n'
    content += '=' * len(address) + '\n\n'
    content += f'<a href="{post_url}" target="_parent">{post_title}</a>\n'
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✅ Erstellt: {filepath}")


def interactive_mode(config):
    """Interaktiver Matching-Modus"""
    print("=" * 80)
    print("Interaktives Marker ↔ WordPress Post Matching")
    print("=" * 80)
    print()
    
    # Daten laden
    markers = get_markers_from_travels()
    posts = get_all_wordpress_posts(config)
    existing = get_existing_rst_markers()
    
    # Finde Marker ohne RST
    markers_without_rst = {k: v for k, v in markers.items() if k not in existing}
    
    print(f"📍 Marker gesamt:           {len(markers)}")
    print(f"📄 WordPress Posts:         {len(posts)}")
    print(f"✅ Marker mit RST:          {len(existing)}")
    print(f"⚠️  Marker ohne RST:        {len(markers_without_rst)}")
    print()
    
    if not markers_without_rst:
        print("✅ Alle Marker haben bereits RST-Dateien!")
        return
    
    print("=" * 80)
    print("Starte Matching...")
    print("=" * 80)
    print()
    
    stats = {'matched': 0, 'skipped': 0, 'no_match': 0}
    
    for i, (marker_key, marker_data) in enumerate(markers_without_rst.items(), 1):
        print(f"[{i}/{len(markers_without_rst)}] {marker_key}")
        print(f"  📍 {marker_data['address']}")
        
        # Finde passende Posts
        matches = find_matching_posts(marker_data, posts)
        
        if not matches:
            print(f"  ⚠️  Keine passenden Posts gefunden")
            stats['no_match'] += 1
            print()
            continue
        
        print(f"\n  Gefundene Matches:")
        for j, (post, score) in enumerate(matches, 1):
            title = post['title']['rendered']
            date = post['date'][:10]
            print(f"    [{j}] {title} ({date}) - Score: {score:.2f}")
        
        print()
        
        # Frage Benutzer
        while True:
            choice = input(f"  Auswahl (1-{len(matches)}, s=skip, q=quit): ").strip().lower()
            
            if choice == 'q':
                print("\n👋 Abgebrochen")
                return
            
            if choice == 's':
                print("  ⏭️  Übersprungen\n")
                stats['skipped'] += 1
                break
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(matches):
                    post, score = matches[idx]
                    
                    # Erstelle RST-Datei
                    create_rst_file(
                        marker_key,
                        marker_data,
                        post['link'],
                        post['title']['rendered']
                    )
                    
                    stats['matched'] += 1
                    print()
                    break
                else:
                    print("  ❌ Ungültige Nummer")
            except ValueError:
                print("  ❌ Bitte Zahl, 's' oder 'q' eingeben")
    
    # Zusammenfassung
    print("=" * 80)
    print("ZUSAMMENFASSUNG")
    print("=" * 80)
    print(f"Gematched:     {stats['matched']}")
    print(f"Übersprungen:  {stats['skipped']}")
    print(f"Kein Match:    {stats['no_match']}")
    print()
    
    if stats['matched'] > 0:
        print("✅ Neue RST-Dateien erstellt!")
        print("\nNächster Schritt:")
        print("  python sync_rst_to_wordpress.py")


def automatic_mode(config, threshold=0.8):
    """Automatisches Matching (nur hohe Scores)"""
    print("=" * 80)
    print("Automatisches Matching (hohe Konfidenz)")
    print(f"Threshold: {threshold}")
    print("=" * 80)
    print()
    
    markers = get_markers_from_travels()
    posts = get_all_wordpress_posts(config)
    existing = get_existing_rst_markers()
    
    markers_without_rst = {k: v for k, v in markers.items() if k not in existing}
    
    print(f"⚠️  {len(markers_without_rst)} Marker ohne RST\n")
    
    stats = {'auto_matched': 0, 'manual_needed': 0}
    
    for marker_key, marker_data in markers_without_rst.items():
        matches = find_matching_posts(marker_data, posts)
        
        if matches and matches[0][1] >= threshold:
            # Hoher Score = automatisch matchen
            post, score = matches[0]
            
            print(f"✅ {marker_key}")
            print(f"  → {post['title']['rendered']} (Score: {score:.2f})")
            
            create_rst_file(
                marker_key,
                marker_data,
                post['link'],
                post['title']['rendered']
            )
            
            stats['auto_matched'] += 1
        else:
            print(f"⚠️  {marker_key}: {marker_data['address'][:50]}...")
            print(f"  → Manuelles Matching erforderlich")
            stats['manual_needed'] += 1
    
    print()
    print("=" * 80)
    print(f"Auto-matched:       {stats['auto_matched']}")
    print(f"Manual benötigt:    {stats['manual_needed']}")
    print()
    
    if stats['manual_needed'] > 0:
        print("Für die restlichen:")
        print("  python match_markers_to_posts.py --interactive")


def main():
    import sys
    
    config = load_config()
    
    if '--auto' in sys.argv:
        automatic_mode(config)
    else:
        interactive_mode(config)


if __name__ == '__main__':
    main()
