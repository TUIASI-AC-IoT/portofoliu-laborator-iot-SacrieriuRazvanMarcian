from flask import Flask, jsonify, request, abort,send_from_directory
import os

app = Flask(__name__)

FILES_DIR='files'

if not os.path.exists(FILES_DIR):
    try:
        os.mkdir(FILES_DIR)
    except Exception as e:
        print(f"Error creating directory '{FILES_DIR}': {e}")

@app.route("/")
def home():
    return send_from_directory(app.static_folder,'index.html')

@app.route("/files",methods=['GET'])
def displayDirectory():
    try:
        dir_list=os.listdir(FILES_DIR)
    except FileNotError: 
        return jsonify({'error': f"Directory '{FILES_DIR}' not found."}), 404
    return jsonify({'files':dir_list}),200

@app.route("/files/<filename>",methods=['GET'])
def read_file(filename):
    filepath=os.path.join(FILES_DIR,filename)
    try:
        if not os.path.exists(filepath):
            return jsonify({'error':'File not found'}), 404
        with open(filepath, 'r') as f:
            content=f.read()
        return jsonify({'content':content}), 200
    except Exception as e:
        return jsonify({'error':str(e)}),500

@app.route("/files",methods=['POST'])
def create_file():
    data=request.json
    filename=data.get('filename')
    content=data.get('content','')
    if not filename:
        return jsonify({'error':'Filename is required'}), 400
    filepath=os.path.join(FILES_DIR,filename)
    try:
        if os.path.exists(filepath):
            return jsonify({'error':'FIle already exists'}), 400
        with open(filepath,'w') as f:
            f.write(content)
        return jsonify({'message':f'File {filename} created successfully'}), 201
    except Exception as e:
        return jsonify({'error':str(e)}),500


@app.route("/files/<filename>",methods=['PUT'])
def update_file(filename):
    filepath=os.path.join(FILES_DIR,filename)
    try:
        if not os.path.exists(filepath):
            return jsonify({'error':'File not found'}),404
        data=request.json
        content = data.get('content','')
        with open(filepath,'w') as f:
            f.write(content)
        return jsonify({'message':f"File {filename} updated successfully"}),201
    except Exception as e:
        return jsonify({'error':str(e)}),500

@app.route("/files/<filename>", methods=['DELETE'])
def delete_file(filename):
    filepath = os.path.join(FILES_DIR,filename)
    try:
        if not os.path.exists(filepath):
            return jsonify({'error':'File not found'}), 404
        os.remove(filepath)
        return jsonify({'message': f'File {filename} deleted successfully'}),201
    except Exception as e:
        return jsonify({'error':str(e)}),500


if __name__ == "__main__":
    app.run(debug=True)
