"""
WordPress REST API Integration for VueTraccar
Handles automatic loading of WordPress posts for map markers
Posts are tagged with location keys (marker123456...)
"""

import requests
import functools
import time
from datetime import datetime, timedelta
import arrow
import html  # NEU: Für HTML Entity Dekodierung
from typing import Dict, List, Optional


class WordPress:
    def __init__(self, config: Dict):
        """Initialize WordPress API client with configuration"""
        self.base_url = config.get('wordpress_url', '').rstrip('/')
        self.username = config.get('wordpress_user', '')
        self.password = config.get('wordpress_password', '')
        self.app_password = config.get('wordpress_app_password', '')
        
        # Cache settings
        self.cache_duration = config.get('wordpress_cache_duration', 3600)  # 1 hour default
        self._posts_cache = {}
        self._cache_timestamp = {}
        
        # Validate configuration
        if not self.base_url:
            print("WARNING: WordPress URL not configured")
            
    def _get_auth(self):
        """Get authentication for WordPress REST API"""
        if self.app_password and self.username:
            return (self.username, self.app_password)
        elif self.username and self.password:
            return (self.username, self.password)
        return None
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is still valid"""
        if key not in self._cache_timestamp:
            return False
        cache_age = time.time() - self._cache_timestamp[key]
        return cache_age < self.cache_duration
    
    def _cache_posts(self, key: str, posts: List[Dict]):
        """Cache posts for given key"""
        self._posts_cache[key] = posts
        self._cache_timestamp[key] = time.time()
    
    def get_posts_by_tag(self, tag: str, limit: int = 10) -> List[Dict]:
        """
        Get WordPress posts by tag name (case-insensitive)
        
        Args:
            tag: Tag name (e.g., 'marker123456789' or 'marker360417M56303')
            limit: Maximum number of posts to return
            
        Returns:
            List of post dictionaries with relevant fields
        """
        if not self.base_url:
            return []
            
        # Check cache first (use lowercase for cache key)
        cache_key = f"{tag.lower()}_{limit}"
        if self._is_cache_valid(cache_key):
            print(f"WordPress: Using cached posts for tag '{tag}'")
            return self._posts_cache[cache_key]
        
        try:
            # Build API URL for posts with tag
            api_url = f"{self.base_url}/wp-json/wp/v2/posts"
            
            # Search for tag (case-insensitive search)
            tags_url = f"{self.base_url}/wp-json/wp/v2/tags"
            tags_params = {
                'search': tag,  # WordPress 'search' is case-insensitive
                'per_page': 10  # Get more results to find exact match
            }
            
            auth = self._get_auth()
            tags_response = requests.get(tags_url, params=tags_params, auth=auth, timeout=30)
            tags_response.raise_for_status()
            tags_data = tags_response.json()
            
            # Find exact match (case-insensitive comparison)
            tag_id = None
            for tag_item in tags_data:
                if tag_item['name'].lower() == tag.lower():
                    tag_id = tag_item['id']
                    print(f"WordPress: Found tag '{tag}' (name: '{tag_item['name']}') with ID {tag_id}")
                    break
            
            if not tag_id:
                print(f"WordPress: No tag found for '{tag}'")
                self._cache_posts(cache_key, [])
                return []
            
            # Now get posts with this tag
            posts_params = {
                'tags': tag_id,
                'per_page': limit,
                'status': 'publish',
                '_embed': True  # Include featured images and other embedded data
            }
            
            posts_response = requests.get(api_url, params=posts_params, auth=auth, timeout=30)
            posts_response.raise_for_status()
            posts_data = posts_response.json()
            
            # Process posts to extract relevant information
            processed_posts = []
            for post in posts_data:
                # Extract featured image if available
                featured_image = None
                if '_embedded' in post and 'wp:featuredmedia' in post['_embedded']:
                    featured_media = post['_embedded']['wp:featuredmedia']
                    if featured_media:
                        featured_image = featured_media[0].get('source_url', '')
                
                # NEU: Dekodiere HTML Entities in title, excerpt, content
                processed_post = {
                    'id': post['id'],
                    'title': html.unescape(post['title']['rendered']),
                    'excerpt': html.unescape(post['excerpt']['rendered']),
                    'content': html.unescape(post['content']['rendered']),
                    'date': post['date'],
                    'date_gmt': post['date_gmt'],
                    'modified': post['modified'],
                    'link': post['link'],
                    'slug': post['slug'],
                    'featured_image': featured_image,
                    'author': post.get('author', ''),
                    'status': post['status']
                }
                processed_posts.append(processed_post)
            
            # Cache the results
            self._cache_posts(cache_key, processed_posts)
            
            print(f"WordPress: Found {len(processed_posts)} posts for tag '{tag}'")
            return processed_posts
            
        except requests.exceptions.RequestException as e:
            print(f"WordPress API error for tag '{tag}': {e}")
            return []
        except Exception as e:
            print(f"WordPress processing error for tag '{tag}': {e}")
            return []
    
    def get_posts_by_multiple_tags(self, tags: List[str], limit: int = 50) -> Dict[str, List[Dict]]:
        """
        Get WordPress posts for multiple tags at once
        
        Args:
            tags: List of tag names
            limit: Maximum total posts to return per tag
            
        Returns:
            Dictionary mapping tag names to lists of posts
        """
        results = {}
        for tag in tags:
            results[tag] = self.get_posts_by_tag(tag, limit)
        return results
    
    def clear_cache(self):
        """Clear the posts cache"""
        self._posts_cache.clear()
        self._cache_timestamp.clear()
        print("WordPress: Cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            'cached_keys': list(self._posts_cache.keys()),
            'cache_size': len(self._posts_cache),
            'cache_timestamps': self._cache_timestamp
        }
    
    def format_posts_for_infowindow(self, posts: List[Dict], max_posts: int = 3) -> str:
        """
        Format posts for display in Google Maps InfoWindow
        
        Args:
            posts: List of WordPress posts
            max_posts: Maximum number of posts to display
            
        Returns:
            HTML string formatted for InfoWindow
        """
        if not posts:
            return ""
        
        html_parts = ['<div class="wordpress-posts">']
        
        for i, post in enumerate(posts[:max_posts]):
            # Format date
            try:
                post_date = arrow.get(post['date']).format('DD.MM.YYYY')
            except:
                post_date = post.get('date', '')[:10]
            
            # Clean excerpt (remove HTML tags for summary)
            import re
            excerpt = re.sub(r'<[^>]+>', '', post['excerpt'])[:200]
            if len(excerpt) == 200:
                excerpt += '...'
            
            html_parts.append(f'''
            <div class="wp-post" style="margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 10px;">
                <h4 style="margin: 0 0 5px 0;">
                    <a href="{post['link']}" target="_blank" style="color: #1976d2; text-decoration: none;">
                        {post['title']}
                    </a>
                </h4>
                <div style="font-size: 0.9em; color: #666; margin-bottom: 5px;">
                    {post_date}
                </div>
                <div style="font-size: 0.95em; line-height: 1.4;">
                    {excerpt}
                </div>
            </div>
            ''')
        
        if len(posts) > max_posts:
            html_parts.append(f'<div style="font-style: italic; color: #666;">... und {len(posts) - max_posts} weitere Beiträge</div>')
        
        html_parts.append('</div>')
        
        return ''.join(html_parts)
    
    def test_connection(self) -> bool:
        """Test WordPress REST API connection"""
        if not self.base_url:
            print("WordPress: No URL configured")
            return False
            
        try:
            test_url = f"{self.base_url}/wp-json/wp/v2"
            auth = self._get_auth()
            response = requests.get(test_url, auth=auth, timeout=10)
            response.raise_for_status()
            
            print(f"WordPress: Connection successful to {self.base_url}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"WordPress: Connection failed - {e}")
            return False


if __name__ == '__main__':
    # Test configuration
    test_config = {
        'wordpress_url': 'https://example.com',
        'wordpress_user': 'test_user',
        'wordpress_app_password': 'test_password'
    }
    
    wp = WordPress(test_config)
    print("WordPress API wrapper initialized")
    print("Use wp.test_connection() to test your configuration")