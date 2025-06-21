from flask import Flask, jsonify, request
from src.main import fetch_target_iv

app = Flask(__name__)

@app.route('/api/targetiv')
def targetiv():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing url parameter'}), 400
    data = fetch_target_iv(url)
    return jsonify({'result': data})

if __name__ == '__main__':
    app.run(debug=True)