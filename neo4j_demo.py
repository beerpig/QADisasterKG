from py2neo import Graph, Node


class neo4j_demo:
    def __init__(self):
        self.g = Graph("http://localhost:7474", auth=("neo4j", "beerpig"))

    def create_node(self, label, nodes):
        for node in nodes:
            gnode = Node(label, name=node)
            self.g.merge(gnode, label, "name")
        return

    def create_introduction_node(self, label, intros):
        for intro in intros:
            gnode = Node(label,  name=intro['name'] + '简介', content=intro['content'])
            self.g.create(gnode)

        return


if __name__ == '__main__':
    handler = neo4j_demo()
    nodes = ['高温', '暴雨', '暴雪', '洪灾', '干旱', '泥石流', '滑坡', '台风', '寒潮', '大风', '沙尘暴', '雷电', '冰雹', '霜冻', '大雾', '霾', '道路结冰']
    nodeset = set(nodes)
    intro = [{'name': '高温', 'content': "日最高气温大于或等于35℃的天气称为高温天气，大于或等于38℃的天气称为酷热天气，连续5天以上的高温称为持续高温或“热浪”天气。高温预警信号分为2级，分别以黄色、橙色、红色表示。"},
             {'name': '暴雨', 'content': "暴雨是指短时间内产生较强降雨量的天气现象，按照一定标准通常划分为暴雨、大暴雨和特大暴雨。气象部门规定：24小时雨量大于或等于50毫米称为暴雨；大于或等于100毫米称为大暴雨；大于或等于250毫米称为特大暴雨（湖南地方标准为200毫米）。暴雨预警信号分4级，分别以蓝色、黄色、橙色、红色表示。"},
             {'name': '暴雪', 'content': "暴雪是指24小时内降雪量达10毫米以上，且降雪持续，对交通或者农牧业有较大影响的一种灾害性天气。暴雪预警信号分4级，分别以蓝色、黄色、橙色、红色表示。"},
             {'name': '洪灾', 'content': "洪水是指由于暴雨或水库溃堤等引起江河水量迅猛增加及水位急剧上涨的自然现象。"},
             {'name': '干旱', 'content': "干旱是指长期无雨或少雨，人们生活、生产用水供应严重不足，土壤水分不足、农作物减产或绝收，生态环境受到破坏的自然现象。"},
             {'name': '泥石流', 'content': "泥石流是山地沟谷中由洪水引起的携带大量泥沙、石块的洪流。泥石流来势凶猛，且经常伴随山体崩塌，对农田和道路、桥梁及其他建筑物破坏极大。"},
             {'name': '滑坡', 'content': "滑坡是指斜坡上的土体或者岩体，受河流冲刷、地下水活动、地震及人工切坡等因素影响，在重力作用下，沿着一定的软弱面或者软弱带，整体地或者分散地顺坡向下滑动的自然现象。俗称“走山”、“垮山”、“地滑”、“土溜”等。"}]
    label = 'introduction'
    # handler.create_node(label, nodeset)
    handler.create_introduction_node(label, intro)
