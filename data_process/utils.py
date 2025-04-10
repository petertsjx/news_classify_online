import pandas as pd
import re
import emoji
from zhon.hanzi import punctuation

def remove_emoji_simple(text):
    if pd.isna(text):
        return ''
    return emoji.replace_emoji(str(text), '')


def extract_title(df):
    # 清洗title和description
    df['clean_title'] = df['title'].apply(clean_text)
    df['clean_description'] = df['description'].apply(clean_text)
    # 合并文本并去重
    df['merged_text'] = df.apply(
        lambda x: ' '.join(set(filter(None, [x['clean_title'],x['clean_description']]))),
        axis=1
    )

    # 删除字数小于2的行
    df = df[df['merged_text'].str.len() > 2]

    # 删除临时列
    df = df.drop(['clean_title'], axis=1)

    return df

def clean_text(text):
    if pd.isna(text):
        return ''
    # 转换为字符串
    text = str(text)

    # 去除表情符号
    text = remove_emoji_simple(text)
    # 去除网址
    text = re.sub(r'http\S+|www.\S+', '', text)
    # 去除数字
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'\n', '', text)
    # 去除英文
    text = re.sub(r'[a-zA-Z]+', '', text)
    chinese_punc = '，。！？；：""''【】（）《》〈〉、「」『』〔〕…—－～'
    # 去除中文标点符号
    text = re.sub(f'[{punctuation}]', '', text)
    # 去除其他特殊字符和空白字符
    pattern = f'[^\u4e00-\u9fff{chinese_punc}a-zA-Z0-9]'
    cleaned_text = re.sub(pattern, '', text)
    return text.strip()

import math
import pandas as pd
from tqdm import tqdm

def cut_df(df, n):
    df_num = len(df)
    every_epoch_num = math.floor((df_num/n))
    for index in tqdm(range(n)):
        file_name = f'./XXX_{index}.csv' # 切割后的文件名
        if index < n-1:
            df_tem = df[every_epoch_num * index: every_epoch_num * (index + 1)]
        else:
            df_tem = df[every_epoch_num * index:]
        df_tem.to_csv(file_name, index=False)




def process_full_test_data(path):
    df = pd.read_csv(path)
    return extract_title(df)