# -*- coding: utf-8 -*-
import pycurl
import os
import io
import json
import sys
import numpy as np
from pulp import *

class GROOVE_LPSOLVE():
    def __init__(self,login_id,passwd):
        self.curl_timeout = 6
        self.curl_agent = 'Mozilla/5.0'

        #for prepare_cookie
        self.login_url = 'https://mypage.groovecoaster.jp/sp/login/auth_con.php'
        self.music_list_url = 'https://mypage.groovecoaster.jp/sp/json/music_list.php'
        self.login_id = str(login_id)
        self.passwd = str(passwd)
        # !このスクリプトがある場所にcookieを作成!
        self.cookie_url = os.path.abspath(os.path.dirname(__file__)) + '/' + self.login_id + '_cookie.txt'

        #for update_music_id_list
        self.ID_LIST = []

        #for get_score_list
        self.score_list_name = 'score_list.csv'
        self.total = 0
        self.music_id_list = []
        self.score_lack = []
        self.difficult_weight = []

        #for music _dict
        self.music_dict = {}

    def prepare_cookie(self):
        b = io.BytesIO()
        curl = pycurl.Curl()
        curl.setopt(pycurl.URL,self.login_url)
        curl.setopt(pycurl.TIMEOUT,self.curl_timeout)
        curl.setopt(pycurl.USERAGENT,self.curl_agent)
        curl.setopt(pycurl.WRITEFUNCTION, b.write)
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.HTTPPOST, [('nesicaCardId', self.login_id), ('password', self.passwd)])
        curl.setopt(pycurl.COOKIEJAR,self.cookie_url)

        try:
            curl.perform()
            http_code = curl.getinfo(pycurl.HTTP_CODE)
            if http_code == 200:
                retval = 'OK'
            else:
                retval = str(http_code)
        except Exception as e:
            retval = str(e)

    def update_music_id_list(self):
        b = io.BytesIO()
        curl = pycurl.Curl()
        curl.setopt(pycurl.URL,self.music_list_url)
        curl.setopt(pycurl.TIMEOUT,self.curl_timeout)
        curl.setopt(pycurl.USERAGENT,self.curl_agent)
        curl.setopt(pycurl.WRITEFUNCTION, b.write)
        curl.setopt(pycurl.COOKIEFILE,self.cookie_url)

        try:
            curl.perform()
            http_code = curl.getinfo(pycurl.HTTP_CODE)
            if http_code == 200:
                retval = b.getvalue()
            else:
                retval = str(http_code)
                print retval
                return 0
        except Exception as e:
            retval = str(e)
            print retval
            return 0

        decode_retval = json.loads(retval)

        l = open('id_list.txt','w')
        for i in range(len(decode_retval['music_list'])):
            self.ID_LIST.append(decode_retval['music_list'][i]['music_id'])
            l.write(str(decode_retval['music_list'][i]['music_id'])+ '\t' + decode_retval['music_list'][i]['music_title'].encode('utf_8')  + '\n')
        l.close()

    def get_total_score(self):
        # GET player total score
        url = 'https://mypage.groovecoaster.jp/sp/json/player_data.php'
        b = io.BytesIO()
        curl = pycurl.Curl()
        curl.setopt(pycurl.URL,url)
        curl.setopt(pycurl.TIMEOUT,self.curl_timeout)
        curl.setopt(pycurl.USERAGENT,self.curl_agent)
        curl.setopt(pycurl.WRITEFUNCTION, b.write)
        curl.setopt(pycurl.COOKIEFILE,self.cookie_url)

        try:
            curl.perform()
            http_code = curl.getinfo(pycurl.HTTP_CODE)
            if http_code == 200:
                retval = b.getvalue()
            else:
                print '!error! HTTP Status %d'%http_code
                return 0

        except Exception as e:
            retval = str(e)
            print '!error! Cannot access to the player data'
            print retval
            return 0

        decode_ret = json.loads(retval)
        self.total = int(decode_ret['player_data']['total_score'])
        # GET player total score ~~ end

    def get_score_list(self):
        # 先にupdate_music_id_list()を実行すること(ID_LISTの準備)
        p = open(self.score_list_name,'w')

        for one_id in self.ID_LIST:
            url = 'https://mypage.groovecoaster.jp/sp/json/music_detail.php?music_id=' + str(one_id)
            b = io.BytesIO()
            curl = pycurl.Curl()
            curl.setopt(pycurl.URL,url)
            curl.setopt(pycurl.TIMEOUT,self.curl_timeout)
            curl.setopt(pycurl.USERAGENT,self.curl_agent)
            curl.setopt(pycurl.WRITEFUNCTION, b.write)
            curl.setopt(pycurl.COOKIEFILE,self.cookie_url)

            try:
                curl.perform()
                http_code = curl.getinfo(pycurl.HTTP_CODE)
                if http_code == 200:
                    retval = b.getvalue()
                else:
                    print '!error! HTTP Status %d'%http_code
                    return str(http_code)
            except Exception as e:
                retval = str(e)
                print '!error! Cannot access to the music data(ID:%d)'%one_id
                print retval
                return retval

            # 取得したjson<str> を保存
            p.write(retval + '\n')

            # jsonを読み込む、self.score_lack, music_id_list, difficult_weight に対応する値格納
            self.read_music_data_json(retval)
        p.close()

    def import_file(self):
        f = open(self.score_list_name,'r')
        for line in f:
            line = line.rstrip()
            self.read_music_data_json(line)
        f.close()

    def read_music_data_json(self,json_str):
        decode_ret = json.loads(json_str)
        difficult_list = ['simple_result_data','normal_result_data','hard_result_data','extra_result_data']
        if decode_ret['music_detail']['ex_flag'] == 1:
            cycle = 4
        else:
            cycle = 3

        one_id = int(decode_ret['music_detail']['music_id'])

        for difficult in range(cycle):
            if decode_ret['music_detail'][difficult_list[difficult]]:
                score = decode_ret['music_detail'][difficult_list[difficult]]['score']

                if score == 1000000:
                    continue
                else:
                    self.score_lack.append(1000000-score)
                    self.music_id_list.append(one_id)
                    self.difficult_weight.append((1+difficult)*(1+difficult))
            else:

                self.score_lack.append(1000000)
                self.music_id_list.append(one_id)
                self.difficult_weight.append((1+difficult)*(1+difficult))

    def prepare_dictionary(self):
        # 先にupdate_music_id_list()を実行すること(id_list.txtの準備)
        f = open('id_list.txt','r')
        for line in f:
            ID,MUSIC_NAME = line.split('\t')
            self.music_dict[ID] = MUSIC_NAME[:-1]

    def solve_LP(self,aim):
        # 先に get_score_list(), get_total_score(), prepare_dictionary()を実行後に実行すること
        diff = aim - self.total
        if diff <= 0:
            print u'現在の得点より高い目標点を設定してください'
            sys.exit()

        lp = LpProblem()
        x = [LpVariable('x_%d_%d'%(ID,i),0,1,'Binary') for ID,i in zip(self.music_id_list,self.difficult_weight)]
        lp += lpDot(self.difficult_weight,x)
        lp += lpDot(self.score_lack,x) <= diff
        lp += lpDot(self.score_lack,x) >= diff
        statue = lp.solve()
        ans = value(lp.objective)

        print '~~ Result ~~'
        if ans == int(ans):
            ans_list = ([ str(x[i]) for i in range(len(self.score_lack)) if value(x[i])==1.0])
            for music in ans_list:
                trash,ID,difficult = music.split('_')

                if int(difficult) == 1:
                    DIFF = 'simple'
                if int(difficult) == 4:
                    DIFF = 'normal'
                if int(difficult) == 9:
                    DIFF = 'hard'
                if int(difficult) == 16:
                    DIFF = 'extreme'
                print '%s\t%s'%(self.music_dict[ID],DIFF)
        else:
            print u'目標点にピッタリ合う組み合わせがありません'

    def check_cookie(self):
        if os.path.exists(self.cookie_url):
            return True
        else:
            return False

    def delete_cookie(self):
        os.system('rm ' + self.cookie_url)
