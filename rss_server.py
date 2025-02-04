import feedparser
import redis
import time
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import json
import os
#from dotenv import load_dotenv

# Load environment variables
#load_dotenv()

class RSSServer:
    def __init__(self):
        # Initialize Redis connection
        try:
            self.redis_client = redis.Redis(
                username=os.getenv('REDIS_USER'),
                password=os.getenv('REDIS_PASSWORD'),
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 0)) 
            )
            # Test the connection
            self.redis_client.ping()
            print("Successfully connected to Redis")
        except redis.ConnectionError as e:
            print(f"Failed to connect to Redis: {str(e)}")
            raise
        # Email configuration
        self.email_sender = os.getenv('EMAIL_SENDER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.email_recipient = os.getenv('EMAIL_RECIPIENT')
        
    def add_source(self, url, name):
        """Add new RSS source"""
        try:
            print(f"Attempting to add source: {name} ({url})")
            feed = feedparser.parse(url)
            print(f"Feed parse result: {feed.status if hasattr(feed, 'status') else 'No status'}")
            
            if hasattr(feed, 'status') and feed.status != 200:
                print(f"Failed to fetch RSS feed: status {feed.status}")
                return False, "Failed to fetch RSS feed"
            
            source_data = {
                "url": url,
                "name": name,
                "last_update": datetime.now().isoformat()
            }
            
            # Save source info to Redis
            print("Saving source to Redis")
            self.redis_client.hset("rss_sources", name, json.dumps(source_data))
            
            # Save initial entries
            print(f"Processing {len(feed.entries)} initial entries")
            for entry in feed.entries:
                entry_id = f"{name}:{entry.id if hasattr(entry, 'id') else entry.link}"
                if not self.redis_client.hexists("rss_entries", entry_id):
                    self.redis_client.hset("rss_entries", entry_id, json.dumps({
                        "title": entry.title,
                        "link": entry.link,
                        "published": entry.published if hasattr(entry, 'published') else "",
                        "source": name
                    }))
                    print(f"Saved new entry: {entry.title}")
            
            return True, "Source added successfully"
            
        except Exception as e:
            print(f"Error adding source: {str(e)}")
            return False, str(e)
    
    def check_updates(self):
        """Check for updates in all RSS sources"""
        sources = self.redis_client.hgetall("rss_sources")
        print(f"Found {len(sources)} sources in Redis,{sources}")
        
        for source_name, source_data in sources.items():
            try:
                source_name = source_name.decode('utf-8') if isinstance(source_name, bytes) else source_name
                source_data = source_data.decode('utf-8') if isinstance(source_data, bytes) else source_data
                source = json.loads(source_data)
                print(f"Checking source: {source['name']} ({source['url']})")
                
                feed = feedparser.parse(source['url'])
                print(f"Found {len(feed.entries)} entries in feed")
                
                new_entries = []
                for entry in feed.entries:
                    entry_id = f"{source['name']}:{entry.id if hasattr(entry, 'id') else entry.link}"
                    # Encode entry_id to bytes if it isn't already
                    entry_id_bytes = entry_id.encode('utf-8') if isinstance(entry_id, str) else entry_id
                    print(f"Checking entry: {entry_id}")
                    print(f"Entry ID type: {type(entry_id)}")
                    print(f"Checking existence of: {entry_id_bytes}")
                    exists = self.redis_client.hget("rss_entries", entry_id_bytes)
                    print(f"Exists in Redis: {exists}")
                    if not exists:
                        print(f"New entry found: {entry.title}")
                        obj = {
                            "title": entry.title,
                            "link": entry.link,
                            "published": entry.published if hasattr(entry, 'published') else ""
                        }
                        
                        # Save new entry
                        self.redis_client.hset("rss_entries", entry_id, json.dumps({
                            "title": entry.title,
                            "link": entry.link,
                            "published": entry.published if hasattr(entry, 'published') else "",
                            "source": source['name']
                        }))
                        print(f"Sending email for {len(new_entries)} new entries")
                        self.send_update_email(source['name'], [obj])
                else:
                    print("No new entries found")
                    
            except Exception as e:
                print(f"Error processing source {source_name}: {str(e)}")
    
    def send_update_email(self, source_name, new_entries):
        """Send email notification for new entries"""
        msg_content = f"New updates from {source_name}:\n\n"
        for entry in new_entries:
            msg_content += f"Title: {entry['title']}\n"
            msg_content += f"Link: {entry['link']}\n"
            msg_content += f"Published: {entry['published']}\n"
            msg_content += "-" * 50 + "\n"
        
        msg = MIMEText(msg_content)
        msg['Subject'] = f'RSS Updates from {source_name}'
        msg['From'] = self.email_sender
        msg['To'] = self.email_recipient
        
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
                smtp_server.login(self.email_sender, self.email_password)
                smtp_server.sendmail(self.email_sender, self.email_recipient, msg.as_string())
        except Exception as e:
            print(f"Failed to send email: {e}") 