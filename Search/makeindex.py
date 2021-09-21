from os import listdir
import jieba
import sqlite3
import os.path
import configparser
import math

# 文档类型，这里的文档类型，是一个文档对应n个Doc，即为每个文档-单词的连接对应一个Doc

class Doc:
    docid = 0
    tf = 0
    ld = 0
    # 两个分词指标
    def __init__(self, docid, tf, ld, tfidf):
        self.docid = docid
        self.tf = tf
        self.ld = ld
        self.tfidf = tfidf

    # 返回一个可以用来表示对象的可打印字符串
    def __repr__(self):
        return str(self.docid) +'\t'+str(self.tf) + '\t' + str(self.ld) +'\t' +str(self.tfidf)

    # __str__使用：被打印的时候需要以字符串的形式输出的时候，就会找到这个方法，并将返回值打印出来
    def __str__(self):
        return str(self.docid) +'\t' +str(self.tf) + '\t' + str(self.ld) + '\t' +str(self.tfidf)

class IndexModule:
    stop_words = set()
    postings_lists = {}
    i = 0
    config_path = ''
    config_encoding = ''
    all_vector=[]
    all_word = {}
    word_idf = {}

    def __init__(self):
        f = open('stop_words.txt', encoding='utf-8')
        words = f.read()
        self.stop_words = set(words.split('\n'))
        # 加载停用词进入集合

    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def calidf(self):
        config = configparser.ConfigParser()
        config.read('config.ini', 'utf-8')
        a = 'data'
        files = listdir(a)
        for k, i in enumerate(files):
            f = open(os.path.join(a, i), encoding='utf-8')
            lines = f.readlines()
            body = str()
            for line in lines:
                if line in ['\n', '\r\n']:
                    pass
                elif line.strip() == ' ':
                    pass
                else:
                    body = body + line
            try:
                seg_list = jieba.lcut(body, cut_all=False)
                # 拼接标题和文本后进行lcut，返回的是list
            except:
                print("Segmentationi Error.")
                print(body)
                continue

            ld, cleaned_dict = self.clean_list(seg_list)
            for key, value in cleaned_dict.items():
                if key not in self.word_idf:
                    self.word_idf[key] = 1
                else:
                    self.word_idf[key] = self.word_idf[key] + 1

    def clean_list(self, seg_list):
        cleaned_dict = {}
        n = 0
        for i in seg_list:
            i = i.strip().lower()
            # 去除词两边的空格，并变为小写
            if i != '' and not self.is_number(i) and i not in self.stop_words:
                n = n + 1
                if i in cleaned_dict:
                    cleaned_dict[i] = cleaned_dict[i] + 1
                else:
                    cleaned_dict[i] = 1
        # 记录有多少个不同的词n，及每个词的出现次数clean_dict[i].
        return n, cleaned_dict

    def write_postings_to_db(self, db_path):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        c.execute('''DROP TABLE IF EXISTS postings''')
        c.execute('''CREATE TABLE postings
                     (term TEXT PRIMARY KEY, df INTEGER, docs TEXT)''')

        for key, value in self.postings_lists.items():
            # 写入的是posting_list即每个词和所有引用了这个词的docid
            doc_list = '\n'.join(map(str, value[1]))
            t = (key, value[0], doc_list)
            c.execute("INSERT INTO postings VALUES (?, ?, ?)", t)

        conn.commit()
        conn.close()

    def construct_postings_lists(self):
        config = configparser.ConfigParser()
        config.read('config.ini', 'utf-8')
        a = 'data'
        files = listdir(a)
        AVG_L = 0
        for k,i in enumerate(files):
            f = open(os.path.join(a, i), encoding='utf-8')
            lines = f.readlines()
            h = i[0:-4]
            docid = int(h)
            body = str()
            for line in lines:
                if line in ['\n', '\r\n']:
                    pass
                elif line.strip() == ' ':
                    pass
                else:
                    body = body + line
            try:
                seg_list = jieba.lcut(body, cut_all=False)
                # 拼接标题和文本后进行lcut，返回的是list
            except:
                print("Segmentationi Error.")
                print(body)
                continue

            ld, cleaned_dict = self.clean_list(seg_list)
            # 对于一个文档的词list清洗

            AVG_L = AVG_L + ld
            # 这个文档有多少有用独特词
            my_vector = []
            this_all = 0
            for j in range(self.i):
                my_vector.append(0)
            for key,value in cleaned_dict.items():
                this_all = this_all +value
            for key, value in cleaned_dict.items():
                # [('a', 1), ('b', 2), ('c', 3)]
                # 把这个文档中的一个词放入Doc类中实例化。
                tfidf = value/this_all * math.log10(len(files)/int(self.word_idf[key]))
                d = Doc(docid,value,ld,tfidf)
                # posting是为整个index维持的一个字典，要记录所有的词的次数，以及这个词和所有连接它的文档的doc类的list
                if key in self.postings_lists:
                    self.postings_lists[key][0] = self.postings_lists[key][0] + 1  # df++
                    self.postings_lists[key][1].append(d)
                    my_vector[self.all_word[key]] = value/this_all
                else:
                    self.all_word[key] = self.i
                    self.i = self.i +1
                    self.postings_lists[key] = [1, [d]]  # [df, [Doc]]
                    my_vector.append(value/this_all)
            self.all_vector.append(my_vector)
        # 平均文档词长
        AVG_L = AVG_L / len(files)
        config.set('DEFAULT', 'N', str(len(files)))
        config.set('DEFAULT', 'avg_l', str(AVG_L))
        with open('config.ini', 'w', encoding='utf-8') as configfile:
            config.write(configfile)
        self.write_postings_to_db('data/ir.db')


if __name__ == "__main__":
    im = IndexModule()
    im.calidf()
    im.construct_postings_lists()

