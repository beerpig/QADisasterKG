from py2neo import Graph, Node
import pandas as pd


class SignalGraph:
    def __init__(self):
        self.data = pd.read_csv('test.csv')
        self.g = Graph("http://localhost:7474", auth=("neo4j", "beerpig"))

    def read_nodes(self):
        # 实体节点
        signals = []
        sub_signals = []
        standards = []
        ekps = []  # 防御指南 string

        # 实体节点关系
        rels_signal2sub_signal = []
        rels_standard = []
        rels_standard2sub_signal = []
        rels_signal_ekp = []

        for i in range(len(self.data)):
            signals.append([self.data.iloc[i]['signal_index'], self.data.iloc[i]['signal']])
            sub_signals.append(
                [self.data.iloc[i]['signal_index'], self.data.iloc[i]['sub_signal'], self.data.iloc[i]['sub_index']])
            standards.append(
                [self.data.iloc[i]['signal_index'], self.data.iloc[i]['standard'], self.data.iloc[i]['sub_index']])
            ekps.append([self.data.iloc[i]['sub_index'], self.data.iloc[i]['ekp']])
            rels_signal2sub_signal.append([signals[i], sub_signals[i]])
            rels_standard.append([signals[i], standards[i]])
            rels_signal_ekp.append([sub_signals[i], ekps[i]])
            rels_standard2sub_signal.append([standards[i], sub_signals[i]])
        return signals, sub_signals, standards, ekps, rels_signal2sub_signal, rels_standard, rels_standard2sub_signal, rels_signal_ekp

    def create_graphnodes(self):
        signals, sub_signals, standards, ekps, _, _, _, _ = self.read_nodes()
        self.create_signalsnode('signal', signals)
        self.create_sub_signalsnode('sub_signal', sub_signals)
        self.create_standardsnode('standard', standards)
        self.create_ekpsnode('ekp', ekps)
        return

    def create_graphrels(self):
        _, _, _, _, rels_signal2sub_signal, rels_standard, rels_standard2sub_signal, rels_signal_ekp = self.read_nodes()
        self.create_signal2sub_signal_relationship('signal', 'sub_signal', rels_signal2sub_signal, 'rels_signal2sub_signal', '预警信号和子预警信号')
        self.create_standard_relationship('signal', 'standard', rels_standard, 'rels_standard', '预警信号和子预警信号的标准')
        self.create_standard2sub_signal_relationship('standard', 'sub_signal', rels_standard2sub_signal, 'rels_standard2sub_signal', '子预警信号标准和子预警信号')
        self.create_signal_ekp_relationship('sub_signal', 'ekp', rels_signal_ekp, 'rels_signal_ekp', '子预警信号和防御措施')

    def create_signalsnode(self, lable, nodes):
        signal_set = []
        for node in nodes:
            if node[0] not in signal_set:
                gnode = Node(lable, name=node[1], index=int(node[0]))
                signal_set.append(node[0])
                self.g.create(gnode)
        return

    def create_sub_signalsnode(self, lable, nodes):
        for node in nodes:
            gnode = Node(lable, name=node[1], index=int(node[0]), sub_index=int(node[2]))
            self.g.create(gnode)
        return

    def create_standardsnode(self, lable, nodes):
        for node in nodes:
            gnode = Node(lable, standard=node[1], index=int(node[0]), sub_index=int(node[2]))
            self.g.create(gnode)
        return

    def create_ekpsnode(self, lable, nodes):
        for node in nodes:
            gnode = Node(lable, ekp=node[1], sub_index=int(node[0]))
            self.g.create(gnode)
        return

    def create_signal2sub_signal_relationship(self, start_node, end_node, edges, rel_type, rel_name):
        edge_set = []
        for edge in edges:
            m = int(edge[0][0])
            if m not in edge_set:
                query = "match(p:%s), (q:%s) where p.index=%s and q.index=%s create (p)-[rel:%s{name:'%s'}]->(q)" % (
                    start_node, end_node, m, int(edge[1][0]), rel_type, rel_name
                )
                edge_set.append(m)
                try:
                    print(query)
                    self.g.run(query)
                    print('CQL:' + query)
                except Exception as e:
                    print(e)
        return

    def create_standard_relationship(self, start_node, end_node, edges, rel_type, rel_name):
        edge_set = []
        for edge in edges:
            m = int(edge[0][0])
            if m not in edge_set:
                query = "match(p:%s), (q:%s) where p.index=%s and q.index=%s create (p)-[rel:%s{name:'%s'}]->(q)" % (
                    start_node, end_node, m, int(edge[1][0]), rel_type, rel_name
                )
                edge_set.append(m)
                try:
                    print(query)
                    self.g.run(query)
                    print('CQL:' + query)
                except Exception as e:
                    print(e)
        return

    def create_standard2sub_signal_relationship(self, start_node, end_node, edges, rel_type, rel_name):
        for edge in edges:
            query = "match(p:%s), (q:%s) where p.sub_index=%s and q.sub_index=%s create (p)-[rel:%s{name:'%s'}]->(q)" % (
                start_node, end_node, int(edge[0][2]), int(edge[1][2]), rel_type, rel_name
            )
            try:
                print(query)
                self.g.run(query)
                print('CQL:' + query)
            except Exception as e:
                print(e)
        return

    def create_signal_ekp_relationship(self, start_node, end_node, edges, rel_type, rel_name):
        for edge in edges:
            query = "match(p:%s), (q:%s) where p.sub_index=%s and q.sub_index=%s create (p)-[rel:%s{name:'%s'}]->(q)" % (
                start_node, end_node, int(edge[0][2]), int(edge[1][0]), rel_type, rel_name
            )
            try:
                print(query)
                self.g.run(query)
                print('CQL:' + query)
            except Exception as e:
                print(e)
        return


if __name__ == '__main__':
    handler = SignalGraph()
    handler.read_nodes()
    handler.create_graphnodes()
    handler.create_graphrels()
