import feedparser
import datetime

keyWord = '田中先生'
rssDatas = feedparser.parse('https://news.google.com/rss/search?q=%27' + keyWord + '%27&hl=ja&gl=JP&ceid=JP:ja')
for rssData in rssDatas.entries:
  # 日付を変換
  updateTime=  datetime.datetime.strptime(rssData.published, '%a, %d %b %Y %H:%M:%S GMT').strftime('%Y/%m/%d')
  print('----'*30)
  print('タイトル：',rssData.title)
  print('日時：',updateTime)
  print('リンク：',rssData.link)
