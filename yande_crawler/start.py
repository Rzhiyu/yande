import requests
import os
import sys
from main import Extract_id
from ori_ext import Extract_ori
from urllib.parse import urlparse, urlsplit
def download(tag, url):
    save_dir = sys.path[0] + '/output/' + tag
    if not os.path.exists(tag):
        os.makedirs(save_dir)
    response = requests.get(url,headers={
        'Referer':"https://yande.re/",
        'User-agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
    })
    file = save_dir +  '/' + url.split('/')[-1]
    if os.path.exists(file):
        pass
    else:
        with open(file,'wb') as f:
            f.write(response.content)
            

if __name__=='__main__':
    tag = 'haku89'
    temp = Extract_id(1,tag)
    temp.start()
    temp.join()

    tlist = []
    for i in temp.id_list:
        o = Extract_ori()