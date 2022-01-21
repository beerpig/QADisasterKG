from py2neo import Graph


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
        if intent == "query_desc" and label == "sub_warning_signal":
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

        # 查询 根据标准查询对应的预警信号
        # TODO
        if intent == "query_trigger_signal" and label == "trigger_entities":
            pass

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
            for query in queries:
                ress = self.graph.run(query).data()
                answers += ress
            final_answer = self.answer_template(intent, label, answers)
            if final_answer:
                final_answers.append(final_answer)
        return final_answers

    def answer_template(self, intent, label,  answers):
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
                final_answer += "\n\t灾害：{0}\n\t简介：{1}\n".format(k, v[0][:])
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
                final_answer += "\n\t预警信号：{0}\n\t标准：{1}\n".format(k, v[0][:])
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
                final_answer += "\n\t预警信号：{0}\n\t防御措施 / 应急方法：{1}\n".format(k, v[0][:])
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
                final_answer += "\n\t灾害：{0}\n\t预警信号：{1}\n".format(k, '，'.join(v))
                i += 1

        # 查询治愈率
        if intent == "query_rate":
            disease_dic = {}
            for data in answers:
                name = data['d.name']
                r = data['d.rate']
                if name not in disease_dic:
                    disease_dic[name] = [r]
                else:
                    disease_dic[name].append(r)
            i = 0
            for k, v in disease_dic.items():
                if i >= 10:
                    break
                final_answer += "疾病 {0} 的治愈率为：{1}\n".format(k, ','.join(list(set(v))))
                i += 1
        # 查询检查项目
        if intent == "query_checklist":
            disease_dic = {}
            for data in answers:
                name = data['d.name']
                r = data['d.checklist']
                if name not in disease_dic:
                    disease_dic[name] = [r]
                else:
                    disease_dic[name].append(r)
            i = 0
            for k, v in disease_dic.items():
                if i >= 10:
                    break
                final_answer += "疾病 {0} 的检查项目有：{1}\n".format(k, ','.join(list(set(v))))
                i += 1
        # 查询科室
        if intent == "query_department":
            disease_dic = {}
            for data in answers:
                name = data['d.name']
                r = data['n.name']
                if name not in disease_dic:
                    disease_dic[name] = [r]
                else:
                    disease_dic[name].append(r)
            i = 0
            for k, v in disease_dic.items():
                if i >= 10:
                    break
                final_answer += "疾病 {0} 所属科室有：{1}\n".format(k, ','.join(list(set(v))))
                i += 1
        # 查询疾病描述
        if intent == "disease_describe":
            disease_infos = {}
            for data in answers:
                name = data['d.name']
                age = data['d.age']
                insurance = data['d.insurance']
                infection = data['d.infection']
                checklist = data['d.checklist']
                period = data['d.period']
                rate = data['d.rate']
                money = data['d.money']
                if name not in disease_infos:
                    disease_infos[name] = [age, insurance, infection, checklist, period, rate, money]
                else:
                    disease_infos[name].extend([age, insurance, infection, checklist, period, rate, money])
            i = 0
            for k, v in disease_infos.items():
                if i >= 10:
                    break
                message = "疾病 {0} 的描述信息如下：\n发病人群：{1}\n医保：{2}\n传染性：{3}\n检查项目：{4}\n" \
                          "治愈周期：{5}\n治愈率：{6}\n费用：{7}\n"
                final_answer += message.format(k, v[0], v[1], v[2], v[3], v[4], v[5], v[6])
                i += 1

        return final_answer
