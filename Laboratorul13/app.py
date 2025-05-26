from flask import Flask,request,jsonify,send_from_directory
from flask_jwt_extended import(
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity, get_jwt
)
import os,uuid,random,string
from datetime import datetime

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'cheie_secreta'
jwt = JWTManager(app)

CONFIG_DIR='configs'
os.makedirs(CONFIG_DIR,exist_ok=True)

users={
    "admin": {"password": "test123", "role": "admin"},
    "guest": {"password": "parola123", "role": "guest"},
    "owner": {"password": "owner", "role": "owner"}
}

blacklist=set()

@app.route("/")
def start():
    return send_from_directory('static', 'index.html')

@app.route('/auth/jwtStore', methods=['DELETE'])
@jwt_required()
def logout():
    jti=get_jwt()['jti']
    if jti in blacklist:
        return jsonify(msg='Token already revoked'), 400
    blacklist.add(jti)
    return jsonify(msg='Token revoked'),200

@jwt.token_in_blocklist_loader
def check_token(jwt_header,jwt_payload):
    jti = jwt_payload['jti']
    return jti in blacklist

@jwt.unauthorized_loader
def custom_missing_token_callback(callback):
    return jsonify({'msg': 'Missing or invalid token. Please log in.'}), 401

@jwt.invalid_token_loader
def custom_invalid_token_callback(error):
    return jsonify({'msg': 'Invalid token. Please log in again.'}), 401


@app.route('/auth',methods=['POST'])
def auth():
    data=request.get_json()
    username=data.get('username')
    password=data.get('password')

    user=users.get(username)
    if not user or user['password'] != password:
        return jsonify({"msg": "Invalid username or password"}), 401

    access_token = create_access_token(identity=username,additional_claims={"role":user['role']})
    return jsonify(access_token=access_token), 200

@app.route('/auth/jwtStore',methods=['GET'])
@jwt_required()
def validate_token():
    identity=get_jwt_identity()
    claims=get_jwt()
    return jsonify({"msg":"Token is valid","user":{"username":identity,"role":claims['role']}}),200

@app.route('/generate_sensors', methods=['POST'])
@jwt_required()
def generate_sensors():
    claims = get_jwt()
    if claims['role'] != 'admin':
        return jsonify({'msg': 'Only admin can generate sensors'}), 403

    count = int(request.json.get('count', 5))
    types = ['temperature', 'humidity', 'pressure', 'light', 'motion']
    generated = []
    for _ in range(count):
        sensor_id = 'sensor_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        filepath = os.path.join(CONFIG_DIR, f'{sensor_id}.cfg')
        if os.path.exists(filepath):
            return jsonify({'msg': 'No new sensors generated; all sensors already exist'}), 200
        with open(filepath, 'w') as f:
            f.write(f"# Config for {sensor_id}\n")
            f.write(f"Type: {random.choice(types)}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        generated.append(sensor_id)
    return jsonify({'generated': generated}), 200

@app.route('/sensors', methods=['GET'])
@jwt_required()
def list_sensors():
    claims=get_jwt()
    if claims['role'] not in ['admin','owner']:
            return jsonify({'msg': 'Access denied: insufficient permissions'}), 403
    sensors = [f.replace('.cfg', '') for f in os.listdir(CONFIG_DIR) if f.endswith('.cfg')]
    return jsonify({'sensors': sensors}), 200

@app.route('/sensors', methods=['POST'])
@jwt_required()
def add_sensor():
    claims = get_jwt()
    if claims['role'] != 'admin':
        return jsonify({'msg': 'Only admin can add sensors'}), 403

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

@app.route('/sensors/<sensor_id>', methods=['GET'])
@jwt_required()
def get_sensor(sensor_id):
    claims = get_jwt()
    if claims['role'] not in ['admin','owner']:
        return jsonify({'msg': 'Access denied: insufficient permissions'}), 403
    
    filepath = os.path.join(CONFIG_DIR, f"{sensor_id}.cfg")
    if not os.path.exists(filepath):
        return jsonify({'msg': 'Sensor not found'}), 404
    with open(filepath, 'r') as f:
        content = f.read()
    return jsonify({'sensor_id': sensor_id, 'config': content}), 200

@app.route('/sensors/<sensor_id>', methods=['PUT'])
@jwt_required()
def update_sensor(sensor_id):
    claims = get_jwt()
    if claims['role'] != 'admin':
        return jsonify({'msg': 'Only admin can update sensors'}), 403

    filepath = os.path.join(CONFIG_DIR, f"{sensor_id}.cfg")
    if not os.path.exists(filepath):
        return jsonify({'msg': 'Sensor not found'}), 404

    data = request.json
    with open(filepath, 'w') as f:
        f.write(f"# Updated config for {sensor_id}\n")
        f.write(f"Type: {data.get('type', 'unknown')}\n")
        f.write(f"Timestamp: {data.get('timestamp', 'not provided')}\n")
    return jsonify({'msg': f'Sensor {sensor_id} updated'}), 200

@app.route('/sensors/<sensor_id>', methods=['DELETE'])
@jwt_required()
def delete_sensor(sensor_id):
    claims = get_jwt()
    if claims['role'] != 'admin':
        return jsonify({'msg': 'Only admin can delete sensors'}), 403

    filepath = os.path.join(CONFIG_DIR, f"{sensor_id}.cfg")
    if not os.path.exists(filepath):
        return jsonify({'msg': 'Sensor not found'}), 404

    os.remove(filepath)
    return jsonify({'msg': f'Sensor {sensor_id} deleted'}), 200

if __name__ == '__main__':
    app.run(debug=True)
