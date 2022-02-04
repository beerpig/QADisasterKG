import jieba
import jieba.posseg as pseg
import pandas as pd
import csv


csv_data = pd.read_csv('test.csv')
std_list = []
sub_signal_list = []
for i in range(len(csv_data)):
    l = csv_data.iloc[i]['standard']
    sub_signal_list.append(csv_data.iloc[i]['sub_signal'])
    std_list.append(l.replace('，', ',').replace('（', ',').replace('）', ',').replace('。', '').replace('、', ',') \
                    .replace('；', ',').replace(' ', ''))

jieba.enable_paddle()
jieba.add_word('零下5度', tag='m')
s = '日最高气温大于或等于35度的天气称为高温天气，大于或等于38℃的天气称为酷热天气，连续5天以上的高温称为持续高温或“热浪”天气。高温预警信号分为2级，分别以黄色、橙色、红色表示。'
t = '24小时内可能或者已经受热带气旋影响，沿海或者陆地平均风力达6级以上，或者阵风8级以上并可能持续'
p = '沙尘暴天气，能见度小于1000米是什么预警信号？'

with open("split.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(['sub_signal', 'standard', 'tags'])
    for j in range(len(std_list)):
        lists = []
        lists.append(str(sub_signal_list[j]))
        print(jieba.lcut(std_list[j], HMM=True, use_paddle=True))
        HMM_paddle_cut = pseg.lcut(std_list[j], HMM=True, use_paddle=True)
        print([(j.word, j.flag) for j in HMM_paddle_cut])
        output = []
        tags = []
        for i in range(len(HMM_paddle_cut)):
            if HMM_paddle_cut[i].flag == 'TIME':
                output.append(HMM_paddle_cut[i].word)
                tags.append(HMM_paddle_cut[i].flag)
            if HMM_paddle_cut[i].flag == 'n' and HMM_paddle_cut[i].word != '，':
                output.append(HMM_paddle_cut[i].word)
                tags.append(HMM_paddle_cut[i].flag)
                if i - 1 >= 0 and HMM_paddle_cut[i].word != '，' and (HMM_paddle_cut[i - 1].flag == 'n' or HMM_paddle_cut[i - 1].flag == 'a'):
                    output.append(HMM_paddle_cut[i - 1].word + HMM_paddle_cut[i].word)
                    tags.append(HMM_paddle_cut[i - 1].flag + HMM_paddle_cut[i].flag)
            if HMM_paddle_cut[i].flag == 'm':
                output.append(HMM_paddle_cut[i].word)
                tags.append(HMM_paddle_cut[i].flag)
                if i + 1 < len(HMM_paddle_cut) and HMM_paddle_cut[i + 1].flag == 'f':
                    output.append(HMM_paddle_cut[i].word + HMM_paddle_cut[i + 1].word)
                    tags.append(HMM_paddle_cut[i].flag + HMM_paddle_cut[i + 1].flag)
                if HMM_paddle_cut[i - 1].flag == 'v':
                    output.append(HMM_paddle_cut[i - 1].word + HMM_paddle_cut[i].word)
                    tags.append(HMM_paddle_cut[i - 1].flag + HMM_paddle_cut[i].flag)
        print(output)
        ll = []
        tags_t = []
        for i in range(len(output)):
            if not output[i] in ll:
                ll.append(output[i])
                tags_t.append(tags[i])
        print(ll)
        print(tags_t)
        assert len(ll) == len(tags_t), 'error'
        lists.append(','.join(ll))
        lists.append(','.join(tags_t))
        writer.writerow(lists)
        print('========================================')
