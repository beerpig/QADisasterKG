import os
import ahocorasick
import jieba
import numpy as np
import joblib
# from sklearn.externals import joblib


class EntityExtractor:
    def __init__(self):
        cur_dir = '/'.join(os.path.abspath(__file__).split('/')[:-1])
        # 路径
        self.vocab_path = os.path.join(cur_dir, 'data/vocab.txt')
        self.stopwords_path = os.path.join(cur_dir, 'data/stop_words.utf8')
        self.word2vec_path = os.path.join(cur_dir, 'data/merge_sgns_bigram_char300.txt')
        # self.same_words_path = os.path.join(cur_dir, 'DATA/同义词林.txt')
        self.stopwords = [w.strip() for w in open(self.stopwords_path, 'r', encoding='utf8') if w.strip()]

        # 意图分类模型文件
        # self.tfidf_path = os.path.join(cur_dir, 'model/tfidf_model.m')
        # self.nb_path = os.path.join(cur_dir, 'model/intent_reg_model.m')  # 朴素贝叶斯模型
        # self.tfidf_model = joblib.load(self.tfidf_path)
        # self.nb_model = joblib.load(self.nb_path)

        self.disaster_path = os.path.join(cur_dir, 'data/disaster_vocab.txt')
        self.warning_signal_path = os.path.join(cur_dir, 'data/warning_signal_vocab.txt')
        self.sub_warning_signal_path = os.path.join(cur_dir, 'data/sub_warning_signal_vocab.txt')
        self.trigger_entities_path = os.path.join(cur_dir, 'data/trigger_entities.txt')

        self.disaster_entities = [w.strip() for w in open(self.disaster_path, encoding='utf8') if w.strip()]
        self.warning_signal_entities = [w.strip() for w in open(self.warning_signal_path, encoding='utf8') if w.strip()]
        self.sub_warning_signals_entities = [w.strip() for w in open(self.sub_warning_signal_path, encoding='utf8') if
                                             w.strip()]
        self.trigger_entities = [w.strip() for w in open(self.trigger_entities_path, encoding='utf8') if w.strip()]

        self.region_words = list(set(self.disaster_entities + self.warning_signal_entities))

        # 构造领域actree？
        self.disaster_tree = self.build_actree(list(set(self.disaster_entities)))
        self.warning_signal_tree = self.build_actree(list(set(self.warning_signal_entities)))
        self.sub_warning_signal_tree = self.build_actree(list(set(self.sub_warning_signals_entities)))
        self.trigger_entities_tree = self.build_actree(list(set(self.trigger_entities)))

        # self.disaster_qwds = ['什么灾害', '是哪种灾害', '怎么回事', '什么情况']
        # self.warning_signal_qwds = ['预警信号', '预警', '什么预警', '什么预警信号']
        self.desc_qwds = ['是什么']
        self.ekp_qwds = ['怎么办', '注意什么', '防御', '措施', '应急', '策略', '注意', '注意哪些']
        self.sub_warning_signals_qwds = ['有哪些预警', '有哪些信号', '预警有哪些', '信号有哪些']
        self.trigger_qwds = ['是什么预警', '是什么信号']

    def build_actree(self, wordlist):
        """
        构造actree，加速过滤
        :param wordlist:
        :return:
        """
        actree = ahocorasick.Automaton()
        # 向树中添加单词
        for index, word in enumerate(wordlist):
            actree.add_word(word, (index, word))
        actree.make_automaton()
        return actree

    def entity_reg(self, question):
        """
        模式匹配，得到匹配的词和类型。如气象灾害，预警信号
        :param question: str
        :return:
        """
        self.result = {}

        for i in self.disaster_tree.iter(question):
            word = i[1][1]
            if "Disaster" not in self.result:
                self.result["Disaster"] = [word]
            else:
                self.result["Disaster"].append(word)

        for i in self.warning_signal_tree.iter(question):
            word = i[1][1]
            if "warning_signal" not in self.result:
                self.result["warning_signal"] = [word]
            else:
                self.result["warning_signal"].append(word)

        for i in self.sub_warning_signal_tree.iter(question):
            word = i[1][1]
            if "sub_warning_signal" not in self.result:
                self.result["sub_warning_signal"] = [word]
            else:
                self.result["sub_warning_signal"].append(word)

        for i in self.trigger_entities_tree.iter(question):
            word = i[1][1]
            if "trigger_entities" not in self.result:
                self.result["trigger_entities"] = [word]
            else:
                self.result["trigger_entities"].append(word)

        return self.result

    def find_sim_words(self, question):
        """
        当全匹配失败时，就采用相似度计算俩照相似的词
        :param question:
        :return:
        """
        import re
        import string
        from gensim.models import KeyedVectors, Word2Vec

        jieba.load_userdict(self.vocab_path)
        self.model = KeyedVectors.load_word2vec_format(self.word2vec_path, binary=False)
        sentence = re.sub("[{}]", re.escape(string.punctuation), question)
        sentence = re.sub("[，。‘’；：？、！【】]", " ", sentence)
        sentence = sentence.strip()

        words = [w.strip() for w in jieba.cut(sentence) if w.strip() not in self.stopwords and len(w.strip()) >= 2]

        alist = []

        for word in words:
            temp = [self.disaster_entities, self.warning_signal_entities]
            for i in range(len(temp)):
                flag = ""
                if i == 0:
                    flag = "Disaster"
                elif i == 1:
                    flag = "warning_signal"
                elif i == 2:
                    flag = "sub_warning_signal"
                scores = self.simCal(word, temp[i], flag)
                alist.extend(scores)
        temp1 = sorted(alist, key=lambda k: k[1], reverse=True)
        if temp1:
            self.result[temp1[0][2]] = [temp1[0][0]]

    def editDistanceDP(self, s1, s2):
        """
        采用DP方法计算编辑距离
        :param s1:
        :param s2:
        :return:
        """
        m = len(s1)
        n = len(s2)
        solution = [[0 for j in range(n + 1)] for i in range(m + 1)]
        for i in range(len(s2) + 1):
            solution[0][i] = i
        for i in range(len(s1) + 1):
            solution[i][0] = i

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i - 1] == s2[j - 1]:
                    solution[i][j] = solution[i - 1][j - 1]
                else:
                    solution[i][j] = 1 + min(solution[i][j - 1], min(solution[i - 1][j],
                                                                     solution[i - 1][j - 1]))
        return solution[m][n]

    def simCal(self, word, entities, flag):
        """
        计算词语和字典中的词的相似度
        相同字符的个数/min(|A|,|B|)   +  余弦相似度
        :param word: str
        :param entities:List
        :return:
        """
        a = len(word)
        scores = []
        for entity in entities:
            sim_num = 0
            b = len(entity)
            c = len(set(entity + word))
            temp = []
            for w in word:
                if w in entity:
                    sim_num += 1
            if sim_num != 0:
                score1 = sim_num / c  # overlap score
                temp.append(score1)
            try:
                score2 = self.model.similarity(word, entity)  # 余弦相似度分数
                temp.append(score2)
            except:
                pass
            score3 = 1 - self.editDistanceDP(word, entity) / (a + b)  # 编辑距离分数
            if score3:
                temp.append(score3)

            score = sum(temp) / len(temp)
            if score >= 0.7:
                scores.append((entity, score, flag))

        scores.sort(key=lambda k: k[1], reverse=True)
        return scores

    def check_words(self, wds, sent):
        """
        基于特征词分类
        :param wds:
        :param sent:
        :return:
        """
        for wd in wds:
            if wd in sent:
                return True
        return False

    def tfidf_features(self, text, vectorizer):
        """
        提取问题的TF-IDF特征
        :param text:
        :param vectorizer:
        :return:
        """
        jieba.load_userdict(self.vocab_path)
        words = [w.strip() for w in jieba.cut(text) if w.strip() and w.strip() not in self.stopwords]
        sents = [' '.join(words)]

        tfidf = vectorizer.transform(sents).toarray()
        return tfidf

    def other_features(self, text):
        """
        提取问题的关键词特征
        :param text:
        :return:
        """
        features = [0] * 3
        # for d in self.disaster_qwds:
        #     if d in text:
        #         features[0] += 1
        #
        # for s in self.warning_signal_qwds:
        #     if s in text:
        #         features[1] += 1

        for c in self.desc_qwds:
            if c in text:
                features[2] += 1

        m = max(features)
        n = min(features)
        normed_features = []
        if m == n:
            normed_features = features
        else:
            for i in features:
                j = (i - n) / (m - n)
                normed_features.append(j)

        return np.array(normed_features)

    def model_predict(self, x, model):
        """
        预测意图
        :param x:
        :param model:
        :return:
        """
        pred = model.predict(x)
        return pred

    # 实体抽取主函数
    def extractor(self, question):
        self.entity_reg(question)
        if not self.result:
            self.find_sim_words(question)

        types = []  # 实体类型
        for v in self.result.keys():
            types.append(v)

        intentions = []  # 查询意图

        # 意图预测
        # tfidf_feature = self.tfidf_features(question, self.tfidf_model)
        #
        # other_feature = self.other_features(question)
        # m = other_feature.shape
        # other_feature = np.reshape(other_feature, (1, m[0]))
        #
        # feature = np.concatenate((tfidf_feature, other_feature), axis=1)
        #
        # predicted = self.model_predict(feature, self.nb_model)
        # intentions.append(predicted[0])

        # 已知triggerEntities，查询预警信号
        if self.check_words(self.trigger_qwds, question) and ('trigger_entities' in types):
            intention = "query_trigger_signal"
            if intention not in intentions:
                intentions.append(intention)

        # 已知灾害，查询预警信号
        elif self.check_words(self.sub_warning_signals_qwds, question) and ('Disaster' in types):
            intention = "query_warning_signal"
            if intention not in intentions:
                intentions.append(intention)

        # 已知灾害，查询灾害描述
        elif self.check_words(self.desc_qwds, question) and ('Disaster' in types):
            intention = "query_desc"
            if intention not in intentions:
                intentions.append(intention)

        # 已知灾害，查询防御策略
        elif self.check_words(self.ekp_qwds, question) and ('Disaster' in types):
            intention = "query_ekp"
            if intention not in intentions:
                intentions.append(intention)

        # 已知预警信号，查询预警信号描述
        elif self.check_words(self.desc_qwds, question) and ('sub_warning_signal' in types):
            intention = "query_desc"
            if intention not in intentions:
                intentions.append(intention)

        # 已知预警信号，查询预警信号防御策略
        elif self.check_words(self.ekp_qwds, question) and ('sub_warning_signal' in types):
            intention = "query_ekp"
            if intention not in intentions:
                intentions.append(intention)

        # 若没有识别出实体或意图则调用其它方法
        elif not intentions or not types:
            intention = "QA_matching"
            if intention not in intentions:
                intentions.append(intention)

        self.result["intentions"] = intentions

        return self.result
