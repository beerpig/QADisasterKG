import pandas as pd

data = pd.read_csv('test.csv')

l = []
for i in range(len(data.values)):
    l.append(data.values[i][2])
disaster_set = set(l)
# with open('data/disaster_vocab.txt', 'w', encoding='utf-8') as f:
#     for every in iter(disaster_set):
#         f.write(every[: -4] + '\n')
# with open('data/warning_signal_vocab.txt', 'w', encoding='utf-8') as f:
#     for every in iter(disaster_set):
#         f.write(every + '\n')
with open('data/sub_warning_signal_vocab.txt', 'w', encoding='utf-8') as f:
    for every in iter(disaster_set):
        f.write(every + '\n')
        f.write(every[: -2] + '\n')
