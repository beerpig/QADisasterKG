from py2neo import Graph, Node
from py2neo.cypher import Record
import pandas as pd


class build_standard:
    def __init__(self):
        self.data = pd.read_csv('split.csv')
        self.g = Graph("http://localhost:7474", auth=("neo4j", "beerpig"))

    def read_data(self):
        sub_signals = []
        standards = []
        [sub_signals.append(self.data.iloc[i]['sub_signal']) for i in range(len(self.data))]
        [standards.append(self.data.iloc[i]['standard']) for i in range(len(self.data))]
        assert len(sub_signals) == len(standards), 'len(sub_signals) != len(standards)'
        return sub_signals, standards

    def build(self):
        sub_signals, standards = self.read_data()
        for i in range(len(sub_signals)):
            self.build_per(sub_signals[i], standards[i])
        return

    def build_per(self, sub_signal, standard):
        standard_list = standard.split(',')
        standard_list = standard_list[::-1]
        tx = self.g.begin()
        cursor = tx.run('create (p:standard_end{name:"dummy"}) return id(p)')
        pre_id = cursor.data()[0]['id(p)']

        for std in standard_list:
            create_standard_split_sql = 'create (p:standard_split{name:"%s"}) return id(p)' % (
                std
            )
            print(create_standard_split_sql)
            csr = tx.run(create_standard_split_sql)
            node_id = csr.data()[0]['id(p)']
            create_rel_standard_split_sql = \
                'match (p), (q) where id(p)=%s and id(q)=%s ' \
                'create (p)-[r: rels_standard_split{name:"标准切分"}]->(q)' % (
                    pre_id, node_id
                )
            print(create_rel_standard_split_sql)
            tx.run(create_rel_standard_split_sql)
            pre_id = node_id

        create_rel_signal2standard_split_sql = \
            'match (p), (q) where id(p)=%s and q.name="%s" ' \
            'create (p)-[r: rels_standard_split{name:"标准切分"}]->(q)' % (
                pre_id, sub_signal
            )
        print(create_rel_signal2standard_split_sql)
        tx.run(create_rel_signal2standard_split_sql)
        tx.commit()
        return


handler = build_standard()
handler.build()
