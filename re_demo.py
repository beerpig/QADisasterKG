# coding: utf-8
import re
import os

with open("re_demo.txt", "r", encoding='utf-8') as f:  # 打开文件
    line = f.readline()
    while line:
        line = line.strip('\n')
        pattern = re.compile(r"标准(:|：).*")
        tmp = pattern.search(line)
        print(tmp.string)
        line = f.readline().strip('\n')
        while line:
            p = re.compile(r'防御')
            t = p.search(line)
            if not t:
                print(tmp.string + line.strip('\n'))
                line = f.readline()
            else:
                line = f.readline()
                break
    f.close()

