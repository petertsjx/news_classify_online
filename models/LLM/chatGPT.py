import http.client
import json
import time
import re
from typing import Dict, List, Union

from scipy.integrate import lebedev_rule


class NewsClassifier:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.conn = http.client.HTTPSConnection("api.tu-zi.com")
        self.news_num = 0
        
        self.type_dict = {
            1: "国际政治与外交 包括： 国际政治（俄日韩朝美国欧洲非洲）、国家间关系、外交访问与通话、国际组织动态、国际条约与协定、主权与领土争端、外交政策声明、制裁（政治目的）、选举与领导人更迭（非中国）。",
            2: "中国时政与时事 包括： 法律修订执行、中央及地方政府人事任免、国家新闻机构与传播、反腐败行动、重要会议（如两会）、政府政策发布与解读（如乡村振兴、八项规定）、人权相关案件与议题。",
            3: "经济与商业 包括： 宏观经济数据（GDP、CPI、LPR、失业率、产品产量等）、贸易政策与争端（含关税）、金融市场动态（股市、汇率、利率）、产业发展与监管、企业新闻（经营、并购、投资、丑闻）",
            4: "社会与民生 包括： 中国社会热点事件与争议，打工人就业、犯罪案件与司法审判、公共安全事件（非灾难事故）、民众维权行动、教育医疗议题、人口与生育政策、生活服务问题、特定维稳群体关切（如农民工、退役军人）、劳工问题（讨薪、罢工）",
            5: "科技与环境 包括： 重大科研和装备（AI、芯片、航天、生物医药、核电等）、科技企业动态（非纯商业层面）、科研进展、环境保护与气候变化、能源（新能源、核能）",
            6: "军事与安全 包括： 国防政策、军事演习与行动、地区安全局势（如南海、台海）、军备发展、恐怖主义与反恐、国家安全（间谍活动、网络安全）",
            7: "灾难与事故 包括： 全球自然灾害（地震、火灾、洪水、滑坡等）、重大事故（交通、工业、建筑坍塌等）和救援行动",
            8: "文化与人物 包括： 文化艺术动态、娱乐媒体与传播、体育赛事（如亚冬会）、知名人物活动与逝世、中国历史回顾与纪念。",
            9: "加密货币与web3 包括： 比特币、以太坊、币安、炒币、币圈诈骗。",
            10: "不属于以上分类的新闻"
        }
        
        '''
        self.type_dict = {
            1: "国际政治与外交",
            2: "中国国内政治 ",
            3: "经济与商业 ",
            4: "社会与民生" ,
            5: "科技与环境 ",
            6: "军事与安全",
            7: "灾难与事故 ",
            8: "文化与人物 ",
            9: "加密货币与web3 ",
            10: "其他：不属于以上类别的新闻"
        }
        '''
    def get_type_dict(self):
        return self.type_dict
        
    def create_prompt(self, news_text: str) -> str:
        if self.news_num>1:
            prompt = f"""你是一个新闻分类助手，请严格按照提供的分类标准对下列{self.news_num}条新闻进行分类，请直接返回所属类别的数字序号，答案中间用_隔开，组合成一串字符串。

            分类标准：
            {json.dumps(self.type_dict, ensure_ascii=False, indent=2)}

            新闻文本：
            {news_text}
            """
        else:
            prompt = f"""你是一个新闻分类助手，请严格按照提供的分类标准对下列{self.news_num}条新闻进行分类，请直接返回所属类别的数字序号

            分类标准：
            {json.dumps(self.type_dict, ensure_ascii=False, indent=2)}

            新闻文本：
            {news_text}
            """

            
        return prompt

    def set_news_num(self,news_num:int):
        self.news_num = news_num

    def classify_news(self, news_text: str, max_retries: int = 1) -> Dict[str, Union[int, str, float]]:
        headers = {
            'Authorization': 'Bearer sk-YXG8dZnpWpf7fMcJ04vbaWPNxS3VKILTNWB4RkKFpDaQdb3L',
            'Content-Type': 'application/json'
        }
        payload = json.dumps({
            "model": "gpt-4o-mini",  # 根据实际可用模型调整
            "messages": [
                {"role": "user", "content": self.create_prompt(news_text)}
            ],
            "temperature": 0.1
        })
        result=[]
        #print(self.create_prompt(news_text))
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                
                self.conn.request("POST", "/v1/chat/completions?=null", payload, headers)

                end_time = time.time()
                process_time = end_time - start_time
                response = self.conn.getresponse()

                if response.status == 200:
                    response_data = response.read()

                    # 根据实际API返回格式调整
                    classification = json.loads(response_data)["choices"][0]["message"]["content"]
                    def extract_numbers2(text):
                        if '10' not in text:
                            numbers = re.findall(r'\d', text)
                        else:
                            numbers=['10']
                        return numbers
                    if self.news_num>1:
                        for c in re.split(r'_',classification):
                            result.append(int(c.strip()))
                    else:
                        result = extract_numbers2(classification)
                    print("before try: ",result,news_text)
                    try:
                        result_num = len(result)
                        if result_num == self.news_num or result ==[]:
                            return {
                                "category":1,
                                "result": result,
                                "process_time": round(process_time, 2),
                                "status": "success"
                            }
                        else:
                            raise ValueError
                    except ValueError:
                        if attempt == max_retries - 1:
                            return {
                                "category": -1,
                                "category_name": "结果和新闻数量不匹配",
                                "process_time": round(process_time, 2),
                                "status": "error: invalid category",
                                "result": result
                            }
                else:
                    if attempt == max_retries - 1:
                        return {
                            "category": -1,
                            "category_name": "请求错误",
                            "process_time": round(process_time, 2),
                            "status": f"error: API request failed with status {response.status}"
                        }

            except Exception as e:
                if attempt == max_retries - 1:
                    return {
                        "category": -1,
                        "category_name": "无结果",
                        "process_time": 0,
                        "status": f"error: {str(e)}",
                        "result":result
                    }
                time.sleep(1)  # 在重试前等待1秒

        return {
            "category": -1,
            "category_name": "无结果",
            "process_time": 0,
            "status": "error: max retries reached"
        }


def main():
    import pandas as pd
    # 替换为你的图资API密钥
    api_key = "sk-LDzDuiWkxUoM3w0DPsEdcLZhhdEI2o2a5Il6u3M77cHZ03MA"
    classifier = NewsClassifier(api_key)
    data_path="../../data_process/XXX_0.csv"
    df = pd.read_csv(data_path)
    batch_size=5

    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i + batch_size]
        # 在这里处理这10条数据
        print(f"Processing batch from index {i} to {i+batch_size-1}")
        # print(batch)
        text = ""
        for index, row in batch.iterrows():
            # index是行索引，row是每一行的数据
            # print(index, row['id'],row['text'])
            text += "这是新闻："+str(index)+":"+row['merged_text'] + "\n"+"\n"

        classifier.set_news_num(len(batch))
        
        result = classifier.classify_news(text)

        if result['category'] == 1:
            print("预测成功")
            with open("result_XXX_0_classify_by_gpt_mini_o4.txt","a+",encoding="utf-8") as f:
                for id,text,label in zip(batch['id'],batch['merged_text'],result['result']):
                        f.write(f"{id},{text},{label}"+"\n")
        else:
            print("预测失败")
            with open("error_XXX_0_classify_by_gpt_mini_o4.txt", "a+", encoding="utf-8") as f:
                f.write(f"Processing batch from index {i} to {i+batch_size-1}"+"\n")
            print(result)
            with open("error.log","a+",encoding="utf-8") as f:
                f.write(json.dumps(result)+"\n")
         
     
        
        

    '''
    # 测试新闻
    test_news = [
    "特斯拉第一季度交付数据不及预期，股价大跌7%。分析师认为，需求疲软和价格战影响了特斯拉的业绩表现。",
    "中国国家主席习近平访问美国。",
    "网友投稿月日云南昆明市城管开始收缴路边电动车"
    ]

    text=""
    for news in test_news:
        text += news + "\n"

    classifier.set_news_num(len(test_news))
    result = classifier.classify_news(text)
    #print(json.dumps(result, ensure_ascii=False, indent=2))
    if result['category']==1:
        print("预测成功")
        
    else:
        print("预测失败")
        '''



if __name__ == "__main__":
    main()
    