import requests
from bs4 import BeautifulSoup
import urllib.parse

class Article:
    def __init__(self, title: str, link: str):
        self.title = title
        self.link = link

    def __repr__(self):
        return f"<Article: {self.title[:50]}...>"

class YahooNews:
    def __init__(self):
        self.trending_url = "https://news.yahoo.co.jp/ranking/access/news"  # Base URL for trendings
        self.search_url = "https://news.yahoo.co.jp/search?p={}&ei=UTF-8"  # Search URL

    def _fetch_articles(self, url):
        response = requests.get(url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            news_feed = soup.find('ol', class_='newsFeed_list')
            if news_feed:
                articles = news_feed.find_all('li')
                news_list = []
                for article in articles:
                    a_tag = article.find('a')
                    if a_tag:
                        title = a_tag.get_text(strip=True)
                        link = a_tag['href']
                        news_list.append(Article(title, link))
                return news_list
            else:
                print("No news feed found.")
                return None
        else:
            print(f"Failed to retrieve news. Status code: {response.status_code}")
            return None

    def trendings(self, num: int) -> list[Article]:
        articles = self._fetch_articles(self.trending_url)
        
        if articles:
            return articles[:num]
        else:
            return None

    def search(self, num: int, topics: str) -> list[Article]:
        encoded_query = urllib.parse.quote(topics)
        url = self.search_url.format(encoded_query)
        articles = self._fetch_articles(url)
        
        if articles:
            return articles[:num]
        else:
            return None

    def get_article_content(self, url: str) -> str:
        response = requests.get(url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            article_body = soup.find('div', class_='article_body highLightSearchTarget')
            
            if article_body:
                text = article_body.get_text(separator='\n', strip=True)
                return text
            else:
                return "Article content could not be found."
        else:
            return "Failed to retrieve article content."

# Example usage
if __name__ == "__main__":
    news = YahooNews()
    
    # Get trendings
    recommended_articles = news.trendings(5)
    if recommended_articles:
        print("Trending Articles:")
        for idx, article in enumerate(recommended_articles, 1):
            print(f'{idx}. {article.title}\n{article.link}\n')
    else:
        print("No trendings found.")
    
    # Search for articles
    query = 'AI'
    searched_articles = news.search(5, query)
    if searched_articles:
        print(f"Search Results for '{query}':")
        for idx, article in enumerate(searched_articles, 1):
            print(f'{idx}. {article.title}\n{article.link}\n')
        
        # Ask the user to choose a number
        choice = int(input("Enter the number of the article you're interested in: "))
        
        if 1 <= choice <= len(searched_articles):
            selected_article = searched_articles[choice - 1]
            print(f"\nYou selected: {selected_article.title}")
            
            # Get the full article content
            article_content = news.get_article_content(selected_article.link)
            print("\nArticle Content:")
            print(article_content)
        else:
            print("Invalid choice.")
    else:
        print("No articles found for the search query.")