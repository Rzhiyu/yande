import threading
import requests
import json
from bs4 import BeautifulSoup

prefix = "https://yande.re/post/show/"
class Extract_ori(threading.Thread):
    def __init__(self, n,url):
        super(Extract_ori,self).__init__()
        self.thread_nums = n
        self.url = url
        self.headers = {
            'Referer':"https://yande.re/post?tags=haku89",
            'Cookie':'''vote=1; tag-script=; forum_post_last_read_at="2022-11-08T03:54:37.747-05:00"; session_yande-re=LLhxlptjuVYN2XMka8YEdyEu0Ak2J5nievRu2ddgc5VvGdw/meshVUnZ3gWZEQ5nFu/drMh35aAhgaIk0tqsseJwQr98/qILI6WcgyWgah+IzQQQnjatOEsikTk5GsRugBvK8VXPgre68dMmWCkaJyA/u6fPP2CuG0JUkUEXgcuwwZQPYVeoywlForfoJVk8POkceeLCVtRz9pOTqoqQICgbmbpB9OJWngCd4wC46IKVcvGKCYn3jOqj2pAOg7IoHRJ0hD114BzFb8sf9VW9MJvS9Ct6auo6Y74IPdWIuaSM63vXFD0kElp57btZFw==--9HGQaOnhQeZqTyAX--BXgVi6glmQetB7jmfXTS0w==''',
            'User-agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
        }
    def run(self) -> None:
        response = requests.get(self.url,headers=self.headers)
        soup = BeautifulSoup(response.text,'lxml')
        res = soup.select('.status-notice a')
        try:
            ori_link = res[0].attrs['href']
        except:
            pass
        return super().run()
if __name__=='__main__':
    o = Extract_ori(1,'https://yande.re/post/show/1030527')
    o.start()
    
    s = '[1,2,3]'
    res = json.loads(s)
    print(type(res),res)
