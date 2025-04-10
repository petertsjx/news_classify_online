from utils import process_full_test_data,cut_df
import pandas as pd
data_path = "../data/full_test_update.csv"
df=process_full_test_data(data_path)[['id','merged_text']]
cut_df(df,10)

'''
data_path = "XXX_0.csv"
test_news = pd.read_csv(data_path)[0:3]
for  id,text,label in zip(test_news['id'],test_news['merged_text'],[1,2,3]):
    print(id,text,label)
'''

