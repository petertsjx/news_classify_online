#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import schedule
import time
import logging
import os
from datetime import datetime
import sqlalchemy
from sqlalchemy import create_engine, text
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
import joblib
import jieba  # 中文分词库
import re
from utils import extract_title
from gpt_api import classify_text

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("news_classifier.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("news_classifier")

# 数据库配置
LOCAL_DB_CONFIG = {
    'host': '127.0.0.1',
    'database': 'news_classification',
    'user': 'root',
    'password': '123_datuzi',
    'port': 3306
}
REMOTE_DB_CONFIG ={
    'host': '45.79.28.51',
    'database': 'news-prod',
    'user': 'news_ai',
    'password': '5t!yXnUKjJ9z',
    'port': 3306
}

# 模型配置
MODEL_PATH = 'model/'
CATEGORIES = ['政治', '经济', '体育', '科技', '娱乐', '国际', '社会', '教育']  # 示例分类标签

class NewsClassifier:
    def __init__(self, local_db_config=None,remote_db_config=None):
        """初始化分类器"""
        if local_db_config is None:
            local_db_config = LOCAL_DB_CONFIG
        if remote_db_config is None:
            remote_db_config = REMOTE_DB_CONFIG

        
        self.local_db_config = local_db_config
        self.remote_db_config = REMOTE_DB_CONFIG
        self.local_engine = self._create_db_connection("local")
        self.remote_engine=self._create_db_connection("remote")
        self.model = None
        self.vectorizer = None
        
        # 确保模型目录存在
        os.makedirs(MODEL_PATH, exist_ok=True)
        
        # 加载已有模型或创建新模型
        self._load_or_create_model()
        
    def _create_db_connection(self,engine_type):
        """创建数据库连接"""
        if engine_type=="local":
            conn_str = f"mysql+pymysql://{self.local_db_config['user']}:{self.local_db_config['password']}@{self.local_db_config['host']}:{self.local_db_config['port']}/{self.local_db_config['database']}"
        if engine_type=="remote":
            conn_str = f"mysql+pymysql://{self.remote_db_config['user']}:{self.remote_db_config['password']}@{self.remote_db_config['host']}:{self.remote_db_config['port']}/{self.remote_db_config['database']}"
        return create_engine(conn_str)
    
    def _load_or_create_model(self):
        """加载已有模型，如果不存在则创建新模型"""
        model_file = os.path.join(MODEL_PATH, 'news_classifier_model.pkl')
        vectorizer_file = os.path.join(MODEL_PATH, 'tfidf_vectorizer.pkl')
        
        if os.path.exists(model_file) and os.path.exists(vectorizer_file):
            logger.info("加载现有模型...")
            self.model = joblib.load(model_file)
            self.vectorizer = joblib.load(vectorizer_file)
            logger.info("模型加载完成")
        else:
            logger.info("没有找到现有模型，将在首次运行时创建新模型")
    
    def preprocess_text(self, text):
        """文本预处理：去除特殊字符、分词等"""
        if not text or pd.isna(text):
            return ""
        
        # 去除HTML标签和特殊字符
        text = re.sub(r'<.*?>', '', text)
        text = re.sub(r'[^\w\s]', '', text)
        
        # 中文分词
        words = jieba.cut(text)
        return ' '.join(words)
    
    def train_model(self, force=False):
        """训练新闻分类模型"""
        model_file = os.path.join(MODEL_PATH, 'news_classifier_model.pkl')
        
        # 如果模型已存在且不强制训练，则跳过
        if os.path.exists(model_file) and not force:
            logger.info("模型已存在，跳过训练")
            return
        
        logger.info("开始训练模型...")
        
        # 从数据库中获取已标记的数据
        try:
            query = text("""
                SELECT id, content, category 
                FROM news_articles 
                WHERE category IS NOT NULL
            """)
            df = pd.read_sql(query, self.engine)
            
            if len(df) < 100:  # 检查是否有足够的训练数据
                logger.warning("训练数据不足，需要至少100条带标签的记录")
                return
            
            # 文本预处理
            df['processed_content'] = df['content'].apply(self.preprocess_text)
            
            # 特征提取
            self.vectorizer = TfidfVectorizer(max_features=5000, min_df=5, max_df=0.7)
            X = self.vectorizer.fit_transform(df['processed_content'])
            y = df['category']
            
            # 划分训练集和测试集
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # 训练模型（这里使用随机森林分类器，您可以根据需要替换为其他模型）
            from sklearn.ensemble import RandomForestClassifier
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.model.fit(X_train, y_train)
            
            # 评估模型
            from sklearn.metrics import classification_report
            y_pred = self.model.predict(X_test)
            report = classification_report(y_test, y_pred)
            logger.info(f"模型评估报告:\n{report}")
            
            # 保存模型
            joblib.dump(self.model, model_file)
            joblib.dump(self.vectorizer, os.path.join(MODEL_PATH, 'tfidf_vectorizer.pkl'))
            logger.info("模型训练完成并保存")
            
        except Exception as e:
            logger.error(f"训练模型失败: {str(e)}")
    
    def get_unclassified_news(self):
        remote_query= text("""
        SELECT * from article
        """)
        remote_df=pd.read_sql(remote_query, self.remote_engine)
        local_query = text("""
        SELECT * from news_category_mapping
        """)
        local_df=pd.read_sql(local_query, self.local_engine)
        news_ids_to_remove = local_df['news_id'].unique()
        filtered_data = remote_df[~remote_df['id'].isin(news_ids_to_remove)]
        print("filtered_data: ",len(filtered_data))
        return filtered_data

    def classify_news(self):

        try:
            # 获取未分类的新闻
            '''
            query = text("""
                SELECT a.id, a.title,a.description
                FROM article a
                WHERE NOT EXISTS (
                    SELECT 1 
                    FROM news_category_mapping nc 
                    WHERE nc.news_id = a.id
                );
            """)
            unclassified_news = pd.read_sql(query, self.engine)
            '''
            unclassified_news=self.get_unclassified_news();
            
            
            if len(unclassified_news) == 0:
                logger.info("没有未分类的新闻")
                return
            
            logger.info(f"找到 {len(unclassified_news)} 条未分类新闻")
            
            # 预处理并分类
            df=extract_title(unclassified_news)
            update_count = 0
            for index,row in df.iterrows():
                news_id=row['id']
                merged_text=row['merged_text']
                category=classify_text(merged_text);
                print("category: ",category)
                if category==-1:
                    logger.info(f"新闻 {id} 预测失败")
                    continue
                else:
                    category=category[0]
                # 更新数据库
                with self.engine.begin() as conn:
                    print("即将执行：","新闻:",news_id,"分类:",category)
                    conn.execute(
                        text("INSERT INTO news_category_mapping (news_id,category_id,confidence) VALUES (:id,:category,0);"),
                            {"category": int(category), "id": news_id}
                    )
                    update_count += 1
                    logger.info(f"成功更新 {update_count} 条新闻分类")
                
        except Exception as e:
            logger.error(f"分类新闻失败: {str(e)}")
    
    def check_model_performance(self):
        """检查模型性能，如果性能下降则重新训练"""
        try:
            # 获取最近已分类的新闻样本
            query = text("""
                SELECT id, content, category, predicted_category
                FROM news_articles
                WHERE category IS NOT NULL 
                AND predicted_category IS NOT NULL
                ORDER BY update_time DESC
                LIMIT 100
            """)
            recent_news = pd.read_sql(query, self.engine)
            
            if len(recent_news) < 50:
                logger.info("样本不足，无法评估模型性能")
                return
                
            # 计算准确率
            accuracy = (recent_news['category'] == recent_news['predicted_category']).mean()
            logger.info(f"当前模型准确率: {accuracy:.4f}")
            
            # 如果准确率低于阈值，重新训练模型
            if accuracy < 0.8:
                logger.warning(f"模型性能低于阈值 (0.8)，准备重新训练")
                self.train_model(force=True)
                
        except Exception as e:
            logger.error(f"检查模型性能失败: {str(e)}")
    
    def run_scheduled_job(self):
        """运行定时任务"""
        logger.info("开始定时任务")
        '''
        # 首先检查是否需要训练/更新模型
        if self.model is None or self.vectorizer is None:
            self.train_model()
        else:
            # 每周检查一次模型性能
            current_weekday = datetime.now().weekday()
            if current_weekday == 6:  # 星期日
                self.check_model_performance()
        '''
        
        # 分类新闻
        self.classify_news()
        
        logger.info("定时任务完成")

def main():
    """主函数：初始化分类器并设置定时任务"""
    classifier = NewsClassifier()
    
    # 设置定时任务：每小时运行一次
    #schedule.every(1).hours.do(classifier.run_scheduled_job)
    
    # 立即执行一次任务
    classifier.run_scheduled_job()
    
    # 持续运行定时任务
    logger.info("新闻分类系统已启动，等待定时任务执行...")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()