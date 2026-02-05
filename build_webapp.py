import json

# Read JSON
with open('G:/내 드라이브/notebooklm/slide-prompt-viewer/slide_prompts.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Convert to JS
js_data = json.dumps(data, ensure_ascii=False)

html_template = '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>슬라이드 프롬프트 뷰어 - 100개 디자인 스타일</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #334155;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --accent: #3b82f6;
            --accent-hover: #60a5fa;
            --success: #22c55e;
            --border: #475569;
        }
        body {
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
        }
        .container { max-width: 1600px; margin: 0 auto; padding: 20px; }
        header {
            text-align: center;
            padding: 40px 20px;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border-bottom: 1px solid var(--border);
            margin-bottom: 30px;
        }
        header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        header p { color: var(--text-secondary); font-size: 1.1rem; }
        .stats { display: flex; justify-content: center; gap: 30px; margin-top: 20px; flex-wrap: wrap; }
        .stat-item { background: var(--bg-card); padding: 15px 25px; border-radius: 12px; text-align: center; }
        .stat-number { font-size: 2rem; font-weight: 700; color: var(--accent); }
        .stat-label { font-size: 0.9rem; color: var(--text-secondary); }
        .filters {
            display: flex; flex-wrap: wrap; gap: 10px; justify-content: center;
            margin-bottom: 30px; padding: 20px; background: var(--bg-secondary); border-radius: 16px;
        }
        .filter-btn {
            padding: 10px 20px; border: 1px solid var(--border); background: var(--bg-card);
            color: var(--text-primary); border-radius: 25px; cursor: pointer; transition: all 0.2s; font-size: 0.95rem;
        }
        .filter-btn:hover, .filter-btn.active { background: var(--accent); border-color: var(--accent); }
        .search-box { display: flex; justify-content: center; margin-bottom: 30px; }
        .search-box input {
            width: 100%; max-width: 500px; padding: 15px 25px; border: 2px solid var(--border);
            background: var(--bg-secondary); color: var(--text-primary); border-radius: 30px;
            font-size: 1rem; outline: none; transition: border-color 0.2s;
        }
        .search-box input:focus { border-color: var(--accent); }
        .search-box input::placeholder { color: var(--text-secondary); }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; }
        .card {
            background: var(--bg-secondary); border-radius: 16px; overflow: hidden;
            border: 1px solid var(--border); transition: all 0.3s;
        }
        .card:hover {
            transform: translateY(-5px); border-color: var(--accent);
            box-shadow: 0 10px 40px rgba(59, 130, 246, 0.2);
        }
        .card-preview {
            height: 180px; display: flex; align-items: center; justify-content: center;
            position: relative; overflow: hidden;
        }
        .card-preview-text { font-size: 1.5rem; font-weight: 600; text-align: center; padding: 20px; z-index: 1; }
        .card-body { padding: 20px; }
        .card-category {
            display: inline-block; padding: 5px 12px; background: var(--accent);
            color: white; border-radius: 20px; font-size: 0.8rem; margin-bottom: 10px;
        }
        .card-title { font-size: 1.3rem; font-weight: 600; margin-bottom: 10px; }
        .card-colors { display: flex; gap: 8px; margin-bottom: 15px; }
        .color-dot { width: 24px; height: 24px; border-radius: 50%; border: 2px solid rgba(255,255,255,0.2); }
        .card-meta { display: flex; justify-content: space-between; align-items: center; color: var(--text-secondary); font-size: 0.9rem; }
        .card-actions { display: flex; gap: 10px; padding: 15px 20px; border-top: 1px solid var(--border); }
        .btn {
            flex: 1; padding: 12px; border: none; border-radius: 8px; cursor: pointer;
            font-size: 0.9rem; font-weight: 500; transition: all 0.2s;
        }
        .btn-copy { background: var(--accent); color: white; }
        .btn-copy:hover { background: var(--accent-hover); }
        .btn-preview { background: var(--bg-card); color: var(--text-primary); border: 1px solid var(--border); }
        .btn-preview:hover { background: var(--border); }
        .modal-overlay {
            display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.8); z-index: 1000; align-items: center;
            justify-content: center; padding: 20px;
        }
        .modal-overlay.active { display: flex; }
        .modal {
            background: var(--bg-secondary); border-radius: 20px; max-width: 1000px;
            width: 100%; max-height: 90vh; overflow: hidden; display: flex; flex-direction: column;
        }
        .modal-header {
            display: flex; justify-content: space-between; align-items: center;
            padding: 25px 30px; border-bottom: 1px solid var(--border);
        }
        .modal-header h2 { font-size: 1.5rem; }
        .modal-close {
            width: 40px; height: 40px; border-radius: 50%; border: none;
            background: var(--bg-card); color: var(--text-primary); font-size: 1.5rem;
            cursor: pointer; transition: background 0.2s;
        }
        .modal-close:hover { background: var(--border); }
        .modal-content { display: flex; flex: 1; overflow: hidden; }
        .modal-preview { flex: 1; display: flex; align-items: center; justify-content: center; padding: 40px; }
        .preview-slide {
            width: 100%; aspect-ratio: 16/9; border-radius: 12px; display: flex;
            flex-direction: column; align-items: center; justify-content: center;
            padding: 40px; position: relative; overflow: hidden;
        }
        .preview-title { font-size: 2rem; font-weight: 700; text-align: center; margin-bottom: 20px; z-index: 1; }
        .preview-subtitle { font-size: 1.2rem; opacity: 0.8; text-align: center; z-index: 1; }
        .modal-prompt {
            flex: 1; padding: 30px; background: var(--bg-card);
            display: flex; flex-direction: column; overflow: hidden;
        }
        .prompt-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        .prompt-header h3 { font-size: 1.1rem; }
        .prompt-text {
            flex: 1; background: var(--bg-primary); border-radius: 12px; padding: 20px;
            font-family: 'Consolas', 'Monaco', monospace; font-size: 0.9rem; line-height: 1.6;
            overflow-y: auto; white-space: pre-wrap; color: var(--text-secondary);
        }
        .copy-success {
            position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%);
            background: var(--success); color: white; padding: 15px 30px; border-radius: 30px;
            font-weight: 500; display: none; z-index: 2000;
        }
        .copy-success.show { display: block; animation: slideUp 0.3s ease; }
        @keyframes slideUp {
            from { opacity: 0; transform: translateX(-50%) translateY(20px); }
            to { opacity: 1; transform: translateX(-50%) translateY(0); }
        }
        .no-results { text-align: center; padding: 60px 20px; color: var(--text-secondary); }
        .no-results h3 { font-size: 1.5rem; margin-bottom: 10px; }
        @media (max-width: 768px) {
            header h1 { font-size: 1.8rem; }
            .stats { flex-direction: column; align-items: center; }
            .modal-content { flex-direction: column; }
            .modal-preview, .modal-prompt { flex: none; }
            .modal-preview { padding: 20px; }
            .preview-title { font-size: 1.5rem; }
            .grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <header>
        <h1>슬라이드 프롬프트 뷰어</h1>
        <p>NotebookLM 슬라이드 디자인을 위한 100개 프롬프트 컬렉션</p>
        <div class="stats">
            <div class="stat-item">
                <div class="stat-number" id="totalCount">100</div>
                <div class="stat-label">전체 스타일</div>
            </div>
            <div class="stat-item">
                <div class="stat-number" id="categoryCount">12</div>
                <div class="stat-label">카테고리</div>
            </div>
            <div class="stat-item">
                <div class="stat-number" id="filteredCount">100</div>
                <div class="stat-label">표시 중</div>
            </div>
        </div>
    </header>
    <div class="container">
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="스타일 이름으로 검색... (예: 네온, 미니멀, 의료)">
        </div>
        <div class="filters" id="filters">
            <button class="filter-btn active" data-category="all">전체</button>
        </div>
        <div class="grid" id="grid"></div>
        <div class="no-results" id="noResults" style="display: none;">
            <h3>검색 결과가 없습니다</h3>
            <p>다른 검색어를 시도해보세요</p>
        </div>
    </div>
    <div class="modal-overlay" id="modal">
        <div class="modal">
            <div class="modal-header">
                <h2 id="modalTitle">스타일 이름</h2>
                <button class="modal-close" onclick="closeModal()">×</button>
            </div>
            <div class="modal-content">
                <div class="modal-preview">
                    <div class="preview-slide" id="previewSlide">
                        <div class="preview-title" id="previewTitle">제목 예시</div>
                        <div class="preview-subtitle" id="previewSubtitle">부제목 텍스트</div>
                    </div>
                </div>
                <div class="modal-prompt">
                    <div class="prompt-header">
                        <h3>프롬프트</h3>
                        <button class="btn btn-copy" onclick="copyCurrentPrompt()">복사하기</button>
                    </div>
                    <div class="prompt-text" id="promptText"></div>
                </div>
            </div>
        </div>
    </div>
    <div class="copy-success" id="copySuccess">프롬프트가 클립보드에 복사되었습니다!</div>
    <script>
        const DATA = ''' + js_data + ''';
        const stylesData = DATA.styles;
        let currentStyle = null;

        function init() {
            createFilters();
            renderCards(stylesData);
            setupEventListeners();
            updateStats();
        }

        function createFilters() {
            const categories = [...new Set(stylesData.map(s => s.category))];
            const filtersContainer = document.getElementById('filters');
            categories.forEach(cat => {
                const count = stylesData.filter(s => s.category === cat).length;
                const btn = document.createElement('button');
                btn.className = 'filter-btn';
                btn.dataset.category = cat;
                btn.textContent = cat + ' (' + count + ')';
                filtersContainer.appendChild(btn);
            });
            document.getElementById('categoryCount').textContent = categories.length;
        }

        function parseColors(prompt) {
            const colors = { background: '#1e293b', text: '#f1f5f9', accent: '#3b82f6' };
            const bgMatch = prompt.match(/배경:\\s*(#[A-Fa-f0-9]{6})/);
            const textMatch = prompt.match(/텍스트:\\s*(#[A-Fa-f0-9]{6})/);
            const accentMatch = prompt.match(/강조:\\s*(#[A-Fa-f0-9]{6})/);
            if (bgMatch) colors.background = bgMatch[1];
            if (textMatch) colors.text = textMatch[1];
            if (accentMatch) colors.accent = accentMatch[1];
            return colors;
        }

        function parseFont(prompt) {
            const fontMatch = prompt.match(/폰트:\\s*([^\\n]+)/);
            return fontMatch ? fontMatch[1].trim() : 'sans-serif';
        }

        function renderCards(styles) {
            const grid = document.getElementById('grid');
            const noResults = document.getElementById('noResults');
            if (styles.length === 0) {
                grid.innerHTML = '';
                noResults.style.display = 'block';
                return;
            }
            noResults.style.display = 'none';
            grid.innerHTML = styles.map(style => {
                const colors = parseColors(style.prompt);
                return '<div class="card" data-index="' + style.index + '">' +
                    '<div class="card-preview" style="background:' + colors.background + '">' +
                    '<div class="card-preview-text" style="color:' + colors.text + '">' + style.name + '</div></div>' +
                    '<div class="card-body">' +
                    '<span class="card-category">' + style.category + '</span>' +
                    '<h3 class="card-title">' + style.name + '</h3>' +
                    '<div class="card-colors">' +
                    '<div class="color-dot" style="background:' + colors.background + '" title="배경색"></div>' +
                    '<div class="color-dot" style="background:' + colors.text + '" title="텍스트색"></div>' +
                    '<div class="color-dot" style="background:' + colors.accent + '" title="강조색"></div></div>' +
                    '<div class="card-meta"><span>#' + style.index + '</span></div></div>' +
                    '<div class="card-actions">' +
                    '<button class="btn btn-copy" onclick="copyPrompt(event,' + style.index + ')">복사</button>' +
                    '<button class="btn btn-preview" onclick="openModal(' + style.index + ')">프리뷰</button></div></div>';
            }).join('');
            document.getElementById('filteredCount').textContent = styles.length;
        }

        function setupEventListeners() {
            document.getElementById('filters').addEventListener('click', (e) => {
                if (e.target.classList.contains('filter-btn')) {
                    document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
                    e.target.classList.add('active');
                    filterStyles();
                }
            });
            document.getElementById('searchInput').addEventListener('input', filterStyles);
            document.getElementById('modal').addEventListener('click', (e) => {
                if (e.target.id === 'modal') closeModal();
            });
            document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });
        }

        function filterStyles() {
            const category = document.querySelector('.filter-btn.active').dataset.category;
            const search = document.getElementById('searchInput').value.toLowerCase();
            let filtered = stylesData;
            if (category !== 'all') filtered = filtered.filter(s => s.category === category);
            if (search) filtered = filtered.filter(s =>
                s.name.toLowerCase().includes(search) ||
                s.category.toLowerCase().includes(search) ||
                s.prompt.toLowerCase().includes(search)
            );
            renderCards(filtered);
        }

        function updateStats() { document.getElementById('totalCount').textContent = stylesData.length; }

        function copyPrompt(event, index) {
            event.stopPropagation();
            const style = stylesData.find(s => s.index === index);
            if (style) { navigator.clipboard.writeText(style.prompt); showCopySuccess(); }
        }

        function copyCurrentPrompt() {
            if (currentStyle) { navigator.clipboard.writeText(currentStyle.prompt); showCopySuccess(); }
        }

        function showCopySuccess() {
            const toast = document.getElementById('copySuccess');
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 2000);
        }

        function openModal(index) {
            currentStyle = stylesData.find(s => s.index === index);
            if (!currentStyle) return;
            const colors = parseColors(currentStyle.prompt);
            const font = parseFont(currentStyle.prompt);
            document.getElementById('modalTitle').textContent = currentStyle.name + ' (' + currentStyle.category + ')';
            document.getElementById('promptText').textContent = currentStyle.prompt;
            const previewSlide = document.getElementById('previewSlide');
            previewSlide.style.background = colors.background;
            previewSlide.style.fontFamily = font + ', sans-serif';
            document.getElementById('previewTitle').style.color = colors.text;
            document.getElementById('previewTitle').textContent = currentStyle.name;
            document.getElementById('previewSubtitle').style.color = colors.accent;
            document.getElementById('previewSubtitle').textContent = currentStyle.category + ' 스타일';
            document.getElementById('modal').classList.add('active');
            document.body.style.overflow = 'hidden';
        }

        function closeModal() {
            document.getElementById('modal').classList.remove('active');
            document.body.style.overflow = '';
            currentStyle = null;
        }

        init();
    </script>
</body>
</html>'''

# Write HTML
with open('G:/내 드라이브/notebooklm/slide-prompt-viewer/index.html', 'w', encoding='utf-8') as f:
    f.write(html_template)

print("Done! Created index.html with embedded data")
print(f"Total styles: {len(data['styles'])}")
