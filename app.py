from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory, send_file
from pathlib import Path
import logging
import zipfile
import io
import os

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

BASE_DIRECTORY = Path.home()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/explore')
def explore():
    rel = request.args.get('path', '').strip().lstrip('/')
    if rel in ('', '.', '/'):
        rel = ''

    full_path = (BASE_DIRECTORY / rel).resolve()

    try:
        full_path.relative_to(BASE_DIRECTORY)
    except ValueError:
        return jsonify({'error': 'Diretório inválido'}), 400

    if not full_path.exists() or not full_path.is_dir():
        return jsonify({'error': 'Não é um diretório válido'}), 400

    dirs = [p.name for p in full_path.iterdir() if p.is_dir()]
    files = [p.name for p in full_path.iterdir() if p.is_file()]

    rel_to_base = full_path.relative_to(BASE_DIRECTORY)
    current = '' if rel_to_base == Path('.') else str(rel_to_base)

    parent = ''
    if current:
        parent = str(Path(current).parent) 

    return jsonify({
        'current_path': current,
        'parent_path': parent,
        'directories': dirs,
        'files': files
    })

@app.route('/upload', methods=['POST'])
def upload():
    rel = request.form.get('current_path', '').lstrip('/')
    dest = (BASE_DIRECTORY / rel).resolve()

    app.logger.debug(f"[upload] rel={rel!r}, dest={dest}")

    try:
        dest.relative_to(BASE_DIRECTORY)
    except ValueError:
        return jsonify({'error': 'Destino inválido'}), 400

    dest.mkdir(parents=True, exist_ok=True)

    for f in request.files.getlist('files[]'):
        if f.filename:
            target = dest / f.filename
            target.write_bytes(f.read())

    for f in request.files.getlist('folder[]'):
        if f.filename:
            target = dest / f.filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(f.read())

    return redirect(url_for('index'))

@app.route('/download')
def download():
    rel = request.args.get('path', '').strip().lstrip('/')
    if rel in ('', '.', '/'):
        return jsonify({'error': 'Nenhum arquivo ou pasta especificado'}), 400

    full_path = (BASE_DIRECTORY / rel).resolve()
    try:
        full_path.relative_to(BASE_DIRECTORY)
    except ValueError:
        return jsonify({'error': 'Acesso negado'}), 403

    if not full_path.exists():
        return jsonify({'error': 'Não encontrado'}), 404

    if full_path.is_file():
        return send_from_directory(
            directory=str(full_path.parent),
            path=full_path.name,
            as_attachment=True
        )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(full_path):
            for filename in files:
                absfname = os.path.join(root, filename)
                arcname = os.path.relpath(absfname, full_path.parent)
                zf.write(absfname, arcname)
    buffer.seek(0)

    zip_name = f"{full_path.name}.zip"
    return send_file(
        buffer,
        mimetype='application/zip',
        download_name=zip_name,
        as_attachment=True
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
