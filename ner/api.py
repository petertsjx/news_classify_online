from flask import Flask, jsonify, make_response
from datetime import datetime
import json

def read_json(file_path):
    """从指定的 JSON 文件中读取数据并返回 Python 对象。"""
    try:
        with open(file_path, 'r',encoding="utf-8") as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print("文件未找到，请检查文件路径。")
    except json.JSONDecodeError:
        print("文件格式错误，无法解析 JSON。")
    except Exception as e:
        print(f"发生错误: {e}")

app = Flask(__name__)
app.json.ensure_ascii = False

# 示例数据
data=read_json("data_sampled_entities.json")


@app.route('/api/data', methods=['GET'])
def get_books():
    response = make_response(jsonify({
        "status": "sucess",
        "message": "sucess",
        "data": data,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }))
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response




if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True)