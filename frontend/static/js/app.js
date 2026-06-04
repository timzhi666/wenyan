/**
 * 文言文实词测试 - 主应用逻辑
 */

// ===== 全局状态 =====
let currentPage = 'home';
let libraryPage = 1;
let librarySearch = '';
let searchTimer = null;

let gameQuestions = [];
let gameCurrentIndex = 0;
let gameScore = 0;
let gameResults = [];  // [{word_id, is_correct}, ...]

let defCount = 1;  // 手工添加表单中的释义数量

// ===== 导航 =====
function navigateTo(page) {
    if (currentPage === page) return;
    currentPage = page;

    // 更新导航标签
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.page === page);
    });

    // 切换页面
    document.querySelectorAll('.page').forEach(p => {
        p.classList.toggle('active', p.id === `page-${page}`);
    });

    // 按需加载数据
    if (page === 'home') loadStats();
    if (page === 'library') loadLibrary();
    if (page === 'test') resetTestToReady();
}

document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', () => navigateTo(tab.dataset.page));
});

// ===== 首页 =====
async function loadStats() {
    try {
        const data = await API.getStats();
        animateNumber('word-count', data.word_count);
        animateNumber('history-count', data.history_count);
        animateNumber('game-count', data.game_count);
        animateNumber('perfect-count', data.perfect_count);
    } catch (e) {
        console.error('加载统计失败', e);
    }
}

function animateNumber(id, target) {
    const el = document.getElementById(id);
    if (!el) return;
    const start = parseInt(el.textContent) || 0;
    const diff = target - start;
    if (diff === 0) return;
    const duration = 600;
    const startTime = performance.now();
    function step(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const ease = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.round(start + diff * ease);
        if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}

function goToLibrary() {
    navigateTo('library');
}

function startTest() {
    navigateTo('test');
    // 如果在测试准备状态，直接开始
    setTimeout(() => {
        if (document.getElementById('test-ready').style.display !== 'none') {
            // 已经在准备状态，不自动开始
        }
    }, 100);
}

// ===== 游戏记录弹窗 =====
async function showGameRecords() {
    const modal = document.getElementById('records-modal');
    modal.style.display = 'flex';
    const listEl = document.getElementById('records-list');
    listEl.innerHTML = '<div class="loading-placeholder">加载中...</div>';

    try {
        const data = await API.getRecords();
        if (!data.records || data.records.length === 0) {
            listEl.innerHTML = '<div class="empty-placeholder"><div class="empty-icon">🎮</div><p>暂无游戏记录</p></div>';
            return;
        }

        listEl.innerHTML = data.records.map(r => {
            const correctWords = (r.correct_words || []).join('、') || '无';
            const wrongWords = (r.wrong_words || []).join('、') || '无';
            const perfectBadge = r.is_perfect ? '<span class="record-perfect-badge">🏆 全对</span>' : '';
            return `
                <div class="record-item">
                    <div class="record-header">
                        <span class="record-date">🕐 ${formatDate(r.played_at)}</span>
                        <div style="display:flex;align-items:center;gap:8px;">
                            ${perfectBadge}
                            <span class="record-score">${r.correct_count}/${r.total_questions}</span>
                        </div>
                    </div>
                    <div class="record-words">
                        <div class="record-word-section">
                            <div class="record-word-label">✅ 答对</div>
                            <div class="record-word-list correct-words">${correctWords}</div>
                        </div>
                        <div class="record-word-section">
                            <div class="record-word-label">❌ 答错</div>
                            <div class="record-word-list wrong-words">${wrongWords}</div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    } catch (e) {
        listEl.innerHTML = '<div class="empty-placeholder">加载失败</div>';
    }
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    // 格式: "2026-06-03 15:30:22"
    return dateStr.replace('T', ' ').substring(0, 16);
}

function closeModal(id) {
    document.getElementById(id).style.display = 'none';
}

// ===== 词库 =====
async function loadLibrary(page = 1, q = '') {
    libraryPage = page;
    librarySearch = q;

    const listEl = document.getElementById('word-list');
    listEl.innerHTML = '<div class="loading-placeholder">加载中...</div>';

    try {
        const data = await API.getWords(page, 15, q);
        document.getElementById('library-total').textContent =
            `共 ${data.total} 个实词${q ? `（搜索"${q}"）` : ''}`;

        if (!data.words || data.words.length === 0) {
            listEl.innerHTML = `
                <div class="empty-placeholder">
                    <div class="empty-icon">📚</div>
                    <p>${q ? '未找到匹配的实词' : '词库为空，快去添加实词吧！'}</p>
                </div>`;
            document.getElementById('pagination').innerHTML = '';
            return;
        }

        listEl.innerHTML = data.words.map(w => renderWordCard(w)).join('');
        renderPagination(data.total, page, 15);
    } catch (e) {
        listEl.innerHTML = '<div class="empty-placeholder">加载失败，请检查服务器状态</div>';
    }
}

function renderWordCard(word) {
    const definitionsHtml = word.definitions.map((d, i) => {
        const numMap = ['①', '②', '③', '④', '⑤'];
        const examplesHtml = (d.examples || []).map(ex => `
            <div class="example-item-display">
                <div class="ex-sentence">${ex.sentence}</div>
                <div class="ex-source-info">
                    ${ex.source_article ? `<span class="ex-source-tag">《${ex.source_article}》</span>` : ''}
                    ${ex.author ? `<span class="ex-source-tag">${ex.author}</span>` : ''}
                    ${ex.dynasty ? `<span class="ex-source-tag">${ex.dynasty}</span>` : ''}
                </div>
            </div>
        `).join('');

        return `
            <div class="definition-block">
                <div class="def-header">
                    <span class="def-index">${numMap[i] || (i + 1)}</span>
                    <span class="def-text">${escapeHtml(d.definition)}</span>
                </div>
                ${examplesHtml ? `<div class="example-list">${examplesHtml}</div>` : ''}
            </div>
        `;
    }).join('');

    return `
        <div class="word-card" id="word-card-${word.id}">
            <div class="word-card-header" onclick="toggleWordCard(${word.id})">
                <div class="word-card-left">
                    <span class="word-char">${escapeHtml(word.word)}</span>
                    <div class="word-stats">
                        <div class="word-stat-row">
                            <span class="word-stat-correct">✅ 答对 ${word.correct_count} 次</span>
                            <span class="word-stat-wrong">❌ 答错 ${word.wrong_count} 次</span>
                        </div>
                        <div class="word-stat-row">
                            <span style="color:var(--text-muted);font-size:12px;">${word.definitions.length} 个释义</span>
                        </div>
                    </div>
                </div>
                <div class="word-card-right">
                    <button class="btn-delete-word" onclick="event.stopPropagation(); deleteWord(${word.id}, '${escapeHtml(word.word)}')">删除</button>
                    <button class="word-expand-btn" id="expand-btn-${word.id}">▼</button>
                </div>
            </div>
            <div class="word-card-body" id="word-body-${word.id}">
                ${definitionsHtml || '<div style="color:var(--text-muted);font-size:14px;">暂无释义</div>'}
            </div>
        </div>
    `;
}

function toggleWordCard(wordId) {
    const body = document.getElementById(`word-body-${wordId}`);
    const btn = document.getElementById(`expand-btn-${wordId}`);
    const isExpanded = body.classList.contains('expanded');
    body.classList.toggle('expanded', !isExpanded);
    btn.classList.toggle('expanded', !isExpanded);
}

async function deleteWord(wordId, wordText) {
    if (!confirm(`确定要从词库中删除"${wordText}"吗？`)) return;
    try {
        await API.deleteWord(wordId);
        showToast(`已删除"${wordText}"`);
        loadLibrary(libraryPage, librarySearch);
        loadStats();
    } catch (e) {
        showToast('删除失败：' + e.message);
    }
}

function handleSearch(value) {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
        loadLibrary(1, value.trim());
    }, 400);
}

function renderPagination(total, currentPage, perPage) {
    const totalPages = Math.ceil(total / perPage);
    if (totalPages <= 1) {
        document.getElementById('pagination').innerHTML = '';
        return;
    }

    let html = '';
    if (currentPage > 1) {
        html += `<button class="page-btn" onclick="loadLibrary(${currentPage - 1}, '${escapeHtml(librarySearch)}')">‹ 上一页</button>`;
    }

    const start = Math.max(1, currentPage - 2);
    const end = Math.min(totalPages, currentPage + 2);
    for (let p = start; p <= end; p++) {
        html += `<button class="page-btn ${p === currentPage ? 'active' : ''}" onclick="loadLibrary(${p}, '${escapeHtml(librarySearch)}')">${p}</button>`;
    }

    if (currentPage < totalPages) {
        html += `<button class="page-btn" onclick="loadLibrary(${currentPage + 1}, '${escapeHtml(librarySearch)}')">下一页 ›</button>`;
    }

    document.getElementById('pagination').innerHTML = html;
}

// ===== 添加实词 =====
function showAddWordModal() {
    document.getElementById('add-word-modal').style.display = 'flex';
    document.getElementById('add-word-input').value = '';
    document.getElementById('word-preview').style.display = 'none';
    document.getElementById('manual-add-form').style.display = 'none';
    resetManualForm();
}

async function queryWord() {
    const word = document.getElementById('add-word-input').value.trim();
    if (!word) {
        showToast('请输入实词');
        return;
    }

    const previewEl = document.getElementById('word-preview');
    const previewContent = document.getElementById('preview-content');
    const previewWordName = document.getElementById('preview-word-name');
    const previewBadge = document.getElementById('preview-badge');
    const addBtnContainer = document.getElementById('add-to-library-btn-container');

    previewEl.style.display = 'block';
    previewWordName.textContent = word;
    previewContent.innerHTML = '<div class="loading-placeholder" style="padding:20px;">查询中...</div>';
    addBtnContainer.innerHTML = '';

    try {
        const data = await API.searchExternal(word);

        if (data.in_library) {
            previewBadge.textContent = '✅ 已在词库中';
            previewBadge.className = 'preview-badge in-library';
            previewContent.innerHTML = '<p style="color:var(--text-muted);font-size:14px;padding:8px 0;">该实词已在词库中，请在词库中查看。</p>';
        } else {
            previewBadge.textContent = '未收录';
            previewBadge.className = 'preview-badge not-in-library';
            previewContent.innerHTML = `
                <p style="color:var(--text-muted);font-size:14px;padding:8px 0;">
                    该实词尚未在词库中，请手动填写信息后添加。
                </p>
            `;
            // 预填实词名
            document.getElementById('form-word').value = word;
            document.getElementById('manual-add-form').style.display = 'block';
            addBtnContainer.innerHTML = '';
        }
    } catch (e) {
        previewBadge.textContent = '查询失败';
        previewBadge.className = 'preview-badge not-in-library';
        previewContent.innerHTML = `<p style="color:var(--error);font-size:14px;">查询失败：${e.message}</p>`;
    }
}

function resetManualForm() {
    defCount = 1;
    document.getElementById('form-word').value = '';
    const formDefs = document.getElementById('form-definitions');
    formDefs.innerHTML = createDefinitionItem(0);
}

function createDefinitionItem(index) {
    return `
        <div class="definition-item" id="def-item-${index}" data-index="${index}">
            <div class="def-header">
                <span class="def-num">释义 ${index + 1}</span>
                ${index > 0 ? `<button class="btn-remove-def" onclick="removeDefinition(${index})">删除此释义</button>` : ''}
            </div>
            <div class="form-group">
                <label class="form-label">释义内容 *</label>
                <input type="text" class="form-input def-text-input" placeholder="如：靠近，挨着">
            </div>
            <div class="examples-section">
                <label class="form-label">例句（可选）</label>
                <div class="example-items" id="examples-${index}">
                    ${createExampleItem()}
                </div>
                <button class="btn-add-ex" onclick="addExample(${index})">+ 添加例句</button>
            </div>
        </div>
    `;
}

function createExampleItem() {
    return `
        <div class="example-item">
            <input type="text" class="form-input ex-sentence" placeholder="例句文字">
            <input type="text" class="form-input ex-source" placeholder="出处文章">
            <input type="text" class="form-input ex-author" placeholder="作者">
            <input type="text" class="form-input ex-dynasty" placeholder="朝代">
            <button class="btn-remove-ex" onclick="removeExample(this)">−</button>
        </div>
    `;
}

function addDefinition() {
    const container = document.getElementById('form-definitions');
    const item = document.createElement('div');
    item.innerHTML = createDefinitionItem(defCount);
    container.appendChild(item.firstElementChild);
    defCount++;
}

function removeDefinition(index) {
    const item = document.getElementById(`def-item-${index}`);
    if (item) item.remove();
}

function addExample(defIndex) {
    const container = document.getElementById(`examples-${defIndex}`);
    if (!container) return;
    const item = document.createElement('div');
    item.innerHTML = createExampleItem();
    container.appendChild(item.firstElementChild);
}

function removeExample(btn) {
    btn.closest('.example-item').remove();
}

async function saveWord() {
    const word = document.getElementById('form-word').value.trim();
    if (!word) {
        showToast('请输入实词');
        return;
    }

    // 收集所有释义
    const defItems = document.querySelectorAll('#form-definitions .definition-item');
    const definitions = [];

    defItems.forEach(defItem => {
        const defText = defItem.querySelector('.def-text-input')?.value.trim();
        if (!defText) return;

        const examples = [];
        defItem.querySelectorAll('.example-item').forEach(exItem => {
            const sentence = exItem.querySelector('.ex-sentence')?.value.trim();
            if (!sentence) return;
            examples.push({
                sentence,
                source_article: exItem.querySelector('.ex-source')?.value.trim() || '',
                author: exItem.querySelector('.ex-author')?.value.trim() || '',
                dynasty: exItem.querySelector('.ex-dynasty')?.value.trim() || '',
            });
        });

        definitions.push({ definition: defText, examples });
    });

    if (definitions.length === 0) {
        showToast('至少需要一个释义');
        return;
    }

    try {
        await API.addWord({ word, definitions });
        showToast(`"${word}" 已添加到词库！`);
        closeModal('add-word-modal');
        loadLibrary(libraryPage, librarySearch);
        loadStats();
    } catch (e) {
        showToast('添加失败：' + e.message);
    }
}

// ===== 测试 =====
function resetTestToReady() {
    document.getElementById('test-ready').style.display = 'block';
    document.getElementById('test-playing').style.display = 'none';
    document.getElementById('test-result').style.display = 'none';
    gameQuestions = [];
    gameCurrentIndex = 0;
    gameScore = 0;
    gameResults = [];
}

async function loadTest() {
    try {
        const data = await API.startGame();
        if (!data.questions || data.questions.length === 0) {
            showToast('词库为空，请先添加实词');
            return;
        }
        gameQuestions = data.questions;
        gameCurrentIndex = 0;
        gameScore = 0;
        gameResults = [];

        document.getElementById('test-ready').style.display = 'none';
        document.getElementById('test-playing').style.display = 'block';
        document.getElementById('test-result').style.display = 'none';

        document.getElementById('test-total').textContent = `共 ${gameQuestions.length} 题`;

        showQuestion(0);
    } catch (e) {
        showToast('启动失败：' + e.message);
    }
}

function showQuestion(index) {
    if (index >= gameQuestions.length) {
        showResult();
        return;
    }

    const q = gameQuestions[index];
    const total = gameQuestions.length;

    // 更新进度
    document.getElementById('test-current').textContent = `第 ${index + 1} 题`;
    document.getElementById('test-score').textContent = gameScore;
    const pct = (index / total) * 100;
    document.getElementById('progress-bar').style.width = pct + '%';

    // 填入题目
    document.getElementById('q-word').textContent = q.word;
    document.getElementById('q-word-inline').textContent = q.word;
    document.getElementById('q-sentence').textContent = q.sentence;

    // 出处信息
    let sourceInfo = q.source_article ? `《${q.source_article}》` : '';
    let authorInfo = '';
    if (q.author || q.dynasty) {
        authorInfo = [q.author, q.dynasty].filter(Boolean).join('·');
    }
    document.getElementById('q-source').textContent = sourceInfo;
    document.getElementById('q-author').textContent = authorInfo ? ` ${authorInfo}` : '';

    // 渲染选项
    const container = document.getElementById('options-container');
    container.innerHTML = q.options.map((opt, i) => `
        <button class="option-btn" onclick="selectOption(this, ${opt.is_correct}, ${q.word_id}, '${escapeJs(q.word)}')">
            ${escapeHtml(opt.text)}
        </button>
    `).join('');

    // 动画
    const card = document.getElementById('question-card');
    card.style.animation = 'none';
    card.offsetHeight;  // reflow
    card.style.animation = 'fadeIn 0.3s ease';
}

function selectOption(btn, isCorrect, wordId, word) {
    // 禁用所有选项
    const container = document.getElementById('options-container');
    container.querySelectorAll('.option-btn').forEach(b => {
        b.disabled = true;
    });

    // 标记对错
    if (isCorrect) {
        btn.classList.add('correct');
        gameScore++;
        document.getElementById('test-score').textContent = gameScore;
    } else {
        btn.classList.add('wrong');
        // 高亮正确答案
        const q = gameQuestions[gameCurrentIndex];
        container.querySelectorAll('.option-btn').forEach(b => {
            const matchOption = q.options.find(opt => opt.text === b.textContent.trim());
            if (matchOption && matchOption.is_correct) {
                b.classList.add('correct');
            }
        });
    }

    // 记录结果
    gameResults.push({ word_id: wordId, is_correct: isCorrect });

    // 延迟进入下一题
    setTimeout(() => {
        gameCurrentIndex++;
        if (gameCurrentIndex < gameQuestions.length) {
            showQuestion(gameCurrentIndex);
        } else {
            // 更新进度条到100%
            document.getElementById('progress-bar').style.width = '100%';
            setTimeout(showResult, 400);
        }
    }, 1000);
}

async function showResult() {
    document.getElementById('test-playing').style.display = 'none';
    document.getElementById('test-result').style.display = 'block';

    // 提交结果
    let resultData = { correct_count: gameScore, total: gameQuestions.length, is_perfect: false, correct_words: [], wrong_words: [] };
    try {
        resultData = await API.submitGame(gameResults);
    } catch (e) {
        console.error('提交结果失败', e);
    }

    const total = gameQuestions.length;
    const correct = resultData.correct_count || gameScore;
    const isPerfect = resultData.is_perfect;

    // 设置显示
    document.getElementById('result-score').textContent = correct;
    document.querySelector('.score-total').textContent = total;

    if (isPerfect) {
        document.getElementById('result-emoji').textContent = '🏆';
        document.getElementById('result-title').textContent = '善哉！善哉！';
    } else if (correct >= total * 0.8) {
        document.getElementById('result-emoji').textContent = '🎉';
        document.getElementById('result-title').textContent = '答题完成';
    } else if (correct >= total * 0.6) {
        document.getElementById('result-emoji').textContent = '📝';
        document.getElementById('result-title').textContent = '继续努力';
    } else {
        document.getElementById('result-emoji').textContent = '💪';
        document.getElementById('result-title').textContent = '加油加油';
    }

    // 正确/错误的实词
    const correctWords = resultData.correct_words || [];
    const wrongWords = resultData.wrong_words || [];

    const correctEl = document.getElementById('correct-words');
    const wrongEl = document.getElementById('wrong-words');

    correctEl.innerHTML = correctWords.length
        ? correctWords.map(w => `<span class="word-tag correct">${w}</span>`).join('')
        : '<span style="color:var(--text-muted);font-size:14px;">无</span>';

    wrongEl.innerHTML = wrongWords.length
        ? wrongWords.map(w => `<span class="word-tag wrong">${w}</span>`).join('')
        : '<span style="color:var(--text-muted);font-size:14px;">无</span>';

    // 隐藏空分区
    document.getElementById('correct-section').style.display = correctWords.length ? 'block' : 'block';
    document.getElementById('wrong-section').style.display = wrongWords.length ? 'block' : wrongWords.length === 0 ? 'none' : 'block';

    // 刷新统计
    loadStats();
}

function retryTest() {
    resetTestToReady();
    setTimeout(loadTest, 100);
}

function goHome() {
    navigateTo('home');
}

// ===== 工具函数 =====
function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function escapeJs(str) {
    if (!str) return '';
    return String(str).replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '\\"');
}

function showToast(msg) {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.style.display = 'block';
    toast.style.animation = 'none';
    toast.offsetHeight;
    toast.style.animation = 'toastFade 2.5s ease forwards';
    setTimeout(() => { toast.style.display = 'none'; }, 2600);
}

// ===== 初始化 =====
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
});
