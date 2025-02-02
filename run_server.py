from rss_server import RSSServer
import time

def main():
    rss_server = RSSServer()
    
    # Example: Add some RSS sources
    #rss_server.add_source("https://news.ycombinator.com/rss", "Hacker News")
    #rss_server.add_source("https://www.reddit.com/r/programming/.rss", "Reddit Programming")
    rss_server.add_source("https://rss.panewslab.com/en/gtimg/rss", "PANews")
    
    # Check for updates every 30 minutes
    while True:
        print("Checking for updates...")
        rss_server.check_updates()
        time.sleep(5*60)  # 5 minutes

if __name__ == "__main__":
    main() 