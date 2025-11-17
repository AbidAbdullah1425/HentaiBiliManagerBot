"""
Episode Scraper for hentaimama.io
Extracts: Episode MP4 files, Cover images, Preview images, Episode names, Studios, Genres/Tags
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import os
import json
import re
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class EpisodeScraper:
    def __init__(self, base_url="https://hentaimama.io"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.download_dir = "downloads"
        os.makedirs(self.download_dir, exist_ok=True)
        self.driver = None
    
    def init_selenium(self):
        if self.driver is None:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                print("  ✓ Browser initialized")
            except Exception as e:
                print(f"  Could not initialize Selenium: {e}")
                self.driver = None
    
    def close_selenium(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def delay(self, min_sec=2, max_sec=5):
        time.sleep(random.uniform(min_sec, max_sec))
    
    def get_page(self, url):
        try:
            print(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            self.delay()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Error fetching page: {e}")
            return None
    
    def download_file(self, url, filename):
        try:
            print(f"Downloading: {filename}")
            response = self.session.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            filepath = os.path.join(self.download_dir, filename)
            total_size = int(response.headers.get('content-length', 0))
            
            with open(filepath, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size:
                            percent = (downloaded / total_size) * 100
                            print(f"  Progress: {percent:.1f}%", end='\r')
            
            print(f"\n  Saved: {filepath}")
            self.delay()
            return filepath
        except Exception as e:
            print(f"  Error downloading: {e}")
            return None
    
    def extract_video_with_selenium(self, episode_url):
        try:
            print(f"  Loading with browser to extract video...")
            self.init_selenium()
            
            if not self.driver:
                return None
            
            self.driver.get(episode_url)
            
            time.sleep(4)
            
            video_patterns = [
                r'["\'](https?://[^"\']*javprovider[^"\']+\.mp4[^"\']*)["\']',
                r'(https?://[^\s\'"<>]+javprovider[^\s\'"<>]+\.mp4[^\s\'"<>]*)',
                r'["\'](https?://[^"\']+\.mp4\?st=[^"\']+)["\']',
                r'file["\s:]+["\'](https?://[^"\']+\.mp4[^"\']*)["\']',
                r'src["\s:]+["\'](https?://[^"\']+\.mp4[^"\']*)["\']',
                r'(https?://na-\d+\.javprovider\.com/[^\s\'"<>]+\.mp4[^\s\'"<>]*)',
            ]
            
            try:
                print(f"  Looking for play button...")
                play_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button.play, .play-button, .vjs-big-play-button, button[aria-label*='Play'], .plyr__control--overlaid")
                if play_buttons:
                    print(f"  Clicking play button...")
                    play_buttons[0].click()
                    time.sleep(4)
            except Exception as e:
                print(f"  No play button found or couldn't click: {e}")
            
            try:
                video_elem = self.driver.find_element(By.TAG_NAME, "video")
                
                time.sleep(3)
                
                video_src = video_elem.get_attribute("src")
                if video_src and '.mp4' in video_src:
                    print(f"  ✓ Found video in <video> tag src!")
                    print(f"  URL: {video_src[:80]}...")
                    return video_src
                
                current_src = self.driver.execute_script("return document.querySelector('video') ? document.querySelector('video').currentSrc : null;")
                if current_src and '.mp4' in current_src:
                    print(f"  ✓ Found video via currentSrc!")
                    print(f"  URL: {current_src[:80]}...")
                    return current_src
                
                sources = video_elem.find_elements(By.TAG_NAME, "source")
                for source in sources:
                    src = source.get_attribute("src")
                    if src and '.mp4' in src:
                        print(f"  ✓ Found video in <source> tag!")
                        print(f"  URL: {src[:80]}...")
                        return src
            except Exception as e:
                print(f"  No video element found: {e}")
            
            page_source = self.driver.page_source
            
            print(f"  Searching page source for video URL...")
            for pattern in video_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                for match in matches:
                    if 'javprovider' in match and '.mp4' in match:
                        print(f"  ✓ Found javprovider video URL in page!")
                        print(f"  URL: {match[:80]}...")
                        return match
            
            try:
                iframe_elems = self.driver.find_elements(By.TAG_NAME, "iframe")
                for iframe in iframe_elems:
                    iframe_src = iframe.get_attribute("src")
                    if iframe_src and ('hentaimama' in iframe_src or 'player' in iframe_src.lower() or 'video' in iframe_src.lower()):
                        print(f"  Checking video iframe: {iframe_src[:60]}...")
                        self.driver.switch_to.frame(iframe)
                        time.sleep(3)
                        
                        try:
                            play_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button.play, .play-button, .vjs-big-play-button")
                            if play_buttons:
                                print(f"  Clicking play in iframe...")
                                play_buttons[0].click()
                                time.sleep(3)
                        except:
                            pass
                        
                        try:
                            video_elem = self.driver.find_element(By.TAG_NAME, "video")
                            current_src = self.driver.execute_script("return document.querySelector('video') ? document.querySelector('video').currentSrc : null;")
                            if current_src and '.mp4' in current_src:
                                print(f"  ✓ Found video in iframe via currentSrc!")
                                print(f"  URL: {current_src[:80]}...")
                                self.driver.switch_to.default_content()
                                return current_src
                        except:
                            pass
                        
                        iframe_source = self.driver.page_source
                        for pattern in video_patterns:
                            matches = re.findall(pattern, iframe_source, re.IGNORECASE)
                            for match in matches:
                                if 'javprovider' in match and '.mp4' in match:
                                    print(f"  ✓ Found video in iframe!")
                                    print(f"  URL: {match[:80]}...")
                                    self.driver.switch_to.default_content()
                                    return match
                        
                        self.driver.switch_to.default_content()
            except Exception as e:
                print(f"  Iframe check error: {e}")
                try:
                    self.driver.switch_to.default_content()
                except:
                    pass
            
            print(f"  Extracting all scripts from page...")
            scripts = self.driver.execute_script("""
                var scripts = document.getElementsByTagName('script');
                var allScripts = [];
                for(var i = 0; i < scripts.length; i++) {
                    allScripts.push(scripts[i].innerHTML);
                }
                return allScripts.join('\\n');
            """)
            
            for pattern in video_patterns:
                matches = re.findall(pattern, scripts, re.IGNORECASE)
                for match in matches:
                    if 'javprovider' in match and '.mp4' in match:
                        print(f"  ✓ Found video in page scripts!")
                        print(f"  URL: {match[:80]}...")
                        return match
            
            print(f"  ⚠ No direct video URL found")
            return None
        except Exception as e:
            print(f"  Error with browser extraction: {e}")
            return None
    
    def extract_video_via_ajax(self, soup, episode_url):
        try:
            print(f"  Extracting video via AJAX endpoint...")
            page_text = str(soup)
            
            ajax_pattern = r"action:'get_player_contents',\s*a:'(\d+)'"
            match = re.search(ajax_pattern, page_text)
            
            if not match:
                print(f"  Could not find AJAX episode ID")
                return None
            
            episode_id = match.group(1)
            print(f"  Found episode ID: {episode_id}")
            
            ajax_url = "https://hentaimama.io/wp-admin/admin-ajax.php"
            data = {
                'action': 'get_player_contents',
                'a': episode_id
            }
            
            print(f"  Requesting player content via AJAX...")
            response = self.session.post(ajax_url, data=data, timeout=30)
            
            if response.status_code == 200:
                try:
                    json_response = response.json()
                    
                    if isinstance(json_response, list) and len(json_response) > 0:
                        iframe_pattern = r'src="([^"]+)"'
                        iframe_matches = re.findall(iframe_pattern, json_response[0])
                        
                        if iframe_matches:
                            iframe_url = iframe_matches[0]
                            print(f"  Found iframe URL: {iframe_url[:60]}...")
                            
                            print(f"  Fetching iframe to extract video URL...")
                            iframe_response = self.session.get(iframe_url, timeout=30, headers={
                                'Referer': episode_url
                            })
                            
                            if iframe_response.status_code == 200:
                                iframe_html = iframe_response.text
                                
                                javprovider_patterns = [
                                    r'window\.open\(["\']([^"\']*javprovider[^"\']+)["\']',
                                    r'href=["\']([^"\']*javprovider[^"\']+)["\']',
                                    r'(https?://[^\s\'"<>]*javprovider[^\s\'"<>]+)',
                                    r'file:\s*["\']([^"\']+\.mp4[^"\']*)["\']',
                                ]
                                
                                for pattern in javprovider_patterns:
                                    matches = re.findall(pattern, iframe_html, re.IGNORECASE)
                                    for match in matches:
                                        if 'javprovider' in match or '.mp4' in match:
                                            print(f"  ✓ Found video download URL!")
                                            print(f"  URL: {match[:80]}...")
                                            return match
                
                except Exception as e:
                    print(f"  Error parsing AJAX response: {e}")
            
            return None
        except Exception as e:
            print(f"  Error with AJAX extraction: {e}")
            return None
    
    def scrape_episode(self, episode_url):
        soup = self.get_page(episode_url)
        if not soup:
            return None
        
        episode_data = {
            'url': episode_url,
            'title': '',
            'studio': '',
            'genres': [],
            'cover_image_url': '',
            'preview_images_urls': [],
            'video_url': '',
            'downloaded_files': {
                'video': None,
                'cover': None,
                'previews': []
            }
        }
        
        title_elem = (soup.find('h1', class_='entry-title') or 
                     soup.find('h2', class_='title') or
                     soup.find('div', class_='title') or
                     soup.find('h1') or
                     soup.find('title'))
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            if ' - ' in title_text:
                episode_data['title'] = title_text.split(' - ')[0]
            elif '|' in title_text:
                episode_data['title'] = title_text.split('|')[0].strip()
            else:
                episode_data['title'] = title_text
        
        meta_og_image = soup.find('meta', property='og:image')
        if meta_og_image and meta_og_image.get('content'):
            episode_data['cover_image_url'] = meta_og_image['content']
        else:
            poster_img = soup.find('img', class_='poster') or soup.find('img', class_='wp-post-image')
            if poster_img and poster_img.get('src'):
                episode_data['cover_image_url'] = poster_img['src']
        
        tags = soup.find_all('a', rel='tag')
        episode_data['genres'] = [tag.get_text(strip=True) for tag in tags if tag.get_text(strip=True)]
        
        studio_elem = (soup.find('div', class_='studio') or 
                      soup.find('span', class_='studio') or
                      soup.find('a', {'rel': 'tag', 'href': lambda x: x and '/studio/' in x}))
        if studio_elem:
            episode_data['studio'] = studio_elem.get_text(strip=True)
        
        video_url = self.extract_video_via_ajax(soup, episode_url)
        if video_url:
            episode_data['video_url'] = video_url
        else:
            video_source = soup.find('source', type='video/mp4')
            if video_source and video_source.get('src'):
                episode_data['video_url'] = video_source['src']
            else:
                video_tag = soup.find('video')
                if video_tag:
                    source = video_tag.find('source')
                    if source and source.get('src'):
                        episode_data['video_url'] = source['src']
                
                if not episode_data['video_url']:
                    video_url = self.extract_video_with_selenium(episode_url)
                    if video_url:
                        episode_data['video_url'] = video_url
        
        all_imgs = soup.find_all('img', src=True)
        for img in all_imgs:
            src = img.get('src', '')
            if src and 'data:image' not in src and 'tmdb.org' not in src and src not in episode_data['preview_images_urls']:
                episode_data['preview_images_urls'].append(src)
                if len(episode_data['preview_images_urls']) >= 3:
                    break
        
        return episode_data
    
    def download_episode_files(self, episode_data):
        episode_id = episode_data['url'].split('/')[-1] or episode_data['url'].split('/')[-2]
        
        if episode_data['video_url']:
            video_filename = f"{episode_id}.mp4"
            video_path = self.download_file(episode_data['video_url'], video_filename)
            episode_data['downloaded_files']['video'] = video_path
        
        if episode_data['cover_image_url']:
            ext = episode_data['cover_image_url'].split('.')[-1].split('?')[0]
            cover_filename = f"{episode_id}_cover.{ext}"
            cover_path = self.download_file(episode_data['cover_image_url'], cover_filename)
            episode_data['downloaded_files']['cover'] = cover_path
        
        for idx, preview_url in enumerate(episode_data['preview_images_urls'], 1):
            ext = preview_url.split('.')[-1].split('?')[0]
            preview_filename = f"{episode_id}_preview_{idx}.{ext}"
            preview_path = self.download_file(preview_url, preview_filename)
            if preview_path:
                episode_data['downloaded_files']['previews'].append(preview_path)
        
        return episode_data
    
    def get_recent_episodes(self, limit=5):
        soup = self.get_page(self.base_url)
        if not soup:
            return []
        
        episode_links = []
        
        recent_section = soup.find('div', id='recent-episodes') or soup.find('section', class_='recent-episodes')
        
        if recent_section:
            print(f"\n✓ Found 'Recent Episodes' section")
            articles = recent_section.find_all('article') or recent_section.find_all('div', class_='episode')
        else:
            articles = soup.find_all('article', class_='post') or soup.find_all('article')
            print(f"\nSearching homepage for episode links...")
        
        for article in articles:
            link = article.find('a', href=True)
            if link:
                href = link['href']
                if '/episodes/' in href and href not in episode_links:
                    episode_links.append(href)
        
        if not episode_links:
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link['href']
                if '/episodes/' in href and href not in episode_links:
                    episode_links.append(href)
        
        print(f"Found {len(episode_links)} episode link(s)")
        print(f"Processing {min(len(episode_links), limit)} episodes...\n")
        
        all_episodes = []
        
        for idx, url in enumerate(episode_links[:limit], 1):
            print(f"\n[{idx}/{min(len(episode_links), limit)}] Processing episode...")
            episode_data = self.scrape_episode(url)
            
            if episode_data and episode_data['title']:
                all_episodes.append(episode_data)
                
                print(f"\n{'='*60}")
                print(f"📺 TITLE: {episode_data['title']}")
                print(f"🔗 URL: {episode_data['url']}")
                print(f"🎨 STUDIO: {episode_data['studio'] or 'N/A'}")
                print(f"🏷️  GENRES: {', '.join(episode_data['genres']) or 'N/A'}")
                if episode_data['video_url']:
                    print(f"🎬 VIDEO DOWNLOAD LINK: {episode_data['video_url']}")
                else:
                    print(f"🎬 VIDEO: Not Found")
                print(f"🖼️  COVER: {'Found' if episode_data['cover_image_url'] else 'Not Found'}")
                print(f"📸 PREVIEWS: {len(episode_data['preview_images_urls'])} images")
                print(f"{'='*60}\n")
                
                self.save_episode_to_json(episode_data)
        
        return all_episodes
    
    def save_episode_to_json(self, episode_data, filename="episodes_data.json"):
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = []
            
            episode_id = episode_data['url'].split('/')[-1] or episode_data['url'].split('/')[-2]
            
            existing_ids = [ep.get('url') for ep in data]
            if episode_data['url'] not in existing_ids:
                data.append(episode_data)
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                print(f"  ✓ Saved to {filename}")
        except Exception as e:
            print(f"  Error saving to JSON: {e}")
    
def main():
    print("=== Episode Scraper for hentaimama.io ===")
    print("Extracting from 'Recent Episodes' section\n")
    
    scraper = EpisodeScraper()
    
    try:
        episodes = scraper.get_recent_episodes(limit=5)
        
        if episodes:
            print(f"\n\n{'='*60}")
            print(f"✓ COMPLETE! Processed {len(episodes)} episode(s)")
            print(f"✓ All data saved to: episodes_data.json")
            print(f"{'='*60}\n")
            
            download_choice = input("Do you want to download video files? (y/n): ").lower()
            
            if download_choice == 'y':
                print("\nStarting video downloads...\n")
                for episode in episodes:
                    if episode['video_url']:
                        print(f"\nDownloading: {episode['title']}")
                        scraper.download_episode_files(episode)
                print("\n✓ Downloads complete! Check 'downloads/' folder")
        else:
            print("\nNo episodes found in 'Recent Episodes' section.")
            print("The website structure may have changed.")
    finally:
        scraper.close_selenium()

if __name__ == "__main__":
    main()