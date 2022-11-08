import threading
import requests
import json
from bs4 import BeautifulSoup

prefix = "https://yande.re/post/show/"
class Extract_id(threading.Thread):
    def __init__(self, n, tag):
        super(Extract_id,self).__init__()
        self.thread_nums = n
        self.url = 'https://yande.re/post?tags=' + tag
        self.headers = {
            'Cookie':'''vote=1; tag-script=; forum_post_last_read_at="2022-11-08T03:22:53.808-05:00"; session_yande-re=p7jtzJqnMte6COm5J8ZZBaO6QupQZ1mrt09/5ksd69ZXNwl+JYmRyRh6+MfykAETiEhg+6Kx/HO1j9F2ZLv4XKWZ7MLMvcHZJbdjbJdfbd0SYlPPsIrWom5R66a0LOVbguMEY5J07SSEIzrVDGFMxhtDHM1tM8uZguYVpJFmhryRWLqvFX2vrRXnU8cE/68FkI0PTk1XxUMiruAGG/fkypAuTUdPTe1HVudyaRTA7MUoZLpagNvpvqImyK/hdtghVe5rCBogH0Gx2gmS5jce/YzMet6fBbIUO53EZO5DhS5qEDg+gMX8mw4rl694vQ==--iQcGOnGPSssMwclB--rYSCXDZqYJDibt351UM6Bw==''',
            'User-agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
        }
    def run(self) -> None:
        response = requests.get(self.url,headers=self.headers)
        soup = BeautifulSoup(response.text,'lxml')
        res = soup.select('script')
        
        try:
            content = json.loads(res[-1].get_text())
            self.id_list = [prefix + str(i["id"]) for i in content]
        except:
            pass
        return super().run()
if __name__=='__main__':
    o = Extract_id(1)
    o.start()
