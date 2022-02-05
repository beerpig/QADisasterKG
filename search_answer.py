from py2neo import Graph
from tqdm import tqdm


class AnswerSearching:
    def __init__(self):
        self.graph = Graph("http://localhost:7474", auth=("neo4j", "beerpig"))
        self.top_num = 5

    def question_parser(self, data):
        """
        根据不同实体和意图构造cypher查询语句
        :param data: {"disaster":[], "warning_signal":[]}
        :return:
        """
        sqls = []
        if data:
            for intent in data["intentions"]:
                sql_ = {}
                sql_["intention"] = intent
                sql = []
                if intent == 'query_standard':
                    sql = self.transfor_to_sql4query_standard(data['question_split'], intent)
                    sql_["label"] = "standard_split"
                    sql_["data"] = data['question_split']
                else:
                    if data.get("sub_warning_signal"):
                        sql = self.transfor_to_sql("sub_signal", data["sub_warning_signal"], intent)
                        sql_["label"] = "sub_signal"
                    elif data.get("disaster"):
                        sql = self.transfor_to_sql("disaster", data["disaster"], intent)
                        sql_["label"] = "disaster"
                    elif data.get("trigger_entities"):
                        sql = self.transfor_to_sql("trigger_entities", data["trigger_entities"], intent)

                if sql:
                    sql_['sql'] = sql
                    sqls.append(sql_)
        return sqls

    def transfor_to_sql(self, label, entities, intent):
        """
        将问题转变为cypher查询语句
        :param label:实体标签
        :param entities:实体列表
        :param intent:查询意图
        :return:cypher查询语句
        """
        if not entities:
            return []
        sql = []

        # 查询灾害简介
        if intent == "query_desc" and label == "disaster":
            sql = ["MATCH (n:introduction) WHERE n.name=~'{0}.*' \
                    Match (n)-[r:rels_disaster2intro]-(p) RETURN p.name, n.content".format(e)
                   for e in entities]

        # 查询预警信号标准
        if intent == "query_desc" and label == "sub_signal":
            sql = ["MATCH (w:sub_signal) WHERE w.name=~'{0}.*' Match (w)-[r:rels_standard2sub_signal]-(p) \
                    RETURN w.name, p.standard".format(e)
                   for e in entities]

        # 查询防御措施 / 应急方法
        # TODO
        if intent == "query_ekp" and label == "disaster":
            sql = ["MATCH (d:disaster) WHERE d.name='{0}' return d.name,d.ekp".format(e) for e in entities]

        if intent == "query_ekp" and label == "sub_signal":
            sql = ["MATCH (w:sub_signal) WHERE w.name=~'{0}.*' Match (w)-[r:rels_signal_ekp]-(p) \
             return w.name, p.ekp".format(e) for e in entities]

        # 查询预警信号
        if intent == "query_warning_signal" and label == "disaster":
            sql = ["MATCH (d:disaster)-[]->(w:sub_signal) WHERE d.name='{0}' return d.name, w.name".format(e) for e in
                   entities]

        return sql

    def transfor_to_sql4query_standard(self, question_split, intent):
        sql = []
        if intent == 'query_standard':
            for i in question_split:
                word = i[0]
                tag = i[1]
                if tag == 'TIME' or tag == 'm' or tag == 'mf' or tag == 'vm' or tag == 'an' or tag == 'n':
                    # 查询慢 20秒左右
                    # sql_ = 'match p=(x)-[*]-(y)-[*]->(z) ' \
                    #        'where x.name="dummy" and y.name="%s" and z.name=~".*信号" return p' % (
                    #            word
                    #        )
                    # 10秒左右
                    sql_ = 'match p=(x)-[:rels_standard_split*]-(y)-[:rels_standard_split*]->(z) ' \
                           'where x.name="dummy" and y.name="%s" and z.name=~".*信号" return p' % (
                               word
                           )
                    sql.append(sql_)
        return sql

    def searching(self, sqls):
        """
        执行cypher查询，返回结果
        :param sqls:
        :return:str
        """
        final_answers = []
        for sql_ in sqls:
            intent = sql_['intention']
            label = sql_['label']
            queries = sql_['sql']
            answers = []
            final_answer = ''
            if intent == 'query_standard':
                for q in queries:
                    results = self.graph.run(q).data()
                    split_list = sql_['data']
                    candidate_ans = []
                    candidate_ans_standard = []
                    max = 0
                    if len(results) > 0:
                        for r in tqdm(results):
                            node_list = [i['name'] for i in r['p'].nodes]
                            cnt = 0
                            for sl in split_list:
                                if sl[0] in node_list:
                                    cnt += 1
                            if cnt != 0 and cnt >= max:
                                candidate_ans.append((r['p'].end_node['name'], cnt))
                                max = cnt
                    final_candidate_ans = []
                    for n in candidate_ans:
                        if n[1] == max:
                            final_candidate_ans.append(n)
                    if len(final_candidate_ans) > 0:
                        query_standard_sqls = ['match (p)-[r:rels_standard2sub_signal]->(q) where q.name="{0}" return ' \
                                               'p.standard'.format(i[0]) for i in final_candidate_ans]
                        for query_standard_sql in tqdm(query_standard_sqls):
                            standard = self.graph.run(query_standard_sql).data()
                            candidate_ans_standard.append(standard[0]['p.standard'])

                        send = zip(final_candidate_ans, candidate_ans_standard)
                        final_answer += self.answer_template(intent, label, list(send))
                        break
            else:
                for query in queries:
                    ress = self.graph.run(query).data()
                    answers += ress
                    final_answer = self.answer_template(intent, label, answers)
            if final_answer:
                final_answers.append(final_answer)
        return final_answers

    def answer_template(self, intent, label, answers):
        """
        根据不同意图，返回不同模板的答案
        :param intent: 查询意图
        :param answers: 知识图谱查询结果
        :return: str
        """
        final_answer = ""
        if not answers:
            return ""
        # 查询灾害简介
        if intent == "query_desc" and label == 'disaster':
            disaster_dic = {}
            for data in answers:
                name = data['p.name']
                ekp = data['n.content']
                if name not in disaster_dic:
                    disaster_dic[name] = [ekp]
                else:
                    disaster_dic[name].append(ekp)
            i = 0
            for k, v in disaster_dic.items():
                if i >= 10:
                    break
                final_answer += "灾害：{0}\n简介：{1}".format(k, v[0][:])
                i += 1

        # 查询预警信号标准
        if intent == "query_desc" and label == 'sub_signal':
            disaster_dic = {}
            for data in answers:
                name = data['w.name']
                standard = data['p.standard']
                if name not in disaster_dic:
                    disaster_dic[name] = [standard]
                else:
                    disaster_dic[name].append(standard)
            i = 0
            for k, v in disaster_dic.items():
                if i >= 10:
                    break
                final_answer += "预警信号：{0}\n标准：{1}".format(k, v[0][:])
                i += 1

        # 查询防御措施 / 应急方法
        if intent == "query_ekp" and label == "sub_signal":
            disaster_dic = {}
            for data in answers:
                name = data['w.name']
                ekp = data['p.ekp']
                if name not in disaster_dic:
                    disaster_dic[name] = [ekp]
                else:
                    disaster_dic[name].append(ekp)
            i = 0
            for k, v in disaster_dic.items():
                if i >= 10:
                    break
                final_answer += "预警信号：{0}\n防御措施 / 应急方法：{1}".format(k, v[0][:])
                i += 1

        # 查询有哪些预警信号
        if intent == "query_warning_signal" and label == "disaster":
            disaster_dic = {}
            for data in answers:
                name = data['d.name']
                signals = data['w.name']
                if name not in disaster_dic:
                    disaster_dic[name] = [signals]
                else:
                    disaster_dic[name].append(signals)
            i = 0
            for k, v in disaster_dic.items():
                if i >= 10:
                    break
                final_answer += "灾害：{0}\n预警信号：{1}".format(k, '，'.join(v))
                i += 1

        # 查询信号标准
        if intent == "query_standard" and label == "standard_split":
            for i in answers:
                final_answer += "预警信号：{0}\n标准：{1}\n".format(i[0][0], i[1])

        return final_answer
