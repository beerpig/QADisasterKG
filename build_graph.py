import os
import json
from py2neo import Graph, Node
import pandas as pd


class DisasterGraph:
    def __init__(self):
        cur_dir = '/'.join(os.path.abspath(__file__).split('/')[:-1])

        self.data_path = open("data/disaster.json", 'r', encoding='utf-8')
        self.g = Graph("http://localhost:7474", auth=("neo4j", "beerpig"))

    def read_csv(self):
        data = pd.read_csv('test.csv')
        return data

    def read_nodes(self):
        # 实体节点
        disasters = []  # 灾害
        warning_signals = []
        # emergency_key_points = []  # 应急要点、防御指南

        disaster_infos = []  # 灾害信息

        # 实体节点关系
        rels_disaster_warning_signal = []  # 灾害-预警关系
        rels_warning_signal_desc = []  # 预警信号-标准描述关系
        # rels_warning_signal_ekp = []  # 预警信号-应急防御关系

        count = 0
        self.data_path.seek(0)
        for data in self.data_path:
            disaster_dict = {}
            count += 1
            print(count)
            data_json = json.loads(data)
            disaster = data_json['disaster']
            disaster_dict['disaster'] = disaster
            disasters.append(disaster)
            disaster_dict['disaster_info'] = ''

            if 'disaster_info' in data_json:
                disaster_dict['disaster_info'] = data_json['disaster_info']

            if 'warning_signal' in data_json and data_json['warning_signal'] is not []:
                for i in data_json['warning_signal']:
                    warning_signals.append(data_json['warning_signal'][i])
                    rels_disaster_warning_signal.append([disaster, data_json['warning_signal'][i]['name']])
                    rels_warning_signal_desc.append(
                        [data_json['warning_signal'][i]['name'], data_json['warning_signal'][i]['desc']])

            if 'ekp' in data_json:
                disaster_dict['ekp'] = data_json['ekp']

            disaster_infos.append(disaster_dict)
        return set(disasters), warning_signals, disaster_infos, rels_warning_signal_desc, rels_disaster_warning_signal

    def create_node(self, label, nodes):
        count = 0
        for node in nodes:
            if isinstance(node, dict):
                gnode = Node(label, name=node['name'], desc=node['desc'], ekp=node['ekp'])
                self.g.create(gnode)
                count += 1
                print(count, len(nodes))
        return

    def create_disaster_nodes(self, disaster_infos):
        count = 0
        for disaster_dict in disaster_infos:
            node = Node("Disaster", name=disaster_dict['disaster'], desc=disaster_dict['disaster_info'],
                        ekp=disaster_dict['ekp'])
            self.g.create(node)
            count += 1
            print(count)
        return

    def create_graphnodes(self):
        disasters, warning_signals, disaster_infos, rels_warning_signal_desc, rels_disaster_warning_signal = self.read_nodes()
        self.create_disaster_nodes(disaster_infos)
        self.create_node('warning_signal', warning_signals)
        return

    def create_graphrels(self):
        disasters, warning_signals, disaster_infos, rels_warning_signal_desc, rels_disaster_warning_signal = self.read_nodes()
        self.create_relationship('Disaster', 'warning_signal', rels_disaster_warning_signal, 'warning_signal', '预警信号')

    def create_relationship(self, start_node, end_node, edges, rel_type, rel_name):
        count = 0

        set_edges = []
        for edge in edges:
            set_edges.append('###'.join(edge))
        all = len(set(set_edges))
        for edge in set(set_edges):
            edge = edge.split('###')
            p = edge[0]
            q = edge[1]
            query = "match(p:%s), (q:%s) where p.name='%s' and q.name='%s' create (p)-[rel:%s{name:'%s'}]->(q)" % (
                start_node, end_node, p, q, rel_type, rel_name)
            try:
                self.g.run(query)
                count += 1
                print(rel_type, count, all)
            except Exception as e:
                print(e)
        return


if __name__ == '__main__':
    handler = DisasterGraph()
    # handler.create_graphnodes()
    # handler.create_graphrels()
    handler.read_csv()
