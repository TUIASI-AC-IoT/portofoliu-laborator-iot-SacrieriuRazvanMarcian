from flask import Flask, request, jsonify, send_from_directory
import os
import uuid
import random
import string
from datetime import datetime

app = Flask(__name__)

CONFIG_DIR = 'configs'
os.makedirs(CONFIG_DIR, exist_ok=True)

@app.route("/")
def start():
    return send_from_directory('static', 'index.html')

@app.route('/generate_sensors', methods=['POST'])
def generate_sensors():
    try:
        count = int(request.json.get('count', 5))
        types = ['temperature', 'humidity', 'pressure', 'light', 'motion']
        generated = []

        for _ in range(count):
            sensor_id = 'sensor_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            filepath = os.path.join(CONFIG_DIR, f'{sensor_id}.cfg')

            if os.path.exists(filepath):
                continue

            with open(filepath, 'w') as f:
                f.write(f"# Config for {sensor_id}\n")
                f.write(f"Type: {random.choice(types)}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")

            generated.append(sensor_id)

        if not generated:
            return jsonify({'msg': 'No new sensors generated; all sensors already exist'}), 200

        return jsonify({'generated': generated}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/sensors', methods=['GET'])
def list_sensors():
    try:
        sensors = [f.replace('.cfg', '') for f in os.listdir(CONFIG_DIR) if f.endswith('.cfg')]
        if not sensors:
            return jsonify({'msg': 'No sensors available'}), 404
        return jsonify({'sensors': sensors}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/sensors', methods=['POST'])
def add_sensor():
    try:
        data = request.json
        sensor_id = data.get('sensor_id') or f'sensor_{uuid.uuid4().hex[:8]}'
        filepath = os.path.join(CONFIG_DIR, f'{sensor_id}.cfg')

        if os.path.exists(filepath):
            return jsonify({'msg': 'Sensor already exists'}), 400

        with open(filepath, 'w') as f:
            f.write(f"# Config for {sensor_id}\n")
            f.write(f"Type: {data.get('type', 'unknown')}\n")
            f.write(f"Timestamp: {data.get('timestamp', 'not provided')}\n")

        return jsonify({'msg': f'Sensor {sensor_id} created'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/sensors/<sensor_id>', methods=['GET'])
def get_sensor(sensor_id):
    try:
        filepath = os.path.join(CONFIG_DIR, f"{sensor_id}.cfg")
        if not os.path.exists(filepath):
            return jsonify({'msg': 'Sensor not found'}), 404

        with open(filepath, 'r') as f:
            content = f.read()

        return jsonify({'sensor_id': sensor_id, 'config': content}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/sensors/<sensor_id>', methods=['PUT'])
def update_sensor(sensor_id):
    try:
        filepath = os.path.join(CONFIG_DIR, f"{sensor_id}.cfg")
        if not os.path.exists(filepath):
            return jsonify({'msg': 'Sensor not found'}), 404

        data = request.json
        with open(filepath, 'w') as f:
            f.write(f"# Updated config for {sensor_id}\n")
            f.write(f"Type: {data.get('type', 'unknown')}\n")
            f.write(f"Timestamp: {data.get('timestamp', 'not provided')}\n")

        return jsonify({'msg': f'Sensor {sensor_id} updated'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/sensors/<sensor_id>', methods=['DELETE'])
def delete_sensor(sensor_id):
    try:
        filepath = os.path.join(CONFIG_DIR, f"{sensor_id}.cfg")
        if not os.path.exists(filepath):
            return jsonify({'msg': 'Sensor not found'}), 404

        os.remove(filepath)
        return jsonify({'msg': f'Sensor {sensor_id} deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
