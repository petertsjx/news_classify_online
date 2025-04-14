import stanza
import re
from collections import defaultdict
from ner_model import CustomEntityRecognizer
import json
from tqdm import tqdm

 
def read_json(file_path):
    """从指定的 JSON 文件中读取数据并返回 Python 对象。"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print("文件未找到，请检查文件路径。")
    except json.JSONDecodeError:
        print("文件格式错误，无法解析 JSON。")
    except Exception as e:
        print(f"发生错误: {e}")

def save_json(data, file_path):
    """将数据保存到指定的 JSON 文件中。"""
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)  # 保存为 JSON 格式
        print(f"数据已成功保存到 {file_path}")
    except Exception as e:
        print(f"发生错误: {e}")

def extract_sample_news_entities(): 
    custom_recognizer = CustomEntityRecognizer()
    data_path = "data.json"
    data= read_json(data_path)
    events = data["data"]["data"]["events"]

    type_constrain={'PERSON','GPE','DATE','ORG','LAW','LOC'}
    new_envents=[]
    for event in tqdm(events[0:1500]):
        entity_dict={}
        for sample_news in event["sample_news"]:
            sample_news_entities=custom_recognizer.prediction(sample_news['title'])
            for entity in sample_news_entities:
                if entity['text'] not in entity_dict and len(entity['text'])>1:
                    entity_dict[entity['text']]=entity['type']
        
        event["sample_news_entities_summary"] = entity_dict
        new_envents.append(event)
    data["data"]["data"]["events"]=new_envents 

    file_path="new_data_1.json"
    save_json(data,file_path)
        


    # 示例中文文本
    #text="一位作者发了[数值]张截图说[人名]把自己的帖子删了马斯克回复这是撒谎"


    #custom_recognizer = CustomEntityRecognizer()
    #custom_recognizer.prediction(text)

def merge_json():
    data1_path="new_data.json"
    data2_path="new_data_1.json"
    data1= read_json(data1_path)
    data2= read_json(data2_path)
    events1 = data1["data"]["data"]["events"]
    events2 = data2["data"]["data"]["events"]

    events1.extend(events2)
    data1["data"]["data"]["events"]=events1
    file_path="data_sampled_entities.json"
    save_json(data1,file_path)
    return 

#merge_json()
extract_sample_news_entities()




