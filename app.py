from flask import Flask, request, jsonify, render_template, redirect, url_for
import os

app = Flask(__name__)
BASE_DIRECTORY = '/home/wellington'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/explore', methods=['GET'])
def explore():
    path = request.args.get('path', '/')
    full_path = os.path.join(BASE_DIRECTORY, path.lstrip('/'))

    if not os.path.exists(full_path) or not os.path.isdir(full_path):
        return jsonify({'error': 'Diretório inválido'}), 400

    parent_path = os.path.dirname(path.rstrip('/'))
    directories = []
    files = []

    try:
        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            if os.path.isdir(item_path):
                directories.append(item)
            elif os.path.isfile(item_path):
                files.append(item)
    except PermissionError:
        return jsonify({'error': 'Permissão negada'}), 403

    return jsonify({
        'current_path': path,
        'parent_path': parent_path if path != '/' else None,
        'directories': directories,
        'files': files
    })

@app.route('/upload', methods=['POST'])
def upload():
    current_path = request.form.get('current_path', '/')
    destination = os.path.join(BASE_DIRECTORY, current_path.lstrip('/'))  # Agora o caminho completo vem do input invisível

    if not destination:
        return {'error': 'Nenhum destino selecionado'}, 400

    # Cria o diretório completo no servidor
    destination_path = os.path.join(BASE_DIRECTORY, destination)
    os.makedirs(destination_path, exist_ok=True)

    # Processar arquivos enviados individualmente
    if 'files[]' in request.files:
        files = request.files.getlist('files[]')
        for file in files:
            if file.filename:
                file_path = os.path.join(destination_path, file.filename)
                file.save(file_path)

    # Processar arquivos dentro de pastas
    if 'folder[]' in request.files:
        folders = request.files.getlist('folder[]')
        for file in folders:
            if file.filename:
                # Caminho relativo mantido pelo atributo webkitdirectory
                relative_path = file.filename
                full_path = os.path.join(destination_path, relative_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                file.save(full_path)

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
