from flask import Flask, request, jsonify
from datetime import datetime
from chatGPT import NewsClassifier

app = Flask(__name__)
app.json.ensure_ascii = False
api_key = "sk-LDzDuiWkxUoM3w0DPsEdcLZhhdEI2o2a5Il6u3M77cHZ03MA"
classifier = NewsClassifier(api_key)
# 示例分类函数（你可以替换为实际的分类逻辑）
def classify_text(text):
    # 这里是示例分类逻辑
    classifier.set_news_num(1)
    result = classifier.classify_news(text)
    print(result)
    if result['category'] == 1:
        return result['result'][0]
    else:
        return "-1"

@app.route('/api/classify', methods=['POST'])
def classify():
    if not request.is_json:
        return jsonify({
            "status": "错误",
            "message": "请求必须是JSON格式",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 400

    data = request.get_json()
    
    # 检查是否包含文本字段
    if 'text' not in data:
        return jsonify({
            "status": "错误",
            "message": "缺少文本字段",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 400

    text = data['text']
    category = classify_text(text)
    category=int(category)
    
    if category==-1:
        return jsonify({
        "status": "失败",
        "message": "出现错误",
        "data": {
            "text": text,
            "category": category,
            "description":"",
            "length": len(text)
        },
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    else:
        description = classifier.get_type_dict()[category]
        return jsonify({
            "status": "成功",
            "message": "文本分类完成",
            "data": {
                "text": text,
                "category": category,
                "description":description,
                "length": len(text)
            },
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

if __name__ == '__main__':
    app.run("0.0.0.0",debug=True,port="5002")