# -*- coding: utf-8 -*-
import json
import os
import zipfile
from datetime import datetime

# 1. 슬라이드 프롬프트 JSON 로드
with open('G:/내 드라이브/notebooklm/slide-prompt-viewer/slide_prompts.json', 'r', encoding='utf-8') as f:
    prompts_data = json.load(f)

prompts_json = json.dumps(prompts_data, ensure_ascii=False)

# 2. 통합 HTML 생성
html_content = '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 Vibe 코딩 완벽 가이드 + 디자인 100</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
            line-height: 1.8;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }

        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }

        header h1 { font-size: 2.5em; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.2); }
        header p { font-size: 1.2em; opacity: 0.9; }

        /* 탭 네비게이션 */
        .tab-nav {
            background: #f8f9fa;
            padding: 15px 20px;
            border-bottom: 3px solid #667eea;
            position: sticky;
            top: 0;
            z-index: 100;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            justify-content: center;
        }

        .tab-btn {
            padding: 12px 24px;
            border: none;
            background: white;
            color: #667eea;
            border-radius: 25px;
            cursor: pointer;
            font-weight: 600;
            font-size: 1rem;
            transition: all 0.3s;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        .tab-btn:hover { background: #667eea; color: white; transform: translateY(-2px); }
        .tab-btn.active { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }

        .tab-content { display: none; }
        .tab-content.active { display: block; }

        /* 가이드 탭 스타일 */
        .guide-content { padding: 40px; }

        nav.section-nav {
            background: #f0f0f0;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 30px;
        }

        nav.section-nav ul {
            list-style: none;
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 10px;
        }

        nav.section-nav a {
            text-decoration: none;
            color: #667eea;
            padding: 8px 16px;
            background: white;
            border-radius: 20px;
            transition: all 0.3s;
            font-weight: 500;
            font-size: 0.9rem;
        }

        nav.section-nav a:hover { background: #667eea; color: white; }

        section {
            margin-bottom: 50px;
            padding: 30px;
            background: #f8f9fa;
            border-radius: 15px;
            border-left: 5px solid #667eea;
        }

        section h2 {
            color: #667eea;
            font-size: 1.8em;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        section h3 {
            color: #764ba2;
            font-size: 1.4em;
            margin: 25px 0 15px 0;
            padding-left: 15px;
            border-left: 3px solid #764ba2;
        }

        .step-number {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 45px;
            height: 45px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 50%;
            font-weight: bold;
            font-size: 1.3em;
        }

        .info-box {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin: 15px 0;
            border: 2px solid #e9ecef;
        }

        .warning-box {
            background: #fff3cd;
            border-left: 5px solid #ffc107;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }

        .success-box {
            background: #d4edda;
            border-left: 5px solid #28a745;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }

        .code-block {
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 20px;
            border-radius: 10px;
            overflow-x: auto;
            margin: 15px 0;
            font-family: 'Courier New', monospace;
            position: relative;
        }

        .link-button {
            display: inline-block;
            padding: 12px 25px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 25px;
            transition: all 0.3s;
            margin: 10px 5px;
            font-weight: 600;
        }

        .link-button:hover { transform: translateY(-3px); box-shadow: 0 6px 15px rgba(0,0,0,0.3); }

        .mcp-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }

        .mcp-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            transition: all 0.3s;
            border: 2px solid #e9ecef;
        }

        .mcp-card:hover { transform: translateY(-5px); border-color: #667eea; }
        .mcp-card h4 { color: #667eea; margin-bottom: 10px; font-size: 1.2em; }

        ul, ol { margin-left: 30px; margin-top: 10px; }
        li { margin: 8px 0; }

        /* 디자인 100 탭 스타일 */
        .design-content {
            background: #0f172a;
            min-height: 100vh;
            color: #f1f5f9;
        }

        .design-header {
            text-align: center;
            padding: 40px 20px;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        }

        .design-header h2 {
            font-size: 2rem;
            background: linear-gradient(135deg, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
        }

        .design-header p { color: #94a3b8; }

        .design-stats {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 20px;
            flex-wrap: wrap;
        }

        .design-stat {
            background: #334155;
            padding: 15px 25px;
            border-radius: 12px;
            text-align: center;
        }

        .design-stat-num { font-size: 1.8rem; font-weight: 700; color: #3b82f6; }
        .design-stat-label { font-size: 0.85rem; color: #94a3b8; }

        .design-container { max-width: 1400px; margin: 0 auto; padding: 20px; }

        .design-search {
            display: flex;
            justify-content: center;
            margin-bottom: 25px;
        }

        .design-search input {
            width: 100%;
            max-width: 450px;
            padding: 14px 24px;
            border: 2px solid #475569;
            background: #1e293b;
            color: #f1f5f9;
            border-radius: 30px;
            font-size: 1rem;
            outline: none;
        }

        .design-search input:focus { border-color: #3b82f6; }
        .design-search input::placeholder { color: #64748b; }

        .design-filters {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            justify-content: center;
            margin-bottom: 25px;
            padding: 15px;
            background: #1e293b;
            border-radius: 12px;
        }

        .design-filter-btn {
            padding: 8px 16px;
            border: 1px solid #475569;
            background: #334155;
            color: #f1f5f9;
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.2s;
        }

        .design-filter-btn:hover, .design-filter-btn.active { background: #3b82f6; border-color: #3b82f6; }

        .design-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }

        .design-card {
            background: #1e293b;
            border-radius: 14px;
            overflow: hidden;
            border: 1px solid #475569;
            transition: all 0.3s;
        }

        .design-card:hover {
            transform: translateY(-4px);
            border-color: #3b82f6;
            box-shadow: 0 10px 30px rgba(59, 130, 246, 0.2);
        }

        .design-card-preview {
            height: 160px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .design-card-preview-text { font-size: 1.4rem; font-weight: 600; text-align: center; padding: 15px; }

        .design-card-body { padding: 18px; }

        .design-card-category {
            display: inline-block;
            padding: 4px 10px;
            background: #3b82f6;
            color: white;
            border-radius: 15px;
            font-size: 0.75rem;
            margin-bottom: 8px;
        }

        .design-card-title { font-size: 1.2rem; font-weight: 600; margin-bottom: 10px; }

        .design-card-colors { display: flex; gap: 6px; margin-bottom: 12px; }

        .design-color-dot {
            width: 22px;
            height: 22px;
            border-radius: 50%;
            border: 2px solid rgba(255,255,255,0.2);
        }

        .design-card-actions {
            display: flex;
            gap: 8px;
            padding: 15px 18px;
            border-top: 1px solid #475569;
        }

        .design-btn {
            flex: 1;
            padding: 10px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 500;
            transition: all 0.2s;
        }

        .design-btn-copy { background: #3b82f6; color: white; }
        .design-btn-copy:hover { background: #60a5fa; }
        .design-btn-preview { background: #334155; color: #f1f5f9; border: 1px solid #475569; }
        .design-btn-preview:hover { background: #475569; }

        .design-no-results { text-align: center; padding: 50px 20px; color: #64748b; }
        .design-no-results h3 { font-size: 1.3rem; margin-bottom: 8px; color: #94a3b8; }

        /* 모달 */
        .design-modal-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.85);
            z-index: 1000;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .design-modal-overlay.active { display: flex; }

        .design-modal {
            background: #1e293b;
            border-radius: 16px;
            max-width: 950px;
            width: 100%;
            max-height: 90vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }

        .design-modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 25px;
            border-bottom: 1px solid #475569;
        }

        .design-modal-header h3 { font-size: 1.3rem; color: #f1f5f9; }

        .design-modal-close {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            border: none;
            background: #334155;
            color: #f1f5f9;
            font-size: 1.3rem;
            cursor: pointer;
        }

        .design-modal-close:hover { background: #475569; }

        .design-modal-content { display: flex; flex: 1; overflow: hidden; }

        .design-modal-preview-area {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 30px;
        }

        .design-preview-slide {
            width: 100%;
            aspect-ratio: 16/9;
            border-radius: 10px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 30px;
        }

        .design-preview-title { font-size: 1.8rem; font-weight: 700; text-align: center; margin-bottom: 15px; }
        .design-preview-subtitle { font-size: 1.1rem; opacity: 0.8; text-align: center; }

        .design-modal-prompt-area {
            flex: 1;
            padding: 25px;
            background: #334155;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .design-prompt-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }

        .design-prompt-header h4 { font-size: 1rem; color: #f1f5f9; }

        .design-prompt-text {
            flex: 1;
            background: #0f172a;
            border-radius: 10px;
            padding: 18px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.85rem;
            line-height: 1.6;
            overflow-y: auto;
            white-space: pre-wrap;
            color: #94a3b8;
        }

        .design-copy-toast {
            position: fixed;
            bottom: 25px;
            left: 50%;
            transform: translateX(-50%);
            background: #22c55e;
            color: white;
            padding: 12px 25px;
            border-radius: 25px;
            font-weight: 500;
            display: none;
            z-index: 2000;
        }

        .design-copy-toast.show { display: block; animation: toastSlide 0.3s ease; }

        @keyframes toastSlide {
            from { opacity: 0; transform: translateX(-50%) translateY(15px); }
            to { opacity: 1; transform: translateX(-50%) translateY(0); }
        }

        footer {
            background: #2d3748;
            color: white;
            text-align: center;
            padding: 30px;
        }

        @media (max-width: 768px) {
            header h1 { font-size: 1.8em; }
            .tab-btn { padding: 10px 16px; font-size: 0.9rem; }
            .guide-content { padding: 20px; }
            section { padding: 20px; }
            .design-modal-content { flex-direction: column; }
            .design-modal-preview-area, .design-modal-prompt-area { flex: none; }
            .design-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚀 Vibe 코딩 완벽 가이드 + 디자인 100</h1>
            <p>AI와 함께하는 현대적인 개발 환경 + NotebookLM 슬라이드 프롬프트</p>
        </header>

        <!-- 메인 탭 네비게이션 -->
        <div class="tab-nav">
            <button class="tab-btn active" onclick="showTab('guide')">📚 Vibe 코딩 가이드</button>
            <button class="tab-btn" onclick="showTab('design')">🎨 디자인 100 프롬프트</button>
        </div>

        <!-- 가이드 탭 -->
        <div id="tab-guide" class="tab-content active">
            <div class="guide-content">
                <nav class="section-nav">
                    <ul>
                        <li><a href="#step1">🌐 Antigravity</a></li>
                        <li><a href="#step2">🤖 Claude Code</a></li>
                        <li><a href="#step3">🔐 OAuth 인증</a></li>
                        <li><a href="#step4">⚙️ CLI 도구들</a></li>
                        <li><a href="#step5">💪 Skills MCP</a></li>
                        <li><a href="#step6">🔌 MCP 서버들</a></li>
                        <li><a href="#step7">💻 OpenCode</a></li>
                        <li><a href="#step8">🐙 GitHub</a></li>
                    </ul>
                </nav>

                <!-- Step 1: Antigravity -->
                <section id="step1">
                    <h2><span class="step-number">1</span> Antigravity를 IDE로 사용하기</h2>
                    <div class="info-box">
                        <h3>🌐 Antigravity (Google IDX)란?</h3>
                        <p><strong>Antigravity</strong>는 Google에서 제공하는 클라우드 기반 개발 환경입니다. 브라우저만 있으면 어디서든 코딩할 수 있는 강력한 IDE입니다.</p>
                    </div>
                    <h3>✨ 주요 특징</h3>
                    <ul>
                        <li><strong>완전 클라우드 기반</strong>: 설치 없이 브라우저에서 바로 사용</li>
                        <li><strong>Google 통합</strong>: Firebase, Google Cloud와 완벽 연동</li>
                        <li><strong>AI 지원</strong>: Gemini AI가 내장</li>
                        <li><strong>무료 사용</strong>: Google 계정만 있으면 무료</li>
                    </ul>
                    <h3>🚀 시작하기</h3>
                    <div class="code-block">1. Google 계정으로 로그인
2. idx.google.com 접속
3. "New Workspace" 클릭
4. 원하는 템플릿 선택
5. 프로젝트 이름 입력 후 생성</div>
                    <a href="https://idx.google.com" class="link-button" target="_blank">🔗 Antigravity 바로가기</a>
                </section>

                <!-- Step 2: Claude Code -->
                <section id="step2">
                    <h2><span class="step-number">2</span> Claude Code를 메인 코더로 사용하기</h2>
                    <div class="info-box">
                        <h3>🤖 Claude Code란?</h3>
                        <p><strong>Claude Code</strong>는 Anthropic에서 만든 AI 코딩 어시스턴트입니다. 터미널에서 자연어로 대화하면서 코드를 작성할 수 있습니다.</p>
                    </div>
                    <h3>📦 설치 방법</h3>
                    <div class="code-block"># npm을 통한 설치
npm install -g @anthropic-ai/claude-code

# 설치 확인
claude-code --version</div>
                    <a href="https://docs.anthropic.com/en/docs/build-with-claude/claude-code" class="link-button" target="_blank">🔗 Claude Code 문서</a>
                </section>

                <!-- Step 3: OAuth -->
                <section id="step3">
                    <h2><span class="step-number">3</span> Claude OAuth 인증 설정하기</h2>
                    <div class="info-box">
                        <h3>🔐 OAuth 인증이란?</h3>
                        <p>브라우저에서 인증하면 터미널에서 Claude를 사용할 수 있는 안전한 로그인 방식입니다.</p>
                    </div>
                    <h3>🔑 OAuth 인증 진행하기</h3>
                    <div class="code-block"># 1. 터미널에서 Claude Code 실행
claude-code

# 2. 표시된 URL을 브라우저에서 열기
# 3. Claude 계정으로 로그인
# 4. "Authorize" 클릭</div>
                    <a href="https://claude.ai" class="link-button" target="_blank">🔗 Claude 계정 만들기</a>
                </section>

                <!-- Step 4: CLI -->
                <section id="step4">
                    <h2><span class="step-number">4</span> CLI 도구들 설치하기</h2>
                    <div class="info-box">
                        <h3>⚙️ 필수 CLI 도구들</h3>
                        <p>터미널에서 다양한 서비스를 관리할 수 있는 도구들입니다.</p>
                    </div>
                    <div class="code-block"># Gemini CLI
npm install -g @google/generative-ai-cli

# gcloud CLI
curl https://sdk.cloud.google.com | bash

# Firebase CLI
npm install -g firebase-tools

# Vercel CLI
npm install -g vercel</div>
                </section>

                <!-- Step 5: Skills MCP -->
                <section id="step5">
                    <h2><span class="step-number">5</span> Skills MCP로 모든 스킬 활용하기</h2>
                    <div class="info-box">
                        <h3>💪 Skills MCP란?</h3>
                        <p>AI에게 특별한 능력을 부여하는 시스템입니다. 문서 작성, 이미지 생성 등 다양한 작업을 수행할 수 있습니다.</p>
                    </div>
                    <div class="mcp-grid">
                        <div class="mcp-card"><h4>📝 문서 스킬</h4><p>Office 문서 자동 생성</p></div>
                        <div class="mcp-card"><h4>🎨 디자인 스킬</h4><p>이미지 생성, 편집</p></div>
                        <div class="mcp-card"><h4>📊 데이터 스킬</h4><p>데이터 분석, 시각화</p></div>
                        <div class="mcp-card"><h4>🌐 웹 스킬</h4><p>웹 스크래핑, API 호출</p></div>
                    </div>
                    <a href="https://skillsmp.com" class="link-button" target="_blank">🔗 Skills MCP 사이트</a>
                </section>

                <!-- Step 6: MCP Servers -->
                <section id="step6">
                    <h2><span class="step-number">6</span> 필수 MCP 서버들 설치하기</h2>
                    <div class="info-box">
                        <h3>🔌 MCP란?</h3>
                        <p>AI가 다양한 도구와 서비스를 사용할 수 있게 해주는 연결 프로토콜입니다.</p>
                    </div>
                    <div class="mcp-grid">
                        <div class="mcp-card"><h4>🎭 Playwright MCP</h4><p>브라우저 자동화</p></div>
                        <div class="mcp-card"><h4>🥷 Stealth MCP</h4><p>봇 감지 우회</p></div>
                        <div class="mcp-card"><h4>🧵 Google Stitch</h4><p>Google 서비스 통합</p></div>
                        <div class="mcp-card"><h4>🧠 Context7</h4><p>컨텍스트 관리</p></div>
                    </div>
                </section>

                <!-- Step 7: OpenCode -->
                <section id="step7">
                    <h2><span class="step-number">7</span> OpenCode로 터미널 강화하기</h2>
                    <div class="info-box">
                        <h3>💻 OpenCode란?</h3>
                        <p>터미널을 더 아름답고 강력하게 만들어주는 도구입니다.</p>
                    </div>
                    <div class="code-block"># OpenCode 설치
curl -fsSL https://raw.githubusercontent.com/opencode/install/main/install.sh | sh

# Oh My OpenCode 설치
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyopencode/install/master/install.sh)"</div>
                </section>

                <!-- Step 8: GitHub -->
                <section id="step8">
                    <h2><span class="step-number">8</span> GitHub으로 코드 관리하기</h2>
                    <div class="info-box">
                        <h3>🐙 GitHub란?</h3>
                        <p>세계 최대의 코드 저장소 플랫폼입니다.</p>
                    </div>
                    <h3>⚙️ Git 설정하기</h3>
                    <div class="code-block"># Git 사용자 정보 설정
git config --global user.name "Your Name"
git config --global user.email "your.email@gmail.com"

# 기본 명령어
git add .
git commit -m "메시지"
git push</div>
                    <a href="https://github.com" class="link-button" target="_blank">🔗 GitHub 가입하기</a>
                </section>

                <!-- 마무리 -->
                <section style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none;">
                    <h2 style="color: white;">🎉 모든 설정 완료!</h2>
                    <div style="background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; margin: 20px 0;">
                        <p style="font-size: 1.2em;">이제 AI와 함께 코딩을 시작할 준비가 되었습니다!</p>
                        <p style="margin-top: 10px;">💡 "디자인 100 프롬프트" 탭에서 NotebookLM 슬라이드 스타일도 확인하세요!</p>
                    </div>
                </section>
            </div>
        </div>

        <!-- 디자인 100 탭 -->
        <div id="tab-design" class="tab-content">
            <div class="design-content">
                <div class="design-header">
                    <h2>🎨 슬라이드 프롬프트 뷰어</h2>
                    <p>NotebookLM 슬라이드 디자인을 위한 100개 프롬프트 컬렉션</p>
                    <div class="design-stats">
                        <div class="design-stat">
                            <div class="design-stat-num" id="totalStyles">100</div>
                            <div class="design-stat-label">전체 스타일</div>
                        </div>
                        <div class="design-stat">
                            <div class="design-stat-num" id="totalCategories">12</div>
                            <div class="design-stat-label">카테고리</div>
                        </div>
                        <div class="design-stat">
                            <div class="design-stat-num" id="filteredStyles">100</div>
                            <div class="design-stat-label">표시 중</div>
                        </div>
                    </div>
                </div>

                <div class="design-container">
                    <div class="design-search">
                        <input type="text" id="designSearchInput" placeholder="스타일 검색... (예: 네온, 미니멀, 의료)">
                    </div>

                    <div class="design-filters" id="designFilters">
                        <button class="design-filter-btn active" data-category="all">전체</button>
                    </div>

                    <div class="design-grid" id="designGrid"></div>
                    <div class="design-no-results" id="designNoResults" style="display: none;">
                        <h3>검색 결과가 없습니다</h3>
                        <p>다른 검색어를 시도해보세요</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- 디자인 모달 -->
        <div class="design-modal-overlay" id="designModal">
            <div class="design-modal">
                <div class="design-modal-header">
                    <h3 id="designModalTitle">스타일 이름</h3>
                    <button class="design-modal-close" onclick="closeDesignModal()">×</button>
                </div>
                <div class="design-modal-content">
                    <div class="design-modal-preview-area">
                        <div class="design-preview-slide" id="designPreviewSlide">
                            <div class="design-preview-title" id="designPreviewTitle">제목</div>
                            <div class="design-preview-subtitle" id="designPreviewSubtitle">부제목</div>
                        </div>
                    </div>
                    <div class="design-modal-prompt-area">
                        <div class="design-prompt-header">
                            <h4>프롬프트</h4>
                            <button class="design-btn design-btn-copy" onclick="copyCurrentDesignPrompt()">복사하기</button>
                        </div>
                        <div class="design-prompt-text" id="designPromptText"></div>
                    </div>
                </div>
            </div>
        </div>

        <div class="design-copy-toast" id="designCopyToast">프롬프트가 클립보드에 복사되었습니다!</div>

        <footer>
            <p style="margin-bottom: 10px;">💜 Made with Love</p>
            <p style="opacity: 0.8;">Vibe 코딩 가이드 + 디자인 100 프롬프트 🚀</p>
            <p style="opacity: 0.6; margin-top: 15px; font-size: 0.9em;">© 2024-2026 | 마지막 업데이트: ''' + datetime.now().strftime('%Y년 %m월') + '''</p>
        </footer>
    </div>

    <script>
        // 탭 전환
        function showTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById('tab-' + tabName).classList.add('active');
            event.target.classList.add('active');
        }

        // 부드러운 스크롤
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
        });

        // 코드 블록 복사 버튼
        document.querySelectorAll('.code-block').forEach(block => {
            const btn = document.createElement('button');
            btn.textContent = '📋 복사';
            btn.style.cssText = 'position:absolute;top:8px;right:8px;background:#667eea;color:white;border:none;padding:5px 12px;border-radius:5px;cursor:pointer;font-size:0.85em;';
            block.appendChild(btn);
            btn.onclick = () => {
                navigator.clipboard.writeText(block.textContent.replace('📋 복사', '').trim());
                btn.textContent = '✅ 복사됨!';
                setTimeout(() => btn.textContent = '📋 복사', 2000);
            };
        });

        // 디자인 100 데이터
        const DESIGN_DATA = ''' + prompts_json + ''';
        const designStyles = DESIGN_DATA.styles;
        let currentDesignStyle = null;

        function initDesign() {
            createDesignFilters();
            renderDesignCards(designStyles);
            setupDesignListeners();
        }

        function createDesignFilters() {
            const categories = [...new Set(designStyles.map(s => s.category))];
            const container = document.getElementById('designFilters');
            categories.forEach(cat => {
                const count = designStyles.filter(s => s.category === cat).length;
                const btn = document.createElement('button');
                btn.className = 'design-filter-btn';
                btn.dataset.category = cat;
                btn.textContent = cat + ' (' + count + ')';
                container.appendChild(btn);
            });
            document.getElementById('totalCategories').textContent = categories.length;
        }

        function parseDesignColors(prompt) {
            const colors = { background: '#1e293b', text: '#f1f5f9', accent: '#3b82f6' };
            const bg = prompt.match(/배경:\\s*(#[A-Fa-f0-9]{6})/);
            const txt = prompt.match(/텍스트:\\s*(#[A-Fa-f0-9]{6})/);
            const acc = prompt.match(/강조:\\s*(#[A-Fa-f0-9]{6})/);
            if (bg) colors.background = bg[1];
            if (txt) colors.text = txt[1];
            if (acc) colors.accent = acc[1];
            return colors;
        }

        function renderDesignCards(styles) {
            const grid = document.getElementById('designGrid');
            const noResults = document.getElementById('designNoResults');
            if (styles.length === 0) {
                grid.innerHTML = '';
                noResults.style.display = 'block';
                return;
            }
            noResults.style.display = 'none';
            grid.innerHTML = styles.map(style => {
                const colors = parseDesignColors(style.prompt);
                return '<div class="design-card">' +
                    '<div class="design-card-preview" style="background:' + colors.background + '">' +
                    '<div class="design-card-preview-text" style="color:' + colors.text + '">' + style.name + '</div></div>' +
                    '<div class="design-card-body">' +
                    '<span class="design-card-category">' + style.category + '</span>' +
                    '<h4 class="design-card-title">' + style.name + '</h4>' +
                    '<div class="design-card-colors">' +
                    '<div class="design-color-dot" style="background:' + colors.background + '" title="배경색"></div>' +
                    '<div class="design-color-dot" style="background:' + colors.text + '" title="텍스트색"></div>' +
                    '<div class="design-color-dot" style="background:' + colors.accent + '" title="강조색"></div></div></div>' +
                    '<div class="design-card-actions">' +
                    '<button class="design-btn design-btn-copy" onclick="copyDesignPrompt(event,' + style.index + ')">복사</button>' +
                    '<button class="design-btn design-btn-preview" onclick="openDesignModal(' + style.index + ')">프리뷰</button></div></div>';
            }).join('');
            document.getElementById('filteredStyles').textContent = styles.length;
        }

        function setupDesignListeners() {
            document.getElementById('designFilters').addEventListener('click', e => {
                if (e.target.classList.contains('design-filter-btn')) {
                    document.querySelectorAll('.design-filter-btn').forEach(b => b.classList.remove('active'));
                    e.target.classList.add('active');
                    filterDesignStyles();
                }
            });
            document.getElementById('designSearchInput').addEventListener('input', filterDesignStyles);
            document.getElementById('designModal').addEventListener('click', e => {
                if (e.target.id === 'designModal') closeDesignModal();
            });
            document.addEventListener('keydown', e => { if (e.key === 'Escape') closeDesignModal(); });
        }

        function filterDesignStyles() {
            const category = document.querySelector('.design-filter-btn.active').dataset.category;
            const search = document.getElementById('designSearchInput').value.toLowerCase();
            let filtered = designStyles;
            if (category !== 'all') filtered = filtered.filter(s => s.category === category);
            if (search) filtered = filtered.filter(s =>
                s.name.toLowerCase().includes(search) ||
                s.category.toLowerCase().includes(search) ||
                s.prompt.toLowerCase().includes(search)
            );
            renderDesignCards(filtered);
        }

        function copyDesignPrompt(event, index) {
            event.stopPropagation();
            const style = designStyles.find(s => s.index === index);
            if (style) { navigator.clipboard.writeText(style.prompt); showDesignCopyToast(); }
        }

        function copyCurrentDesignPrompt() {
            if (currentDesignStyle) { navigator.clipboard.writeText(currentDesignStyle.prompt); showDesignCopyToast(); }
        }

        function showDesignCopyToast() {
            const toast = document.getElementById('designCopyToast');
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 2000);
        }

        function openDesignModal(index) {
            currentDesignStyle = designStyles.find(s => s.index === index);
            if (!currentDesignStyle) return;
            const colors = parseDesignColors(currentDesignStyle.prompt);
            document.getElementById('designModalTitle').textContent = currentDesignStyle.name + ' (' + currentDesignStyle.category + ')';
            document.getElementById('designPromptText').textContent = currentDesignStyle.prompt;
            const slide = document.getElementById('designPreviewSlide');
            slide.style.background = colors.background;
            document.getElementById('designPreviewTitle').style.color = colors.text;
            document.getElementById('designPreviewTitle').textContent = currentDesignStyle.name;
            document.getElementById('designPreviewSubtitle').style.color = colors.accent;
            document.getElementById('designPreviewSubtitle').textContent = currentDesignStyle.category + ' 스타일';
            document.getElementById('designModal').classList.add('active');
            document.body.style.overflow = 'hidden';
        }

        function closeDesignModal() {
            document.getElementById('designModal').classList.remove('active');
            document.body.style.overflow = '';
            currentDesignStyle = null;
        }

        initDesign();
    </script>
</body>
</html>'''

# 3. 파일 저장
output_dir = 'G:/내 드라이브/notebooklm/vibe-coding-complete'
os.makedirs(output_dir, exist_ok=True)

html_path = os.path.join(output_dir, 'vibe-coding-complete-guide.html')
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"[OK] HTML created: {html_path}")

# 4. 사용 설명서 생성
readme_content = '''# 📚 Vibe 코딩 완벽 가이드 + 디자인 100

## 📁 파일 구성
- `vibe-coding-complete-guide.html` - 메인 웹앱 (단독 실행 가능)
- `README.txt` - 이 사용 설명서

## 🚀 사용 방법

### 1. 파일 열기
`vibe-coding-complete-guide.html` 파일을 더블클릭하면 브라우저에서 열립니다.
인터넷 연결 없이도 사용 가능합니다 (오프라인 지원).

### 2. 탭 구성
- **📚 Vibe 코딩 가이드**: AI 개발 환경 설정 가이드 (8단계)
- **🎨 디자인 100 프롬프트**: NotebookLM 슬라이드 스타일 100개

### 3. Vibe 코딩 가이드 사용법
1. 상단 네비게이션에서 원하는 섹션 클릭
2. 각 섹션의 코드 블록에서 "📋 복사" 버튼으로 코드 복사
3. 링크 버튼으로 관련 사이트 바로가기

### 4. 디자인 100 프롬프트 사용법
1. **검색**: 상단 검색창에 스타일 이름 입력 (예: 네온, 미니멀)
2. **필터**: 카테고리 버튼으로 필터링 (심플, 모던, 비즈니스 등)
3. **복사**: 각 카드의 "복사" 버튼으로 프롬프트 즉시 복사
4. **프리뷰**: "프리뷰" 버튼으로 컬러 시스템 미리보기

### 5. NotebookLM에서 프롬프트 사용하기
1. 원하는 스타일의 프롬프트 복사
2. NotebookLM에서 슬라이드 생성 시 프롬프트 붙여넣기
3. AI가 해당 스타일로 슬라이드 디자인 생성

## 📊 포함된 스타일 카테고리 (12개, 총 100개)

| 카테고리 | 개수 | 예시 스타일 |
|---------|------|------------|
| 심플 | 8개 | 미니멀 젠, 노르딕, 클린 모던 |
| 모던 | 10개 | 글래스모피즘, 네온 느와르, 다크 모드 |
| 비즈니스 | 10개 | 메디컬 케어, 스타트업 피치, 컨설팅 |
| 내추럴 | 8개 | 포레스트, 딥 오션, 보타니컬 |
| 럭셔리 | 6개 | 골든 아워, 보그 에디토리얼 |
| 레트로 | 12개 | 신스웨이브, 8비트, VHS 글리치 |
| 크리에이티브 | 10개 | 모던 갤러리, 수채화, 스티커 팩 |
| 학술 | 6개 | 학술 논문, 사이언스 랩 |
| 카툰 | 8개 | 클레이 3D, 애니메이션, 웹툰 |
| 테크니컬 | 8개 | 인포그래픽, 대시보드 UI |
| 크래프트 | 6개 | 스케치북, 목판화 |
| 재미 | 8개 | 1급 기밀, 윈도우 95, 밈 템플릿 |

## 💡 추천 스타일

### 의료/헬스케어 발표
- 메디컬 케어 (비즈니스)
- 사이언스 랩 (학술)
- 클린 모던 (심플)

### 비즈니스 프레젠테이션
- 코퍼레이트 (비즈니스)
- 스타트업 피치 (비즈니스)
- 컨설팅 리포트 (비즈니스)

### 크리에이티브/마케팅
- 비비드 팝 (크리에이티브)
- 네온 퓨처 (모던)
- 글래스모피즘 (모던)

### 친근한/교육용
- 클레이 3D (카툰)
- 두들 낙서 (카툰)
- 어린이 그림 (재미)

---
📅 생성일: ''' + datetime.now().strftime('%Y년 %m월 %d일') + '''
💜 Made with Love
'''

readme_path = os.path.join(output_dir, 'README.txt')
with open(readme_path, 'w', encoding='utf-8') as f:
    f.write(readme_content)

print(f"[OK] 사용 설명서 생성: {readme_path}")

# 5. ZIP 압축
zip_path = 'G:/내 드라이브/notebooklm/vibe-coding-complete-guide.zip'
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    zipf.write(html_path, 'vibe-coding-complete-guide.html')
    zipf.write(readme_path, 'README.txt')

print(f"[OK] ZIP 파일 생성: {zip_path}")
print(f"\n[DONE] Files created:")
print(f"   Folder: {output_dir}")
print(f"   ZIP: {zip_path}")
