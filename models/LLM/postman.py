import requests
import json

# API地址
url = 'http://198.58.100.164:5002/api/classify'

# POST请求的数据
data = {
    "text":"商家占道摆放水果不服城管 拿起铁锹猛击城管头部"
}

# 发送POST请求
try:
    # 将Python字典转换为JSON格式
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    
    # 检查响应状态码
    print('Status Code:', response.status_code)
    
    # 打印响应内容
    print('Response:', response.json())

except requests.exceptions.RequestException as e:
    print('Error:', e)

# Flask服务器端示例代码
'''
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/test', methods=['POST'])
def test():
    data = request.get_json()
    return jsonify({
        'message': 'success',
        'data': data
    })

if __name__ == '__main__':
    app.run(debug=True)
'''