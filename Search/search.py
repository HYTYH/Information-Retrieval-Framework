# -*- coding: utf-8 -*-
import argparse
import jieba
import math
import operator
import sqlite3
import configparser
import sys
import json
import os

parser = argparse.ArgumentParser()
parser.add_argument('--method', type=str, default="preVSM", help='the method to search')
parser.add_argument('--o', type=str, default="result.json", help='output dir')
parser.add_argument('--input',type=str,default="世界一流大学")
args = parser.parse_args()


class SearchEngine:
    stop_words = set()

    config_path = ''
    config_encoding = ''
    all_vector = []
    my_dict = {}
    K1 = 0
    B = 0
    N = 0


    conn = None

    def __init__(self):
        f = open('stop_words.txt', encoding='utf-8')
        words = f.read()
        self.stop_words = set(words.split('\n'))
        self.conn = sqlite3.connect('data/ir.db')
        self.K1 = float(1.5)
        self.B = float(0.75)
        config = configparser.ConfigParser()
        config.read('config.ini', 'utf-8')
        self.N = int(config['DEFAULT']['n'])
        self.AVG_L = float(config['DEFAULT']['avg_l'])

    def __del__(self):
        self.conn.close()

    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def clean_list(self, seg_list):
        cleaned_dict = {}
        n = 0
        for i in seg_list:
            i = i.strip().lower()
            if i != '' and not self.is_number(i) and i not in self.stop_words:
                n = n + 1
                if i in cleaned_dict:
                    cleaned_dict[i] = cleaned_dict[i] + 1
                else:
                    cleaned_dict[i] = 1
        return n, cleaned_dict

    def fetch_from_db(self, term):
        c = self.conn.cursor()
        c.execute('SELECT * FROM postings WHERE term=?', (term,))
        return (c.fetchone())

    def fetch_item_from_db(self, term):
        c = self.conn.cursor()
        term += '%'
        c.execute("SELECT term FROM postings WHERE term like ? ORDER BY df DESC LIMIT 10", (term,))
        return (c.fetchall())

    def result_by_VSM(self,sentence):
        seg_list = jieba.lcut(sentence,cut_all = False)
        #print(seg_list)
        n,cleaned_dict = self.clean_list(seg_list)
        mid_score = {}
        my_tf_idf= {}
        my_all = 0
        for key,value in cleaned_dict.items():
            my_all = my_all + value
        for key,value in cleaned_dict.items():
            my_tf_idf[key] = value/my_all
        for term in cleaned_dict.keys():
            r = self.fetch_from_db(term)
            if r is None:
                continue
            df = r[1]
            docs = r[2].split('\n')
            for doc in docs:
                docid, tf, ld, tfidf = doc.strip().split('\t')
                docid = int(docid)
                tfidf = float(tfidf)
                if docid in mid_score:
                    mid_score[docid] = mid_score[docid] + tfidf * my_tf_idf[term]
                else:
                    mid_score[docid] = tfidf * my_tf_idf[term]
        f = zip(mid_score.keys(), mid_score.values())
        c = sorted(f,key=operator.itemgetter(1),reverse=True)
        return c

    def result_by_preVSM(self,sentence):
        seg_list = jieba.lcut(sentence, cut_all=False)
        #print(seg_list)
        n, cleaned_dict = self.clean_list(seg_list)
        mid_score = {}
        for term in cleaned_dict.keys():
            r = self.fetch_from_db(term)
            if r is None:
                continue
            df = r[1]
            docs = r[2].split('\n')
            for doc in docs:
                docid, tf, ld, tfidf = doc.strip().split('\t')
                docid = int(docid)
                if docid in mid_score:
                    mid_score[docid] = mid_score[docid] + 1
                else:
                    mid_score[docid] = 1
        f = zip(mid_score.keys(), mid_score.values())
        c = sorted(f, key=operator.itemgetter(1), reverse=True)
        return c

    def result_by_BM25(self, sentence):
        seg_list = jieba.lcut(sentence, cut_all=False)
        n, cleaned_dict = self.clean_list(seg_list)
        BM25_scores = {}
        for term in cleaned_dict.keys():
            r = self.fetch_from_db(term)
            if r is None:
                continue
            df = r[1]
            w = math.log2((self.N - df + 0.5) / (df + 0.5))
            docs = r[2].split('\n')
            for doc in docs:
                docid,tf,ld,tfidf= doc.strip().split('\t')
                docid = int(docid)
                tf = int(tf)
                ld = int(ld)
                s = (self.K1 * tf * w) / (tf + self.K1 * (1 - self.B + self.B * ld / self.AVG_L))
                if docid in BM25_scores:
                    BM25_scores[docid] = BM25_scores[docid] + s
                else:
                    BM25_scores[docid] = s
        BM25_scores = sorted(BM25_scores.items(), key=operator.itemgetter(1))
        BM25_scores.reverse()
        return BM25_scores
        # if len(BM25_scores) == 0:
        #    return 0, [], cleaned_dict
        # else:
        #    return 1, BM25_scores, cleaned_dict

    def process_bool(self, seg_list):
        if 'OR' in seg_list:
            return 'OR'
        elif 'AND' in seg_list:
            return 'AND'
        else:
            return False

    def intersection(self, doc1, doc2):
        doc = [val for val in doc1 if val in doc2]
        return doc

    def unionset(self, doc1, doc2):
        return list(doc1.union(doc2))

    def clean(self, clean_list):
        final_list = {}
        for term in clean_list.keys():
            if term.lower() != 'or' and term.lower() != 'and':
                final_list[term] = clean_list[term]
        return final_list

    def result_by_bool(self, sentence):
        seg_list = jieba.lcut(sentence, cut_all=False)
        n, cleaned_dict = self.clean_list(seg_list)
        Bool_results = {}
        docidres = []
        i = 0
        for term in cleaned_dict.keys():
            r = self.fetch_from_db(term)
            if r is None:
                continue
            docs = r[2].split('\n')
            nowdoc = []
            for doc in docs:
                docid, tf, ld, tfidf = doc.split('\t')
                nowdoc.append(docid)
            if i == 0:
                docidres = nowdoc
            else:
                docidres = self.intersection(docidres,nowdoc)
            i = i + 1
        for line in docidres:
            Bool_results[line] = 1
        Bool_results = sorted(Bool_results.items(), key=operator.itemgetter(1))
        return Bool_results


def printInfo(mylist,sentence):
    seg_list = jieba.lcut(sentence, cut_all=False)
    h = 'data'
    res = dict()
    for item in mylist:
        a = item[0]
        res[a] = []
        print(a)
        f = open(os.path.join(h, str(a)+'.txt'),encoding='utf-8')
        lines = f.readlines()
        body = str()
        for line in lines:
            if line in ['\n', '\r\n']:
                pass
            elif line.strip() == ' ':
                pass
            else:
                body = body + line
        body1 = jieba.lcut(body, cut_all=False)
        bodyu = ""
        for term in body1:
            if term in seg_list:
                term = "{***"+term+"***}"
            bodyu = bodyu + term
        print(bodyu)

if __name__ == "__main__":

    sentence = args.input
    method = args.method
    outputdir = args.o
    ir = SearchEngine()
    print("检索中:")
    
    if method == "VSM":
        mylist = ir.result_by_VSM(sentence)
    elif method == "preVSM":
        mylist = ir.result_by_preVSM(sentence)
    elif method == "Bool":
        mylist = ir.result_by_bool(sentence)
    elif method == "BM25":
        mylist = ir.result_by_BM25(sentence)
    else:
        print("method error")
        sys.exit()
    
    result = [{"resultID":item[0],"Accuracy":item[1]}for item in mylist]
    
    all_vsm = ir.result_by_VSM(sentence)
    all_pre = ir.result_by_preVSM(sentence)
    all_bool = ir.result_by_bool(sentence)
    all_bm25 = ir.result_by_BM25(sentence)
    print("\n匹配结果:")
    printInfo(mylist,sentence)
    
    all_id = []
    print("\n统计中:")
    for item in all_vsm:
        all_id.append(str(item[0]))
    for item in all_pre:
        all_id.append(str(item[0]))
    for item in all_bool:
        all_id.append(str(item[0]))
    for item in all_bm25:
        all_id.append(str(item[0]))
    all_id_set = set(all_id)
    result_set = set([item['resultID'] for item in result])
    
    
    print(f"Recall : {100.0*len(result_set)/len(all_id_set)} %")
    
    
    if outputdir == "":
        print(result)
    else:
        with open(outputdir, "w") as fp:
            fp.write(json.dumps(result, indent=4))


