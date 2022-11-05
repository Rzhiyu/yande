from ast import arg
from multiprocessing import Pool
from os import name, path
from pymysql import cursors
from urllib.parse import quote
import requests
import json
import re
import time
import os
import pymysql
import datetime
import urllib3
import argparse
import threading
import pathlib
from tqdm import tqdm, trange

from database_for_crawler import Mydatabase
requests.adapters.DEFAULT_RETRIES = 5   #增加重连次数
sem = None
class twitter_crawler():
    image_format = ('jpg','png')
    image_name = ('orig','thumb','small','medium','large','4096x4096')
    image_save_pattern = '?format={}&name={}'
    
    def __init__(self,user_name,task_id,dir) -> None:
        self.task_id = task_id
        self.connect = Mydatabase()
        self.path = dir + '/' + user_name + '/'
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        self.cur_cursor = ''
        self.config = json.loads(open('data.json','r').read())[0]                           #加载配置文件
        self.twitter_url = self.config['twitter_url']                                       #获取得到的main文件id的url
        self.twitter_headers = self.config['twitter_headers']                               #获取对应的headers
        self.user_name = user_name
        self.TwitterMedia_listurl = self.config['media_url'].format(self.user_name)         #获取用户的media页面url

    def main(self):
        self.query_id_url = self.config['query_id_url'].format(self.get_mainjs())           #获取得到query_id以及相应query的operation_name的url，由上一步得到的
                                                                                            #main文件id组成
        self.query_id_headers = self.config['query_id_headers']                             #对应的headers
        self.operation_query = self.get_query_id()                                          #以"operation_name":"query_id"的字典形式返回得到的query_id
        #print(self.operation_query)
        self.media_headers = self.config['media_headers']                                   #这一步需要的是构造访问media页面的url和headers，可以得到每一条推文的id
        self.media_headers['Referer'] = self.TwitterMedia_listurl                           #headers里面的referer字段是空的，需要填入
        self.user_id_and_counts = self.get_user_id()                                        #访问需要用户的id而不是用户名，同时还需要获得推文数量
        #print(self.user_id_and_counts)                                                                      #需要访问的url格式如下https://twitter.com/i/api/graphql/{0}/{1}?variables={2}&features={3}
        if self.connect.get_id(self.user_id_and_counts[0])==None:
            self.connect.add_object(self.user_id_and_counts[0],'',self.user_name)
        self.last_media_id = self.connect.get_last_media_id(self.user_id_and_counts[0])
        self.media_variables =  self.config['UserMedia_variables']                          #获取填入将要访问url的variables变量已经features变量
        self.media_variables['userId'] = self.user_id_and_counts[0]
        #print(self.user_id_and_counts[1])
        self.media_variables['count'] = self.user_id_and_counts[1]
        self.temp_count = self.user_id_and_counts[1]
        self.media_features = self.config['UserMedia_features']
        #self.base_url = self.config['base_url'].format(self.operation_query['UserMedia'],'UserMedia',json.dumps(self.media_variables),json.dumps(self.media_features))
        
        self.all_medias_base_url = self.config['all_medias_base_url'].format(self.user_name)#https://twitter.com/{用户名}/status/{推文id}这是每一条推文的url格式
        self.all_media_id = self.get_medialist() 
        #print(self.all_media_id)
        if self.last_media_id!='': 
            print(self.all_media_id.index(self.last_media_id))                                                                                   #获取所有的media推文的id并构造相应的链接，得到一个列表
            self.all_media_id = self.all_media_id[:self.all_media_id.index(self.last_media_id)]
        #print(self.all_media_id)
        self.all_medias_url = [self.all_medias_base_url+i for i in self.all_media_id]       #这个列表里的链接无需访问，后面需要构造相应的获取相应推文图片资源url
                                                                                            #和headers，headers中的referer字段就是这个列表里面相应的推文url
        self.one_media_variables = self.config['one_media_variables']                       #这是获取每一条推文详细信息的url中所需的variables和features变量
        self.one_media_features = self.config['one_media_features']
        self.all_pic_query_url = self.construct_all_pic_query_url()                               #构造中所有的推文链接
        self.one_media_header = self.config['media_headers']
        self.all_pic_url = []
        self.get_all_pic_url()                                                 #获取里面的图片资源url
        self.download()
        
    def get_user_id(self):
        UserByScreenNamevariables = self.config['UserByScreenNamevariables']
        UserByScreenNamevariables["screen_name"] = self.user_name.lower()
        UserByScreenNamefeatures = self.config['UserByScreenNamefeatures']
        url = self.config['base_url'].format(self.operation_query['UserByScreenName'],'UserByScreenName',json.dumps(UserByScreenNamevariables),json.dumps(UserByScreenNamefeatures))
        response = requests.get(url, headers=self.media_headers)
        #print(response.text)
        if response.status_code == 200:
            res_dict = json.loads(response.text)
            return (res_dict['data']['user']['result']['rest_id'], res_dict['data']['user']['result']['legacy']['media_count'])
        
    def get_mainjs(self):
        try:
            response = requests.get(self.twitter_url, headers=self.twitter_headers)
            if response.status_code == 200:
                content = response.text
                res = re.match(".*?https://abs.twimg.com/responsive-web/client-web/main\.(.*?)\.js.*?",content,re.S)
                mainjs = res.groups()[0]
                return mainjs
        except:
            print("Get Mainjs Error")
    
    def get_query_id(self):
        try:
            response = requests.get(self.query_id_url, headers=self.query_id_headers)           
            if response.status_code == 200:
                content = response.text
                res = re.findall("e\.exports={queryId:\"(.*?)\",operationName:\"(.*?)\"", content, re.S)
                temp = dict()
                for i in res:
                    temp[i[1]] = i[0]
                return temp
            print(response.status_code)
        except:
            print("Get Query_id Error")

    def get_medialist(self,cursor=''):
        self.media_variables['cursor'] = cursor
        self.media_variables['count'] = self.temp_count+1
        url = self.config['base_url'].format(self.operation_query['UserMedia'],'UserMedia',json.dumps(self.media_variables),json.dumps(self.media_features))
        response = requests.get(url, headers=self.media_headers)
        #print(response.text)
        q = json.loads(response.text)
        entry_list = q['data']['user']['result']['timeline_v2']['timeline']['instructions'][0]['entries']
        latter_res = None
        if len(entry_list)-1 < self.temp_count:
            self.temp_count -= len(entry_list)-1
            latter_res = self.get_medialist(cursor=entry_list[-1]['content']['value'])
        if response.status_code == 200:
            res = re.findall("\"entryId\".*?\"rest_id\":\"(.*?)\"",response.text,re.S)

            if latter_res!=None:
                return res + latter_res
            else:
                return res

    def construct_all_pic_query_url(self):
        url_list = []
        for i in self.all_media_id:
            self.one_media_variables["focalTweetId"] = i
            temp_url = self.config['base_url'].format(self.operation_query['TweetDetail'],'TweetDetail',json.dumps(self.one_media_variables),json.dumps(self.one_media_features))
            url_list.append(temp_url)
        return url_list


    def get_all_pic_url(self):
        temp = []
        cnt = 1
        for index in trange(len(self.all_pic_query_url),desc=self.user_name+" extracting the image url",position=self.task_id):
            t = threading.Thread(target=self.get_pic_url,args=(index,))
            t.start()
            temp.append(t)
            if(cnt % 50==0):
                time.sleep(5)
            cnt += 1
        for i in temp:
            i.join()


    def get_pic_url(self,index):
        pattern = re.compile("\"media_url_https\":\"(https://pbs.twimg.com/media/(.*?))\.(png|jpg|jfif)\"",re.S)
        self.one_media_header['Referer'] = self.all_medias_url[index]
        response = requests.get(self.all_pic_query_url[index], headers=self.one_media_header)
        q = json.loads(response.text)
        if 'threaded_conversation_with_injections_v2' not in q['data']:
            with open('error_url_collector.txt','w+') as f:
                f.write(str(q)+'\n')
            os.system('pause')
        pic_entry = q['data']['threaded_conversation_with_injections_v2']['instructions'][0]['entries'][0]
        entry_list = str(pic_entry).replace(' ','').replace('\'','\"')
        res = pattern.findall(entry_list) #返回一个三元组('https://pbs.twimg.com/media/*******', '**********', 'jpg')
        res = list(set(res))
        #print(res)
        res = [(i[0]+twitter_crawler.image_save_pattern.format(i[2],'orig'),i[1]+'.'+i[2]) for i in res]
        if res!=[]:
            self.all_pic_url.extend(res)
            with open("pic_url_list.txt",'a+') as f:
                f.write(str(res))

    def download(self):
        if self.all_pic_url!=[]:
            bar = tqdm(self.all_pic_url,position=self.task_id)
            task_list = []
            for i in bar:
                bar.set_description("Trying to download image " + i[1])
                temp = threading.Thread(target=self.download_task,args=(i,))
                temp.start()
                task_list.append(temp)
            for t in task_list:
                t.join()
            self.connect.update(self.user_id_and_counts[0],self.all_media_id[0])
            self.connect.close()
    def download_task(self,i):
        if os.path.exists(self.path+i[1]):
            pass
        else:
            with open(self.path+i[1],'wb') as f:
                try:
                    #print("Trying to download image " + i[1])
                    res = requests.get(i[0],headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.47'})
                    if res.status_code == 200:
                        f.write(res.content)
                    time.sleep(2)
                except:
                    print("image " + id[1] + ' downloading failed')

def start(args):
    twitter_crawler(args[0],args[1],args[2]).main()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="image crawler in twitter user's media")
    parser.add_argument("--user",type=str,nargs='+')
    parser.add_argument('--maximum',default=50,action="store_const",const=200)
    parser.add_argument('-p',type=int,default=5)
    parser.add_argument('-t',type=int,default=10)
    parser.add_argument('-o','--output_file',type=str,default='d:/code/python_code/twitter')
    args = parser.parse_args(['--user','Rumoon_cocoa','--maximum'])

    user_name = args.user
    maximum_download = args.maximum
    process = args.p
    thread = args.t
    sem = threading.Semaphore(thread)
    output_file = args.output_file
    user_name = [(i,index,output_file) for index,i in enumerate(user_name)]
    pool = Pool(5)
    pool.map(start,user_name)

            
