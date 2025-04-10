
import stanza
import re
from collections import defaultdict


text="一位作者发了[数值]张截图说[人名]把自己的帖子删了马斯克回复这是撒谎"

class CustomEntityRecognizer:
    def __init__(self):
        # 自定义实体字典，格式为 {实体类型: [实体列表]}
        self.custom_entities = {
            'PRODUCT': ['小米手机', '华为手机', '苹果手机', 'iPhone', 'HUAWEI Mate', '小米MIX'],
            'TECH_COMPANY': ['阿里巴巴', '腾讯', '百度', '小米', '华为', '字节跳动', '谷歌', '微软'],
            'CHINESE_ENTREPRENEUR': ['马云', '马化腾', '李彦宏', '雷军', '任正非', '张一鸣'],
            'PERSON':['特朗普','李曙光']
        }
        # 将实体列表编译为正则表达式
        self.entity_patterns = {}
        for entity_type, entities in self.custom_entities.items():
            # 按长度排序，优先匹配较长的实体
            sorted_entities = sorted(entities, key=len, reverse=True)
            pattern = '|'.join(re.escape(entity) for entity in sorted_entities)
            self.entity_patterns[entity_type] = re.compile(f'({pattern})')
        self.nlp = stanza.Pipeline('zh', processors='tokenize,pos,lemma,ner')

    def find_entities(self, text):
        """在文本中查找所有自定义实体"""
        custom_entities = []
        for entity_type, pattern in self.entity_patterns.items():
            for match in pattern.finditer(text):
                custom_entities.append({
                    'text': match.group(),
                    'type': entity_type,
                    'start_char': match.start(),
                    'end_char': match.end()
                })

        # 处理重叠问题（保留最长匹配）
        return self._resolve_overlaps(custom_entities)

    def _resolve_overlaps(self, entities):
        """解决重叠实体问题，保留最长匹配"""
        if not entities:
            return []

        # 按起始位置排序
        sorted_entities = sorted(entities, key=lambda x: (x['start_char'], -x['end_char']))
        result = [sorted_entities[0]]

        for entity in sorted_entities[1:]:
            prev = result[-1]
            # 检查是否重叠
            if entity['start_char'] >= prev['end_char']:
                result.append(entity)
            # 如果当前实体更长，则替换
            elif entity['end_char'] - entity['start_char'] > prev['end_char'] - prev['start_char']:
                result[-1] = entity

        return result

    # 可视化标注（在文本中用不同颜色标记出实体）
    def visualize_entities(text, entities):
        """生成带有HTML标记的文本以可视化实体"""
        # 为不同类型的实体分配不同颜色
        entity_colors = defaultdict(lambda: "#" + hex(hash(str()) % 0xFFFFFF)[2:].zfill(6))
        entity_colors.update({
            'PERSON': '#ff6666',
            'ORG': '#66cc66',
            'LOC': '#6666ff',
            'PRODUCT': '#cc66cc',
            'TECH_COMPANY': '#66cccc',
            'CHINESE_ENTREPRENEUR': '#cccc66'
        })

        # 按位置排序实体
        sorted_entities = sorted(entities, key=lambda x: x['start_char'])

        # 构建标记文本
        marked_text = ""
        last_end = 0

        for entity in sorted_entities:
            start = entity['start_char']
            end = entity['end_char']
            entity_type = entity['type']

            # 添加实体前的文本
            if start > last_end:
                marked_text += text[last_end:start]

            # 添加带标记的实体
            color = entity_colors[entity_type]
            marked_text += f'<span style="background-color:{color};" title="{entity_type}">{text[start:end]}</span>'

            last_end = end

        # 添加最后的文本
        if last_end < len(text):
            marked_text += text[last_end:]

        return marked_text

    def prediction(self,text):
        # 获取Stanza识别的实体
        doc = self.nlp(text)
        stanza_entities = []
        for sent in doc.sentences:
            for ent in sent.ents:
                stanza_entities.append({
                    'text': ent.text,
                    'type': ent.type,
                    'start_char': ent.start_char,
                    'end_char': ent.end_char
                })

        # 获取自定义实体
        custom_entities = self.find_entities(text)

        # 合并实体列表（优先使用自定义实体）
        all_entities = []
        custom_entity_spans = [(e['start_char'], e['end_char']) for e in custom_entities]

        # 先添加不与自定义实体重叠的Stanza实体
        for entity in stanza_entities:
            overlap = False
            for custom_start, custom_end in custom_entity_spans:
                if not (entity['end_char'] <= custom_start or entity['start_char'] >= custom_end):
                    overlap = True
                    break
            if not overlap:
                all_entities.append(entity)

        # 然后添加所有自定义实体
        all_entities.extend(custom_entities)

        # 按位置排序
        all_entities.sort(key=lambda x: x['start_char'])

        # 输出结果
        '''
        print("识别到的所有实体:")
        for entity in all_entities:
            print(f"实体: {entity['text']}, 类型: {entity['type']}, 位置: {entity['start_char']}-{entity['end_char']}")
        '''
        return all_entities


def add_custom_entity(recognizer, entity_type, entity_list):
    """向自定义实体识别器添加新的实体类型和实体列表"""
    if entity_type not in recognizer.custom_entities:
        recognizer.custom_entities[entity_type] = []

    recognizer.custom_entities[entity_type].extend(entity_list)

    # 更新正则表达式
    sorted_entities = sorted(recognizer.custom_entities[entity_type], key=len, reverse=True)
    pattern = '|'.join(re.escape(entity) for entity in sorted_entities)
    recognizer.entity_patterns[entity_type] = re.compile(f'({pattern})')

    return recognizer

def train_custom_ner_model(train_data, model_dir):
    """
    训练自定义NER模型

    Args:
        train_data: 训练数据格式为 [(句子, [(开始位置, 结束位置, 实体类型), ...]), ...]
        model_dir: 模型保存目录
    """
    # 这部分在实际应用中需要准备训练数据并使用Stanza的训练接口
    # 示例代码框架
    '''
    import torch
    from stanza.models.ner.trainer import Trainer
    from stanza.models.common.doc import Document

    # 准备训练数据
    train_docs = []
    for sentence, entities in train_data:
        words = list(sentence)  # 字符级分词
        tags = ['O'] * len(words)
        for start, end, entity_type in entities:
            for i in range(start, end):
                prefix = 'B-' if i == start else 'I-'
                tags[i] = prefix + entity_type

        train_docs.append(Document([], text=sentence, words=words, tags=tags))

    # 配置训练参数
    args = {
        'wordvec_dir': './wordvec',
        'max_steps': 10000,
        'batch_size': 32,
        'dropout': 0.5,
        'learning_rate': 0.001,
        'model_dir': model_dir
    }

    # 初始化训练器并训练模型
    trainer = Trainer(args)
    trainer.train(train_docs)
    '''
    print("训练自定义NER模型的代码框架（需要实际训练数据）")




