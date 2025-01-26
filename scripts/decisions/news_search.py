import requests
from bs4 import BeautifulSoup
import urllib

def search_yahoo_news(query):
    encoded_query = urllib.parse.quote(query)
    url = f'https://news.yahoo.co.jp/search?p={encoded_query}&ei=UTF-8'
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the ol with the class 'newsFeed_list'
        news_feed = soup.find('ol', class_='newsFeed_list')
        
        if news_feed:
            articles = news_feed.find_all('li')  # Find all li elements in the news feed
            
            news_list = []
            for article in articles:
                a_tag = article.find('a')  # Find the a tag within each li
                if a_tag:
                    title = a_tag.get_text()
                    link = a_tag['href']
                    news_list.append({'title': title, 'link': link})
        
            return news_list
        else:
            return None
    else:
        return None

def get_article_content(url):
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the div that contains the article body
        article_body = soup.find('div', class_='article_body highLightSearchTarget')
        
        if article_body:
            # Extract raw text, excluding any images or links
            text = article_body.get_text(separator='\n', strip=True)
            return text
        else:
            return "Article content could not be found."
    else:
        return "Failed to retrieve article content."

# Example of searching for "AI" news
query = 'AI'
news = search_yahoo_news(query)

if news:
    for idx, article in enumerate(news, 1):
        print(f'{idx}. {article["title"]}\n{article["link"]}\n')
    
    # Ask the user to choose a number
    choice = int(input("Enter the number of the article you're interested in: "))
    
    if 1 <= choice <= len(news):
        selected_article = news[choice - 1]
        print(f"\nYou selected: {selected_article['title']}")
        
        # Get the full article content
        article_content = get_article_content(selected_article['link'])
        print("\nArticle Content:")
        print(article_content)
    else:
        print("Invalid choice.")
else:
    print("Failed to retrieve news.")
