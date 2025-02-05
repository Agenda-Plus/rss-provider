from rss_server import RSSServer
import time

def main():
    try:
        rss_server = RSSServer()
        print("RSS Server initialized")
        # Example: Add some RSS sources
        #rss_server.add_source("https://news.ycombinator.com/rss", "Hacker News")
        #rss_server.add_source("https://www.reddit.com/r/programming/.rss", "Reddit Programming")
        rss_server.add_source("https://rss.panewslab.com/en/gtimg/rss", "PANews")
    
        while True: 
            print("Checking for updates...")
            rss_server.check_updates()
            time.sleep(5*60)  # 5 minutes
    except Exception as e:
        print(f"An error occurred: {e}")
        time.sleep(300)  # Wait for 10 seconds before restarting

if __name__ == "__main__":
    main() 