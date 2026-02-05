#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF to Editable PPTX - Streamlit 웹앱
"""
import sys
import io
import tempfile
from pathlib import Path
from datetime import datetime

import streamlit as st
from PIL import Image

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 페이지 설정
st.set_page_config(
    page_title="PDF → 편집 가능 PPTX",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
    .stProgress > div > div > div > div {
        background-color: #4CAF50;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """세션 상태 초기화"""
    if 'pdf_images' not in st.session_state:
        st.session_state.pdf_images = []
    if 'ocr_results' not in st.session_state:
        st.session_state.ocr_results = []
    if 'pdf_name' not in st.session_state:
        st.session_state.pdf_name = ""
    if 'processing_done' not in st.session_state:
        st.session_state.processing_done = False


def render_sidebar():
    """사이드바 설정 UI"""
    st.sidebar.header("⚙️ 변환 설정")

    # DPI 설정
    st.sidebar.subheader("해상도")
    dpi = st.sidebar.select_slider(
        "DPI",
        options=[72, 150, 300],
        value=150,
        help="높을수록 선명하지만 처리 시간이 증가합니다"
    )

    # 폰트 설정
    st.sidebar.subheader("폰트")
    font_options = ["맑은 고딕", "나눔고딕", "Pretendard", "Arial", "Calibri"]
    font_name = st.sidebar.selectbox(
        "폰트 선택",
        options=font_options,
        index=0
    )

    font_mode = st.sidebar.radio(
        "폰트 크기",
        options=["자동 (OCR 추정)", "고정 크기"],
        index=0
    )

    fixed_font_size = 12
    if font_mode == "고정 크기":
        fixed_font_size = st.sidebar.slider(
            "폰트 크기 (pt)",
            min_value=8,
            max_value=72,
            value=12
        )

    use_auto_font_size = font_mode == "자동 (OCR 추정)"

    # 배경 설정
    st.sidebar.subheader("배경 이미지")
    include_background = st.sidebar.checkbox(
        "배경 이미지 포함",
        value=True,
        help="원본 PDF 이미지를 배경으로 포함합니다"
    )

    background_opacity = 100
    if include_background:
        background_opacity = st.sidebar.slider(
            "배경 투명도",
            min_value=0,
            max_value=100,
            value=100,
            format="%d%%",
            help="0%=투명, 100%=불투명"
        )

    # OCR 설정
    st.sidebar.subheader("OCR 설정")
    confidence_threshold = st.sidebar.slider(
        "신뢰도 임계값",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.1,
        help="이 값 미만의 텍스트는 무시됩니다"
    )

    return {
        'dpi': dpi,
        'font_name': font_name,
        'use_auto_font_size': use_auto_font_size,
        'fixed_font_size': fixed_font_size,
        'include_background': include_background,
        'background_opacity': background_opacity,
        'confidence_threshold': confidence_threshold,
    }


def process_pdf(uploaded_file, settings, progress_container):
    """PDF 처리 및 OCR"""
    from webapp.pdf_processor import PDFProcessor
    from webapp.ocr_engine import OCREngine

    # PDF 처리기
    processor = PDFProcessor(dpi=settings['dpi'])

    # 진행률 표시
    progress_bar = progress_container.progress(0)
    status_text = progress_container.empty()

    try:
        # PDF 열기
        status_text.text("📄 PDF 파일 열기...")
        pdf_bytes = uploaded_file.read()
        page_count = processor.open(pdf_bytes)
        progress_bar.progress(10)

        # 이미지 렌더링
        status_text.text(f"🖼️ PDF를 이미지로 변환 중... (0/{page_count})")

        def render_progress(current, total):
            pct = 10 + int((current / total) * 40)
            progress_bar.progress(pct)
            status_text.text(f"🖼️ PDF를 이미지로 변환 중... ({current}/{total})")

        images = processor.render_all_pages(
            dpi=settings['dpi'],
            progress_callback=render_progress
        )
        processor.close()

        # OCR 초기화
        status_text.text("🔤 OCR 엔진 초기화...")
        progress_bar.progress(55)

        ocr = OCREngine(
            lang="korean",
            use_gpu=False,
            confidence_threshold=settings['confidence_threshold']
        )

        # OCR 실행
        status_text.text(f"🔍 텍스트 추출 중... (0/{len(images)})")

        def ocr_progress(current, total):
            pct = 55 + int((current / total) * 40)
            progress_bar.progress(pct)
            status_text.text(f"🔍 텍스트 추출 중... ({current}/{total})")

        ocr_results = ocr.process_pdf_images(
            images,
            progress_callback=ocr_progress
        )

        progress_bar.progress(100)
        status_text.text("✅ 처리 완료!")

        return images, ocr_results

    except Exception as e:
        status_text.text(f"❌ 오류: {str(e)}")
        raise e


def render_preview(images, ocr_results):
    """미리보기 표시"""
    st.subheader("📑 미리보기")

    if not images:
        st.info("PDF를 업로드하고 '처리 시작'을 클릭하세요.")
        return

    # 페이지 선택
    page_num = st.selectbox(
        "페이지 선택",
        options=range(len(images)),
        format_func=lambda x: f"페이지 {x + 1}",
    )

    col1, col2 = st.columns(2)

    with col1:
        st.write("**원본 이미지**")
        st.image(images[page_num], use_container_width=True)

    with col2:
        st.write("**OCR 결과**")
        blocks = ocr_results[page_num] if page_num < len(ocr_results) else []

        if blocks:
            for i, block in enumerate(blocks):
                confidence_color = "green" if block.confidence > 0.8 else "orange" if block.confidence > 0.5 else "red"
                st.markdown(
                    f"**{i+1}.** {block.text} "
                    f"<span style='color:{confidence_color}'>({block.confidence:.2f})</span>",
                    unsafe_allow_html=True
                )
        else:
            st.warning("이 페이지에서 텍스트를 찾지 못했습니다.")

    # 통계
    total_blocks = sum(len(blocks) for blocks in ocr_results)
    st.info(f"총 {len(images)}페이지, {total_blocks}개 텍스트 블록 추출됨")


def generate_pptx(images, ocr_results, settings, progress_container):
    """PPTX 생성"""
    from webapp.pptx_builder import EditablePPTXBuilder

    progress_bar = progress_container.progress(0)
    status_text = progress_container.empty()

    status_text.text("📊 PPTX 생성 중...")

    builder = EditablePPTXBuilder(
        font_name=settings['font_name'],
        default_font_size=settings['fixed_font_size'],
        include_background=settings['include_background'],
        background_opacity=settings['background_opacity']
    )

    def build_progress(current, total):
        pct = int((current / total) * 90)
        progress_bar.progress(pct)
        status_text.text(f"📊 슬라이드 생성 중... ({current}/{total})")

    builder.add_slides_from_ocr_results(
        images=images,
        ocr_results=ocr_results,
        use_auto_font_size=settings['use_auto_font_size'],
        fixed_font_size=settings['fixed_font_size'],
        progress_callback=build_progress
    )

    progress_bar.progress(95)
    status_text.text("💾 파일 저장 중...")

    pptx_bytes = builder.save_to_bytes()

    progress_bar.progress(100)
    status_text.text("✅ PPTX 생성 완료!")

    return pptx_bytes


def main():
    """메인 앱"""
    init_session_state()

    # 헤더
    st.markdown('<p class="main-header">📊 PDF → 편집 가능 PPTX</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">이미지 기반 PDF를 OCR로 텍스트 추출하여 편집 가능한 PowerPoint로 변환합니다</p>',
        unsafe_allow_html=True
    )

    # 사이드바 설정
    settings = render_sidebar()

    # 메인 영역
    col_upload, col_action = st.columns([2, 1])

    with col_upload:
        st.subheader("📤 PDF 업로드")
        uploaded_file = st.file_uploader(
            "PDF 파일을 드래그하거나 클릭하여 업로드",
            type=['pdf'],
            help="이미지 기반 PDF 파일을 업로드하세요"
        )

    with col_action:
        st.subheader("🚀 변환")

        if uploaded_file:
            st.write(f"**파일명:** {uploaded_file.name}")
            st.write(f"**크기:** {uploaded_file.size / 1024:.1f} KB")

            process_btn = st.button(
                "📄 처리 시작",
                type="primary",
                use_container_width=True
            )
        else:
            st.info("PDF 파일을 업로드해주세요")
            process_btn = False

    # 진행률 컨테이너
    progress_container = st.container()

    # PDF 처리
    if process_btn and uploaded_file:
        with st.spinner("처리 중..."):
            try:
                images, ocr_results = process_pdf(
                    uploaded_file,
                    settings,
                    progress_container
                )

                st.session_state.pdf_images = images
                st.session_state.ocr_results = ocr_results
                st.session_state.pdf_name = Path(uploaded_file.name).stem
                st.session_state.processing_done = True

                st.success("✅ PDF 처리 완료!")

            except Exception as e:
                st.error(f"❌ 처리 실패: {str(e)}")
                st.session_state.processing_done = False

    # 미리보기
    if st.session_state.processing_done:
        st.divider()
        render_preview(
            st.session_state.pdf_images,
            st.session_state.ocr_results
        )

        # PPTX 생성 버튼
        st.divider()
        st.subheader("📥 PPTX 다운로드")

        col1, col2 = st.columns([1, 2])

        with col1:
            generate_btn = st.button(
                "🔄 PPTX 생성",
                type="primary",
                use_container_width=True
            )

        if generate_btn:
            pptx_progress = st.container()

            try:
                pptx_bytes = generate_pptx(
                    st.session_state.pdf_images,
                    st.session_state.ocr_results,
                    settings,
                    pptx_progress
                )

                # 파일명 생성
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{st.session_state.pdf_name}_editable_{timestamp}.pptx"

                with col2:
                    st.download_button(
                        label="📥 PPTX 다운로드",
                        data=pptx_bytes,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        use_container_width=True
                    )

                st.success(f"✅ PPTX 생성 완료! 파일명: {filename}")

            except Exception as e:
                st.error(f"❌ PPTX 생성 실패: {str(e)}")

    # 푸터
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: #888; font-size: 0.9rem;'>
        Made with ❤️ by Noterang | PaddleOCR + python-pptx
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
