#!/usr/bin/python
# -*- coding: utf-8 -*-

import subprocess
import sys
import traceback
import socket
from xml.etree.ElementTree import fromstring
from datetime import datetime

# Juliusサーバ
JULIUS_HOST = "localhost"
JULIUS_PORT = 10500
system_status = 0

# juliusの解析結果のXMLをパース
def parse_recogout(xml_data):
    # scoreを取得(どれだけ入力音声が、認識結果と合致しているか)
    shypo = xml_data.find(".//SHYPO")
    if shypo is not None:
        score = shypo.get("SCORE")
    
        # 認識結果の単語を取得
        whypo = xml_data.find(".//WHYPO")
        if whypo is not None:
            word = whypo.get("WORD")
            return score, word

def word_extracter(recv_data):
    for line in recv_data.split('\n'):
        index = line.find('WORD="')
        if index!=-1:
            line = line[index+6:line.find('"',index+6)]
            if(line!='<s>' and line!='</s>'):
                yield line
                                        
if __name__ == "__main__":
        
    try:
        # TCP/IPでjuliusに接続
        bufsize = 4096
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((JULIUS_HOST, JULIUS_PORT))
        sock_file = sock.makefile()
                    
        while True:
            # juliusから解析結果を取得
            data = sock.recv(bufsize)
            word = unicode("".join(word_extracter(data)), 'utf-8')
            
            if u'おはよう鍋太郎' in word:
                subprocess.Popen("jsay おはようございます", shell=True)
                system_status = 1
            elif u'おやすみ鍋太郎' in word:
                subprocess.call("jsay おやすみなさい", shell=True)
                system_status = 0
            elif u'かわいいね' in word or u'かしこいね' in word:
                subprocess.call("jsay あなたもね", shell=True)
            elif u'君の名は' in word or u'あなたの名前は' in word:
                subprocess.call("jsay なべたろうです", shell=True)
            elif u'早口言葉' in word:
                subprocess.call("jsay 右耳の二ミリ右にミニ右耳", shell=True)
            elif u'さようなら' in word:
                subprocess.call("jsay 一人にしないでください", shell=True)
            elif u'ありがとう' in word:
                subprocess.call("jsay どういたしまして", shell=True)
            elif system_status == 1 and u'冷蔵庫点けて' in word:
                subprocess.call("jsay 冷蔵庫の電源を入れます", shell=True)
            elif system_status == 1 and u'冷蔵庫消して' in word:
                subprocess.call("jsay 冷蔵庫の電源を消します", shell=True)
                                   
    except Exception as e:
        print "error occurred", e, traceback.format_exc()
    finally:
        pass
