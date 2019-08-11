import argparse
import os
import time
import re
import requests

import numpy as np
import pandas as pd
from pandas.io.json import json_normalize

import janome
from janome import analyzer
from janome.charfilter import *
from janome.tokenfilter import *
from janome.tokenizer import Tokenizer

from urllib import request 

from tqdm import tqdm


"""
## Usage
python qiita-api.py -auth_token <your_qiita_api_auth_token> -data_dir ./ -start_date 2019-01-01 -end_date 2019-02-01

## Coding reference
* Qiita API
https://qiita.com/pocket_kyoto/items/64a5ae16f02023df883e

* Tokenize
http://tdual.hatenablog.com/entry/2018/04/09/133000
https://ohke.hateblo.jp/entry/2017/11/02/230000

"""


class NumericReplaceFilter(TokenFilter):
    def apply(self, tokens):
        for token in tokens:
            parts = token.part_of_speech.split(',')
            if (parts[0] == '名詞' and parts[1] == '数'):
                token.surface = '0'
                token.base_form = '0'
                token.reading = 'ゼロ'
                token.phonetic = 'ゼロ'
            yield token

class Tokenizer_ntm:
    def __init__(self, stopwords, parser=None, include_pos=None, exclude_posdetail=None, exclude_reg=None):
    
        self.stopwords = stopwords
        self.include_pos = include_pos if include_pos else  ["名詞", "動詞", "形容詞"]
        self.exclude_posdetail = exclude_posdetail if exclude_posdetail else ["接尾", "数", "サ変接続"]
        self.exclude_reg = exclude_reg if exclude_reg else r"$^"  # no matching reg
        
        self.char_filters = [
                        UnicodeNormalizeCharFilter(), 
                        RegexReplaceCharFilter(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+", u''), #url
                        RegexReplaceCharFilter(r"\"?([-a-zA-Z0-9.`?{}]+\.jp)\"?", u''), #*.jp
                        RegexReplaceCharFilter(self.exclude_reg, u'')
                       ]
        
        self.token_filters = [
                         NumericReplaceFilter(),
                         POSKeepFilter(self.include_pos),
                         LowerCaseFilter()
                        ]
        
        self.analyzer = analyzer.Analyzer(self.char_filters, Tokenizer(), self.token_filters)
        
        
    def tokenize(self, text):

        tokens = self.analyzer.analyze(text)
        res = []
        for token in tokens:
            if token.base_form not in self.stopwords and token.part_of_speech.split(',')[1] not in self.exclude_posdetail:
                res.append(token.base_form)
                
        return res

class Tokenizer_txt:
    def __init__(self, exclude_posdetail=None, exclude_reg=None):
    
        self.exclude_posdetail = exclude_posdetail if exclude_posdetail else ["接尾", "サ変接続", "空白"]
        self.exclude_reg = exclude_reg if exclude_reg else r"$^"  # no matching reg
        
        self.char_filters = [
                        UnicodeNormalizeCharFilter(), 
                        RegexReplaceCharFilter(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+", u''), #url
                        RegexReplaceCharFilter(r"\"?([-a-zA-Z0-9.`?{}]+\.jp)\"?", u''), #*.jp
                        RegexReplaceCharFilter(self.exclude_reg, u'')
                       ]
        
        self.token_filters = [
                         NumericReplaceFilter(),
                         LowerCaseFilter()
                        ]
        
        self.analyzer = analyzer.Analyzer(self.char_filters, Tokenizer(), self.token_filters)
        
        
    def tokenize(self, text):

        tokens = self.analyzer.analyze(text)
        res = []
        
        for token in tokens:
            if token.part_of_speech.split(',')[1] not in self.exclude_posdetail:
                res.append(token.surface)
                
        return res

def get_simple_df(df):
    df['tags_str'] = df['tags'].apply(lambda tags: ','.join(tag['name'] for tag in tags))
    return df

def get_qiita_articles(opt):
    url = 'https://qiita.com/api/v2/items'
    h = {'Authorization': 'Bearer {}'.format(opt.auth_token)}
    sleep_sec = 3.6 

    date_list = [d.strftime('%Y-%m-%d') for d in pd.date_range(opt.start_date, opt.end_date)]
    start_list = date_list[:-2]
    end_list = date_list[2:]

    df_list = []

    for start, end in zip(start_list, end_list):
        
        p = {
            "page" : 1,
            'per_page': 100,
            'query': 'created:>{} created:<{}'.format(start, end)
        }

        print("date %s : page 1" % start)
        
        time.sleep(sleep_sec)
        
        r = requests.get(url, params=p, headers=h)
        total_count = int(r.headers['Total-Count'])

        if total_count == 0:
            print("No articles")
            continue
        
        print("Total article :", total_count)
        df_list.append(get_simple_df(json_normalize(r.json())))
        
        
        if total_count > 100:
            for i in range(2, (total_count - 1) // 100 + 2):
                p['page'] = i
                print("date %s : page %s" % (start, i))
                time.sleep(sleep_sec) 
                
                r = requests.get(url, params=p, headers=h)
                
                df_list.append(get_simple_df(json_normalize(r.json())))

    data = pd.concat(df_list, ignore_index=True)

    return data



def get_stopwords():
    res = request.urlopen("http://svn.sourceforge.jp/svnroot/slothlib/CSharp/Version1/SlothLib/NLP/Filter/StopWord/word/Japanese.txt")
    stopwords = [line.decode("utf-8").strip() for line in res]
    res = request.urlopen("http://svn.sourceforge.jp/svnroot/slothlib/CSharp/Version1/SlothLib/NLP/Filter/StopWord/word/English.txt")
    stopwords += [line.decode("utf-8").strip() for line in res]
    stopwords += ['*', '&', '[', ']', ')', '(', '-',':','.','/','0', '...?', '——', '!【', '"', ')、', ')。', ')」']

    return stopwords


def main(opt):

    data = get_qiita_articles(opt)

    # filter. To keep quality, likes_count >=1
    mask = (data['likes_count'] >= 1)


    # downloading stopwords.
    stopwords = get_stopwords()
    
    t_ntm = Tokenizer_ntm(stopwords=stopwords)
    t_txt = Tokenizer_txt()

    # Wakachigaki, Separating words, needs spesific tokenizer like janome and mecab.
    bow = []
    text = []
    target = []
    for (_, i) in tqdm(data[mask].iterrows(), total = len(data[mask])):
        bow.append(t_ntm.tokenize(i.body))
        text.append(t_txt.tokenize(i.body))
        target.append(i.tags_str.lower().split(','))

    # save articles
    pd.to_pickle(bow, opt.data_dir + 'bow.pkl')
    pd.to_pickle(text, opt.data_dir + 'text.pkl')
    pd.to_pickle(target, opt.data_dir + 'target.pkl')
    
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='qiita-api.py')
    
    parser.add_argument('-auth_token', help='Qiita API AUTH TOKEN', required=True) 
    parser.add_argument('-data_dir', help='Directory for data save', required=True)
    parser.add_argument('-start_date', required=True) 
    parser.add_argument('-end_date', required=True) 
    
    opt = parser.parse_args()
    
    if not os.path.exists(opt.data_dir):
        os.mkdir(opt.data_dir)

    main(opt)