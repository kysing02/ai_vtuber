import os
import tweepy
import tweepy.errors
import logging

class TwitterAdapter:
    # このファイルのディレクトリパス
    FILE_PATH = os.path.dirname(__file__)

    def __init__(self):
        consumer_key = os.getenv("CONSUMER_KEY")
        consumer_secret = os.getenv("CONSUMER_SECRET")
        bearer_token = os.getenv("BEARER_TOKEN")
        access_token = os.getenv("ACCESS_TOKEN")
        access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")
        # APIインスタンスの作成
        self.client = tweepy.Client(consumer_key=consumer_key,
                            consumer_secret=consumer_secret,
                            bearer_token=bearer_token,
                            access_token=access_token,
                            access_token_secret=access_token_secret)
        
    def post_tweet(self, content: str):
        try:
            self.client.create_tweet(text=content)
            logging.info("ポストの投稿に成功しました：", content)
        except tweepy.errors.TweepyException as e:
            logging.error(f"エラーが発生しました：{e}")
    
if __name__ == "__main__":
    twitter = TwitterAdapter()
    twitter.post_tweet("これはテストメッセージです。")