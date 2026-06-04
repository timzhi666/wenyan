"""
文言文实词测试 - 后端Flask API
支持本地SQLite 和 Render PostgreSQL 双模式
"""
import os
import json
import random
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# ======================== 数据库适配层 ========================

DATABASE_URL = os.environ.get('DATABASE_URL', '')
USE_POSTGRES = DATABASE_URL.startswith('postgres')

if USE_POSTGRES:
    import psycopg2
    import psycopg2.extras

    def get_db():
        """PostgreSQL 连接（Render 免费 PostgreSQL）"""
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        conn.autocommit = False
        return conn, conn.cursor(cursor_factory=psycopg2.RealDictCursor)

    def db_close(conn, cursor):
        cursor.close()
        conn.close()

    def db_commit(conn):
        conn.commit()

    SQL_PLACEHOLDER = '%s'
else:
    import sqlite3

    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wenyan.db')

    def get_db():
        """SQLite 连接（本地开发）"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn, conn.cursor()

    def db_close(conn, cursor):
        cursor.close()
        conn.close()

    def db_commit(conn):
        conn.commit()

    SQL_PLACEHOLDER = '?'


def query_one(conn, cursor, sql, params=()):
    """执行查询，返回一行字典"""
    cursor.execute(sql, params)
    row = cursor.fetchone()
    return dict(row) if row else None


def query_all(conn, cursor, sql, params=()):
    """执行查询，返回所有行字典列表"""
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    return [dict(r) for r in rows]


# ======================== 建表语句 ========================

CREATE_WORDS = '''
    CREATE TABLE IF NOT EXISTS words (
        id SERIAL PRIMARY KEY,
        word TEXT NOT NULL UNIQUE,
        weight REAL DEFAULT 1.0,
        correct_count INTEGER DEFAULT 0,
        wrong_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''' if USE_POSTGRES else '''
    CREATE TABLE IF NOT EXISTS words (
        INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT NOT NULL UNIQUE,
        weight REAL DEFAULT 1.0,
        correct_count INTEGER DEFAULT 0,
        wrong_count INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    )
'''

CREATE_DEFINITIONS = '''
    CREATE TABLE IF NOT EXISTS definitions (
        id SERIAL PRIMARY KEY,
        word_id INTEGER NOT NULL,
        definition TEXT NOT NULL,
        sort_order INTEGER DEFAULT 0,
        FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE
    )
''' if USE_POSTGRES else '''
    CREATE TABLE IF NOT EXISTS definitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word_id INTEGER NOT NULL,
        definition TEXT NOT NULL,
        sort_order INTEGER DEFAULT 0,
        FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE
    )
'''

CREATE_EXAMPLES = '''
    CREATE TABLE IF NOT EXISTS examples (
        id SERIAL PRIMARY KEY,
        definition_id INTEGER NOT NULL,
        sentence TEXT NOT NULL,
        source_article TEXT,
        author TEXT,
        dynasty TEXT,
        sort_order INTEGER DEFAULT 0,
        FOREIGN KEY (definition_id) REFERENCES definitions(id) ON DELETE CASCADE
    )
''' if USE_POSTGRES else '''
    CREATE TABLE IF NOT EXISTS examples (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        definition_id INTEGER NOT NULL,
        sentence TEXT NOT NULL,
        source_article TEXT,
        author TEXT,
        dynasty TEXT,
        sort_order INTEGER DEFAULT 0,
        FOREIGN KEY (definition_id) REFERENCES definitions(id) ON DELETE CASCADE
    )
'''

CREATE_GAME_RECORDS = '''
    CREATE TABLE IF NOT EXISTS game_records (
        id SERIAL PRIMARY KEY,
        played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_questions INTEGER DEFAULT 10,
        correct_count INTEGER DEFAULT 0,
        is_perfect INTEGER DEFAULT 0,
        correct_words TEXT,
        wrong_words TEXT
    )
''' if USE_POSTGRES else '''
    CREATE TABLE IF NOT EXISTS game_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        played_at TEXT DEFAULT (datetime('now', 'localtime')),
        total_questions INTEGER DEFAULT 10,
        correct_count INTEGER DEFAULT 0,
        is_perfect INTEGER DEFAULT 0,
        correct_words TEXT,
        wrong_words TEXT
    )
'''

ALL_TABLES = [CREATE_WORDS, CREATE_DEFINITIONS, CREATE_EXAMPLES, CREATE_GAME_RECORDS]


def init_db():
    """初始化数据库表结构"""
    conn, c = get_db()
    for table_sql in ALL_TABLES:
        c.execute(table_sql)
    db_commit(conn)
    db_close(conn, c)
    print("数据库表结构已创建/检查完毕")


def ensure_data_imported():
    """首次启动时导入词库数据（仅 PostgreSQL 模式）"""
    if not USE_POSTGRES:
        return

    conn, c = get_db()
    count_row = query_one(conn, c, 'SELECT COUNT(*) AS cnt FROM words')
    db_close(conn, c)

    if count_row and count_row['cnt'] > 0:
        print(f"数据库中已有 {count_row['cnt']} 条实词数据，跳过初始化导入")
        return

    print("检测到空数据库，开始导入初始词库数据...")
    try:
        import_init_data(conn_func=get_db, close_func=db_close, commit_func=db_commit,
                         ph=SQL_PLACEHOLDER, query_one_fn=query_one, query_all_fn=query_all)
        print("初始词库数据导入完成！")
    except Exception as e:
        print(f"初始数据导入失败（将在下次启动时重试）: {e}")


# ======================== 静态文件服务 ========================

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')


@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('../frontend', path)


# ======================== 统计接口 ========================

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取首页统计数据"""
    conn, c = get_db()
    word_count = query_one(conn, c, 'SELECT COUNT(*) AS cnt FROM words')['cnt']
    game_count = query_one(conn, c, 'SELECT COUNT(*) AS cnt FROM game_records')['cnt']
    perfect_count = query_one(conn, c, 'SELECT COUNT(*) AS cnt FROM game_records WHERE is_perfect=1')['cnt']
    history_count = query_one(
        conn, c, 'SELECT COUNT(DISTINCT id) AS cnt FROM words WHERE wrong_count > 0'
    )['cnt']
    db_close(conn, c)
    return jsonify({
        'word_count': word_count,
        'history_count': history_count,
        'game_count': game_count,
        'perfect_count': perfect_count
    })


# ======================== 词库接口 ========================

@app.route('/api/words', methods=['GET'])
def get_words():
    """获取词库列表，支持搜索"""
    search = request.args.get('q', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    offset = (page - 1) * per_page

    conn, c = get_db()

    if search:
        total = query_one(conn, c,
            'SELECT COUNT(*) AS cnt FROM words WHERE word LIKE ?',
            (f'%{search}',))['cnt']
        rows = query_all(conn, c,
            'SELECT * FROM words WHERE word LIKE ? ORDER BY id LIMIT ? OFFSET ?',
            (f'%{search}%', per_page, offset))
    else:
        total = query_one(conn, c, 'SELECT COUNT(*) AS cnt FROM words')['cnt']
        rows = query_all(conn, c,
            'SELECT * FROM words ORDER BY id LIMIT ? OFFSET ?',
            (per_page, offset))

    words = []
    for row in rows:
        defs = query_all(conn, c,
            'SELECT * FROM definitions WHERE word_id=? ORDER BY sort_order',
            (row['id'],))
        definitions = []
        for d in defs:
            exs = query_all(conn, c,
                'SELECT * FROM examples WHERE definition_id=? ORDER BY sort_order',
                (d['id'],))
            d['examples'] = exs
            definitions.append(d)
        row['definitions'] = definitions
        words.append(row)

    db_close(conn, c)
    return jsonify({'words': words, 'total': total, 'page': page, 'per_page': per_page})


@app.route('/api/words/<int:word_id>', methods=['GET'])
def get_word(word_id):
    """获取单个实词详情"""
    conn, c = get_db()
    row = query_one(conn, c, 'SELECT * FROM words WHERE id=?', (word_id,))
    if not row:
        db_close(conn, c)
        return jsonify({'error': '实词不存在'}), 404

    defs = query_all(conn, c,
        'SELECT * FROM definitions WHERE word_id=? ORDER BY sort_order',
        (word_id,))
    definitions = []
    for d in defs:
        exs = query_all(conn, c,
            'SELECT * FROM examples WHERE definition_id=? ORDER BY sort_order',
            (d['id'],))
        d['examples'] = exs
        definitions.append(d)
    row['definitions'] = definitions

    db_close(conn, c)
    return jsonify(row)


@app.route('/api/words', methods=['POST'])
def add_word():
    """添加实词到词库"""
    data = request.get_json()
    word = data.get('word', '').strip()
    definitions = data.get('definitions', [])

    if not word:
        return jsonify({'error': '实词不能为空'}), 400

    conn, c = get_db()

    existing = query_one(conn, c, 'SELECT id FROM words WHERE word=?', (word,))
    if existing:
        db_close(conn, c)
        return jsonify({'error': f'"{word}" 已在词库中，不允许重复添加'}), 409

    c.execute('INSERT INTO words (word, weight) VALUES (?, 1.0)', (word,))
    if USE_POSTGRES:
        word_id = c.fetchone()[0] if c.lastrowid == 0 else c.lastrowid  # psycopg2 uses FETCH LASTROWID concept differently
        # Actually for psycopg2 with RETURNING or lastrowid
    else:
        word_id = c.lastrowid

    # 获取刚插入的 word_id
    if USE_POSTGRES:
        result = query_one(conn, c, 'SELECT id FROM words WHERE word=?', (word,))
        word_id = result['id']

    for i, def_data in enumerate(definitions):
        definition = def_data.get('definition', '').strip()
        if not definition:
            continue
        c.execute(
            'INSERT INTO definitions (word_id, definition, sort_order) VALUES (?, ?, ?)',
            (word_id, definition, i)
        )
        if USE_POSTGRES:
            r = query_one(conn, c, 'SELECT id FROM definitions WHERE word_id=? AND definition=?',
                          (word_id, definition))
            def_id = r['id']
        else:
            def_id = c.lastrowid

        for j, ex_data in enumerate(def_data.get('examples', [])):
            sentence = ex_data.get('sentence', '').strip()
            if not sentence:
                continue
            c.execute(
                '''INSERT INTO examples (definition_id, sentence, source_article, author, dynasty, sort_order)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (def_id, sentence,
                 ex_data.get('source_article', ''),
                 ex_data.get('author', ''),
                 ex_data.get('dynasty', ''),
                 j))

    db_commit(conn)
    db_close(conn, c)
    return jsonify({'success': True, 'word_id': word_id}), 201


@app.route('/api/words/<int:word_id>', methods=['DELETE'])
def delete_word(word_id):
    """删除实词"""
    conn, c = get_db()
    row = query_one(conn, c, 'SELECT id FROM words WHERE id=?', (word_id,))
    if not row:
        db_close(conn, c)
        return jsonify({'error': '实词不存在'}), 404

    c.execute('DELETE FROM words WHERE id=?', (word_id,))
    db_commit(conn)
    db_close(conn, c)
    return jsonify({'success': True})


@app.route('/api/words/search-external', methods=['GET'])
def search_external():
    """查询实词是否在词库中"""
    word = request.args.get('word', '').strip()
    if not word:
        return jsonify({'error': '请输入实词'}), 400

    conn, c = get_db()
    existing = query_one(conn, c, 'SELECT id FROM words WHERE word=?', (word,))
    db_close(conn, c)

    if existing:
        return jsonify({'in_library': True, 'word': word})
    return jsonify({'in_library': False, 'word': word, 'definitions': []})


# ======================== 游戏接口 ========================

def calculate_weight(word):
    """计算实词权重（加权随机算法）"""
    correct = word['correct_count']
    wrong = word['wrong_count']
    if correct == 0 and wrong == 0:
        return 1.5
    weight = 1.0 + wrong * 0.5 - correct * 0.2
    return max(0.3, weight)


@app.route('/api/game/start', methods=['POST'])
def start_game():
    """开始一轮测试，返回10道题"""
    conn, c = get_db()

    all_words_rows = query_all(conn, c, 'SELECT * FROM words')
    word_list = all_words_rows

    valid_words = []
    for w in word_list:
        defs = query_all(conn, c,
            'SELECT d.id FROM definitions d WHERE d.word_id=? '
            'AND EXISTS (SELECT 1 FROM examples e WHERE e.definition_id=d.id)',
            (w['id'],))
        if defs:
            valid_words.append(w)

    if len(valid_words) < 4:
        db_close(conn, c)
        return jsonify({'error': '词库中至少需要4个有例句的实词才能开始测试'}), 400

    weights = [calculate_weight(w) for w in valid_words]
    selected_count = min(10, len(valid_words))
    selected_words = weighted_sample_without_replacement(valid_words, weights, selected_count)

    questions = []
    for word_data in selected_words:
        word_id = word_data['id']

        defs = query_all(conn, c,
            '''SELECT d.* FROM definitions d
               WHERE d.word_id=?
               AND EXISTS (SELECT 1 FROM examples e WHERE e.definition_id=d.id)
               ORDER BY d.sort_order''',
            (word_id,))
        if not defs:
            continue

        correct_def = random.choice(defs)

        examples = query_all(conn, c,
            'SELECT * FROM examples WHERE definition_id=? ORDER BY sort_order',
            (correct_def['id'],))
        if not examples:
            continue

        example = random.choice(examples)

        other_defs = []
        other_words = [w for w in word_list if w['id'] != word_id]
        random.shuffle(other_words)
        for other_word in other_words:
            other_defs_rows = query_all(conn, c,
                'SELECT * FROM definitions WHERE word_id=? ORDER BY sort_order LIMIT 1',
                (other_word['id'],))
            if other_defs_rows:
                cand = other_defs_rows[0]
                if cand['definition'] != correct_def['definition']:
                    other_defs.append(cand)
            if len(other_defs) >= 3:
                break

        if len(other_defs) < 3:
            continue

        options = ([{'text': correct_def['definition'], 'is_correct': True}] +
                  [{'text': d['definition'], 'is_correct': False} for d in other_defs])
        random.shuffle(options)

        questions.append({
            'word_id': word_id,
            'word': word_data['word'],
            'sentence': example['sentence'],
            'source_article': example['source_article'],
            'author': example['author'],
            'dynasty': example['dynasty'],
            'correct_definition': correct_def['definition'],
            'options': options
        })

    db_close(conn, c)

    if len(questions) < 4:
        return jsonify({'error': '词库中有效实词不足，请先添加更多实词'}), 400

    return jsonify({'questions': questions})


def weighted_sample_without_replacement(items, weights, k):
    """加权不重复采样"""
    if k >= len(items):
        return items[:]
    result = []
    remaining_items = list(items)
    remaining_weights = list(weights)
    for _ in range(k):
        total = sum(remaining_weights)
        r = random.uniform(0, total)
        cumulative = 0
        for i, w in enumerate(remaining_weights):
            cumulative += w
            if r <= cumulative:
                result.append(remaining_items[i])
                remaining_items.pop(i)
                remaining_weights.pop(i)
                break
    return result


@app.route('/api/game/submit', methods=['POST'])
def submit_game():
    """提交游戏结果"""
    data = request.get_json()
    results = data.get('results', [])
    if not results:
        return jsonify({'error': '没有答题记录'}), 400

    conn, c = get_db()

    correct_words = []
    wrong_words = []
    correct_count = 0

    for r in results:
        word_id = r.get('word_id')
        is_correct = r.get('is_correct', False)
        word_row = query_one(conn, c, 'SELECT word FROM words WHERE id=?', (word_id,))
        if not word_row:
            continue
        word_name = word_row['word']
        if is_correct:
            correct_count += 1
            correct_words.append(word_name)
            c.execute('UPDATE words SET correct_count = correct_count + 1 WHERE id=?', (word_id,))
        else:
            wrong_words.append(word_name)
            c.execute('UPDATE words SET wrong_count = wrong_count + 1 WHERE id=?', (word_id,))

    is_perfect = 1 if correct_count == len(results) else 0

    c.execute(
        '''INSERT INTO game_records
           (total_questions, correct_count, is_perfect, correct_words, wrong_words)
           VALUES (?, ?, ?, ?, ?)''',
        (len(results), correct_count, is_perfect,
         json.dumps(correct_words, ensure_ascii=False),
         json.dumps(wrong_words, ensure_ascii=False)))

    db_commit(conn)
    db_close(conn, c)

    return jsonify({
        'success': True,
        'correct_count': correct_count,
        'total': len(results),
        'is_perfect': bool(is_perfect),
        'correct_words': correct_words,
        'wrong_words': wrong_words
    })


# ======================== 游戏记录接口 ========================

@app.route('/api/game/records', methods=['GET'])
def get_game_records():
    """获取游戏记录列表"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    offset = (page - 1) * per_page

    conn, c = get_db()
    total = query_one(conn, c, 'SELECT COUNT(*) AS cnt FROM game_records')['cnt']
    rows = query_all(conn, c,
        'SELECT * FROM game_records ORDER BY played_at DESC LIMIT ? OFFSET ?',
        (per_page, offset))

    records = []
    for row in rows:
        try:
            row['correct_words'] = json.loads(row['correct_words'] or '[]')
            row['wrong_words'] = json.loads(row['wrong_words'] or '[]')
        except Exception:
            row['correct_words'] = []
            row['wrong_words'] = []
        records.append(row)

    db_close(conn, c)
    return jsonify({'records': records, 'total': total})


# ======================== 健康检查 ========================

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'time': datetime.now().isoformat()})


# ======================== 启动 ========================

if __name__ == '__main__':
    init_db()
    # 本地开发时也尝试导入数据（如果数据库为空）
    ensure_data_imported()
    port = int(os.environ.get('PORT', 5001))
    print(f"服务器启动于 http://localhost:{port}")
    app.run(debug=True, host='0.0.0.0', port=port)
