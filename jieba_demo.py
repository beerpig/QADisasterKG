import jieba
import jieba.posseg as pseg

jieba.enable_paddle()
# jieba.add_word('连续3天')
s = '连续3天日最高气温将在35度以上'
t = '24小时内可能或者已经受热带气旋影响，沿海或者陆地平均风力达6级以上，或者阵风8级以上并可能持续'
p = '沙尘暴天气，能见度小于1000米是什么预警信号？'
print(jieba.lcut(p, HMM=True, use_paddle=True))
HMM_paddle_cut = pseg.lcut(p, HMM=True, use_paddle=True)
print([(i.word, i.flag) for i in HMM_paddle_cut if i.flag == 'n'])
