#!/usr/bin/env python3
"""
Synchronisiert VueTraccar Marker mit WordPress Posts
- Unterstützt mehrere Links pro RST-Datei
- Findet Marker ohne RST-Files in der Datenbank
"""

import glob
import os
import re
import requests
import tomli
from typing import Optional, List, Tuple, Set
from html.parser import HTMLParser
import sys


class LinkExtractor(HTMLParser):
    """Extrahiert alle Links aus HTML"""
    def __init__(self):
        super().__init__()
        self.links = []
    
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            attrs_dict = dict(attrs)
            if 'href' in attrs_dict:
                self.links.append(attrs_dict['href'])


def load_config():
    """Lade config.toml"""
    with open('config.toml', 'rb') as f:
        return tomli.load(f)


def normalize_wordpress_url(url: str, config: dict) -> str:
    """
    Normalize WordPress URL based on home mode.
    Always convert to cloud URL for API operations.
    """
    if not url or not isinstance(url, str):
        return url

    # Always normalize to cloud URL for WordPress API operations
    # The API always uses the cloud URL regardless of home mode
    url = url.replace('tagebuch.home.smallfamilybusiness.net', 'tagebuch.smallfamilybusiness.net')

    return url


def extract_all_wordpress_urls(content: str, wp_base_url: str) -> List[str]:
    """Extrahiere ALLE WordPress Post URLs aus Datei"""
    found_urls = []

    # Support both cloud and home URLs
    base_domains = ['tagebuch.smallfamilybusiness.net', 'tagebuch.home.smallfamilybusiness.net']

    # Methode 1: HTML Parser
    parser = LinkExtractor()
    try:
        parser.feed(content)
        for url in parser.links:
            if any(domain in url.lower() for domain in base_domains):
                clean_url = url.rstrip('/')
                if clean_url not in found_urls:
                    found_urls.append(clean_url)
    except:
        pass

    # Methode 2: Regex für href
    html_links = re.findall(r'href=["\']([^"\']+)["\']', content, re.IGNORECASE)
    for url in html_links:
        if any(domain in url.lower() for domain in base_domains):
            clean_url = url.rstrip('/')
            if clean_url not in found_urls:
                found_urls.append(clean_url)

    # Methode 3: Plain URLs
    plain_urls = re.findall(r'https?://[^\s<>"]+', content)
    for url in plain_urls:
        if any(domain in url.lower() for domain in base_domains):
            clean_url = url.rstrip('/').rstrip('>')
            if clean_url not in found_urls:
                found_urls.append(clean_url)

    return found_urls


def extract_title_from_html(content: str) -> Optional[str]:
    """Extrahiere ersten Titel aus HTML <a> Tag"""
    match = re.search(r'<a[^>]*>([^<]+)</a>', content, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def get_post_id_from_url(config, post_url: str) -> Optional[int]:
    """Hole WordPress Post ID anhand der URL"""
    wp_url = config['wordpress_url']
    wp_user = config['wordpress_user']
    wp_pass = config['wordpress_app_password']

    # Normalize URL to cloud version for API call
    post_url = normalize_wordpress_url(post_url, config)

    slug = post_url.rstrip('/').split('/')[-1]
    if not slug:
        return None

    try:
        response = requests.get(
            f"{wp_url}/wp-json/wp/v2/posts",
            auth=(wp_user, wp_pass),
            params={'slug': slug, 'per_page': 1},
            timeout=10
        )

        if response.status_code == 200:
            posts = response.json()
            if posts:
                return posts[0]['id']
    except Exception as e:
        print(f"      ⚠️  Fehler beim Abrufen: {e}")

    return None


def get_or_create_tag(config, marker_key: str, description: str = None) -> Optional[int]:
    """Hole oder erstelle WordPress Tag"""
    wp_url = config['wordpress_url']
    wp_user = config['wordpress_user']
    wp_pass = config['wordpress_app_password']
    
    tags_url = f"{wp_url}/wp-json/wp/v2/tags"
    
    # Suche Tag
    try:
        response = requests.get(
            tags_url,
            auth=(wp_user, wp_pass),
            params={'search': marker_key, 'per_page': 10},
            timeout=10
        )
        
        if response.status_code == 200:
            tags = response.json()
            for tag in tags:
                if tag['name'].lower() == marker_key.lower():
                    return tag['id']
    except:
        pass
    
    # Erstelle Tag
    try:
        response = requests.post(
            tags_url,
            auth=(wp_user, wp_pass),
            json={
                'name': marker_key,
                'slug': marker_key.lower(),
                'description': description or f'VueTraccar: {marker_key}'
            },
            timeout=10
        )
        
        if response.status_code == 201:
            return response.json()['id']
        elif response.status_code == 400:
            # Existiert doch, nochmal suchen
            response = requests.get(
                tags_url,
                auth=(wp_user, wp_pass),
                params={'slug': marker_key.lower(), 'per_page': 1},
                timeout=10
            )
            if response.status_code == 200:
                tags = response.json()
                if tags:
                    return tags[0]['id']
    except Exception as e:
        print(f"      ❌ Tag-Fehler: {e}")
    
    return None


def add_tag_to_post(config, post_id: int, tag_id: int) -> Tuple[bool, str]:
    """Füge Tag zu Post hinzu"""
    wp_url = config['wordpress_url']
    wp_user = config['wordpress_user']
    wp_pass = config['wordpress_app_password']
    
    try:
        get_response = requests.get(
            f"{wp_url}/wp-json/wp/v2/posts/{post_id}",
            auth=(wp_user, wp_pass),
            timeout=10
        )
        
        if get_response.status_code != 200:
            return False, f"HTTP {get_response.status_code}"
        
        existing_tags = get_response.json().get('tags', [])
        
        if tag_id in existing_tags:
            return True, "already_tagged"
        
        new_tags = existing_tags + [tag_id]
        
        update_response = requests.post(
            f"{wp_url}/wp-json/wp/v2/posts/{post_id}",
            auth=(wp_user, wp_pass),
            json={'tags': new_tags},
            timeout=10
        )
        
        if update_response.status_code == 200:
            return True, "tagged"
        else:
            return False, f"HTTP {update_response.status_code}"
        
    except Exception as e:
        return False, str(e)


def get_markers_from_database(config) -> Set[str]:
    """
    Hole alle Marker-Keys aus der Datenbank/Backend
    Ruft das Backend auf um alle verfügbaren Marker zu bekommen
    """
    markers = set()
    
    try:
        # Versuche Route-Daten zu laden (enthält alle Marker)
        # Alternativ: Direkt dtraccar Python-Modul nutzen
        import sys
        sys.path.insert(0, 'dtraccar')
        
        try:
            import dtraccar
            T = dtraccar.Traccar()
            
            # Hole alle Standstills/Marker aus den Daten
            # Das ist projektspezifisch - hier ein Beispiel
            
            # Option A: Aus travels.yml
            import yaml
            if os.path.exists('travels.yml'):
                with open('travels.yml', 'r') as f:
                    travels = yaml.safe_load(f)
                    if travels:
                        for travel_key, travel_data in travels.items():
                            standstills = travel_data.get('standstills', [])
                            for standstill in standstills:
                                if 'key' in standstill:
                                    markers.add(standstill['key'])
            
            print(f"  ℹ️  Gefunden: {len(markers)} Marker in travels.yml")
            
        except Exception as e:
            print(f"  ⚠️  Konnte Marker aus Datenbank nicht laden: {e}")
    
    except:
        pass
    
    return markers


def main():
    print("=" * 80)
    print("VueTraccar → WordPress Synchronisation (Erweitert)")
    print("- Unterstützt mehrere Links pro RST")
    print("- Findet Marker ohne RST-Files")
    print("=" * 80)
    print()
    
    # Config laden
    try:
        config = load_config()
    except Exception as e:
        print(f"❌ Config-Fehler: {e}")
        return
    
    wp_url = config.get('wordpress_url', '')
    if not wp_url:
        print("❌ Keine WordPress URL!")
        return
    
    print(f"WordPress: {wp_url}\n")
    
    # Phase 1: RST-Dateien verarbeiten
    print("=" * 80)
    print("PHASE 1: RST-Dateien verarbeiten")
    print("=" * 80)
    print()
    
    rst_files = sorted(glob.glob('documents/marker*.rst'))
    print(f"📁 Gefunden: {len(rst_files)} RST-Dateien\n")
    
    stats = {
        'with_link': 0,
        'without_link': 0,
        'multi_link': 0,
        'tagged': 0,
        'already_tagged': 0,
        'failed': 0,
        'total_posts_tagged': 0
    }
    
    processed_markers = set()
    
    for i, filepath in enumerate(rst_files, 1):
        marker_key = os.path.basename(filepath).replace('.rst', '')
        processed_markers.add(marker_key)
        
        print(f"[{i}/{len(rst_files)}] {marker_key}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"  ❌ Lesefehler: {e}\n")
            stats['failed'] += 1
            continue
        
        # Extrahiere Titel
        title = extract_title_from_html(content)
        if title:
            print(f"  📍 {title}")
        
        # Extrahiere ALLE URLs
        post_urls = extract_all_wordpress_urls(content, wp_url)
        
        if not post_urls:
            print(f"  ⚠️  Kein WordPress-Link\n")
            stats['without_link'] += 1
            continue
        
        if len(post_urls) > 1:
            print(f"  🔗 {len(post_urls)} Links gefunden:")
            stats['multi_link'] += 1
        else:
            stats['with_link'] += 1
        
        # Erstelle/hole Tag
        tag_id = get_or_create_tag(config, marker_key, title)
        if not tag_id:
            print(f"  ❌ Konnte Tag nicht erstellen\n")
            stats['failed'] += 1
            continue
        
        print(f"  🏷️  Tag-ID: {tag_id}")
        
        # Tagge alle gefundenen Posts
        posts_tagged_count = 0
        for j, post_url in enumerate(post_urls, 1):
            print(f"    [{j}] {post_url}")
            
            post_id = get_post_id_from_url(config, post_url)
            if not post_id:
                print(f"      ❌ Post nicht gefunden")
                continue
            
            print(f"      📄 Post-ID: {post_id}")
            
            success, message = add_tag_to_post(config, post_id, tag_id)
            
            if success:
                if message == "already_tagged":
                    print(f"      ⚠️  Bereits getaggt")
                    stats['already_tagged'] += 1
                else:
                    print(f"      ✅ Getaggt!")
                    stats['tagged'] += 1
                    posts_tagged_count += 1
            else:
                print(f"      ❌ Fehler: {message}")
        
        stats['total_posts_tagged'] += posts_tagged_count
        print()
    
    # Phase 2: Marker ohne RST-Files finden
    print("=" * 80)
    print("PHASE 2: Marker ohne RST-Files")
    print("=" * 80)
    print()
    
    all_markers = get_markers_from_database(config)
    
    if all_markers:
        markers_without_rst = all_markers - processed_markers
        
        if markers_without_rst:
            print(f"⚠️  {len(markers_without_rst)} Marker ohne RST-Datei:\n")
            for marker in sorted(markers_without_rst):
                print(f"  - {marker}")
                
                # Erstelle trotzdem Tags
                tag_id = get_or_create_tag(config, marker, f"Marker {marker}")
                if tag_id:
                    print(f"    🏷️  Tag erstellt (ID: {tag_id})")
                else:
                    print(f"    ❌ Tag-Erstellung fehlgeschlagen")
            print()
        else:
            print("✅ Alle Marker haben RST-Dateien\n")
    else:
        print("ℹ️  Keine zusätzlichen Marker in Datenbank gefunden\n")
    
    # Zusammenfassung
    print("=" * 80)
    print("ZUSAMMENFASSUNG")
    print("=" * 80)
    print(f"RST-Dateien gesamt:           {len(rst_files)}")
    print(f"  - Mit 1 Link:               {stats['with_link']}")
    print(f"  - Mit mehreren Links:       {stats['multi_link']}")
    print(f"  - Ohne Link:                {stats['without_link']}")
    print()
    print(f"Posts neu getaggt:            {stats['tagged']}")
    print(f"Posts bereits getaggt:        {stats['already_tagged']}")
    print(f"Posts total getaggt:          {stats['total_posts_tagged']}")
    print(f"Fehler:                       {stats['failed']}")
    print()
    
    if all_markers:
        print(f"Marker ohne RST:              {len(all_markers - processed_markers)}")
    
    print()
    
    if stats['tagged'] > 0:
        print("✅ Synchronisation erfolgreich!")
        print("\nTeste:")
        print("  python app.py")
        print("  curl http://localhost:5999/wordpress/posts/markerXXXXXX")
    
    if stats['without_link'] > 0:
        print(f"\n⚠️  {stats['without_link']} RST-Dateien ohne Link")
        print("Füge Links hinzu:")
        print('  <a href="https://tagebuch.smallfamilybusiness.net/post/">Titel</a>')


if __name__ == '__main__':
    main()
