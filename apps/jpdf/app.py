#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JPDF Web App - PDF/이미지 → 편집 가능 PPTX 변환 웹 서비스
"""
import os
import sys
import uuid
import shutil
from pathlib import Path
from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from jpdf import JPDF, convert_images_to_pptx

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB 제한
app.config['UPLOAD_FOLDER'] = Path('uploads')
app.config['OUTPUT_FOLDER'] = Path('outputs')

# 폴더 생성
app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True)
app.config['OUTPUT_FOLDER'].mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/convert', methods=['POST'])
def convert():
    """파일 변환 API"""
    try:
        # API 키 확인
        api_key = request.form.get('api_key', '').strip()
        if not api_key:
            api_key = os.getenv('GOOGLE_VISION_API_KEY')
        if not api_key:
            return jsonify({'error': 'Google Vision API 키가 필요합니다.'}), 400

        # 파일 확인
        if 'file' not in request.files:
            return jsonify({'error': '파일이 없습니다.'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'PDF, PNG, JPG 파일만 지원합니다.'}), 400

        # 옵션
        mode = request.form.get('mode', 'editable')  # editable or direct
        font_family = request.form.get('font_family', 'Arial')
        font_size = request.form.get('font_size', '')
        font_size = int(font_size) if font_size.isdigit() else None

        # 파일 저장
        job_id = str(uuid.uuid4())[:8]
        filename = secure_filename(file.filename)
        input_path = app.config['UPLOAD_FOLDER'] / f"{job_id}_{filename}"
        file.save(str(input_path))

        # 출력 파일명
        output_filename = f"{input_path.stem}_편집가능.pptx"
        output_path = app.config['OUTPUT_FOLDER'] / f"{job_id}_{output_filename}"

        # 변환 실행
        ext = input_path.suffix.lower()

        if ext == '.pdf':
            converter = JPDF(api_key)
            if mode == 'editable':
                converter.convert(
                    str(input_path),
                    str(output_path),
                    inpaint=True,
                    font_size=font_size,
                    font_family=font_family
                )
            else:
                # 바로 만들기 (이미지 기반)
                converter.convert(
                    str(input_path),
                    str(output_path),
                    inpaint=False,
                    font_size=font_size,
                    font_family=font_family
                )
        else:
            # 이미지 파일
            convert_images_to_pptx(
                [str(input_path)],
                str(output_path),
                api_key=api_key,
                editable=(mode == 'editable'),
                font_size=font_size,
                font_family=font_family
            )

        # 입력 파일 삭제
        input_path.unlink(missing_ok=True)

        return jsonify({
            'success': True,
            'job_id': job_id,
            'filename': output_filename
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/download/<job_id>/<filename>')
def download(job_id, filename):
    """파일 다운로드"""
    file_path = app.config['OUTPUT_FOLDER'] / f"{job_id}_{filename}"
    if not file_path.exists():
        return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404

    return send_file(
        str(file_path),
        as_attachment=True,
        download_name=filename
    )


@app.route('/cleanup/<job_id>')
def cleanup(job_id):
    """임시 파일 정리"""
    for f in app.config['OUTPUT_FOLDER'].glob(f"{job_id}_*"):
        f.unlink(missing_ok=True)
    return jsonify({'success': True})


if __name__ == '__main__':
    print("🚀 JPDF Web App 시작")
    print("   http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
