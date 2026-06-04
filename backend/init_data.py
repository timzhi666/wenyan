"""
文言文实词测试 - 数据初始化脚本 v3
支持 SQLite（本地开发）和 PostgreSQL（Render 部署）双模式
"""
import re
import os
import csv
import io

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.csv')

# 文章出处 -> (作者, 朝代)
ARTICLE_META = {
    '核舟记': ('魏学洢', '明'),
    '捕蛇者说': ('柳宗元', '唐'),
    '小石潭记': ('柳宗元', '唐'),
    '出师表': ('诸葛亮', '三国·蜀汉'),
    '桃花源记': ('陶渊明', '东晋'),
    '陈涉世家': ('司马迁', '西汉'),
    '曹刿论战': ('左丘明', '春秋'),
    '醉翁亭记': ('欧阳修', '宋'),
    '岳阳楼记': ('范仲淹', '宋'),
    '论语': ('孔子及其弟子', '春秋'),
    '孟子': ('孟子及其弟子', '战国'),
    '天时不如地利': ('孟子', '战国'),
    '生于忧患，死于安乐': ('孟子', '战国'),
    '愚公移山': ('列御寇', '战国'),
    '马说': ('韩愈', '唐'),
    '师说': ('韩愈', '唐'),
    '陋室铭': ('刘禹锡', '唐'),
    '爱莲说': ('周敦颐', '宋'),
    '伤仲永': ('王安石', '宋'),
    '送东阳马生序': ('宋濂', '明'),
    '黄生借书说': ('袁枚', '清'),
    '为学': ('彭端淑', '清'),
    '周处': ('刘义庆', '南朝宋'),
    '卖油翁': ('欧阳修', '宋'),
    '黔之驴': ('柳宗元', '唐'),
    '狼': ('蒲松龄', '清'),
    '邹忌讽齐王纳谏': ('刘向', '西汉'),
    '公输': ('墨子及其弟子', '战国'),
    '登泰山记': ('姚鼐', '清'),
    '石钟山记': ('苏轼', '宋'),
    '游褒禅山记': ('王安石', '宋'),
    '赤壁赋': ('苏轼', '宋'),
    '赤壁之战': ('司马光', '宋'),
    '隆中对': ('陈寿', '西晋'),
    '过秦论': ('贾谊', '西汉'),
    '廉颇蔺相如列传': ('司马迁', '西汉'),
    '鱼我所欲也': ('孟子', '战国'),
    '黠鼠赋': ('苏轼', '宋'),
    '唐雎不辱使命': ('刘向', '西汉'),
    '橘逾淮为枳': ('刘向', '西汉'),
    '口技（林嗣环）': ('林嗣环', '清'),
    '口技': ('林嗣环', '清'),
    '湖心亭看雪': ('张岱', '明'),
    '记承天夜游': ('苏轼', '宋'),
    '吕氏春秋两则': ('吕不韦等', '战国'),
    '两小儿辩日': ('列御寇', '战国'),
    '孔孟论学': ('孔子及孟子', '春秋·战国'),
    '与朱元思书': ('吴均', '南朝梁'),
    '三峡': ('郦道元', '北魏'),
    '答司马谏议书': ('王安石', '宋'),
    '潍县署中寄舍弟墨第一书': ('郑燮', '清'),
    '扁鹊见蔡桓公': ('韩非子', '战国'),
    '中国古代寓言四则': ('先秦诸子', '先秦'),
    '中国古代神话三则': ('佚名', '先秦'),
    '木兰诗': ('佚名', '南北朝'),
    '静夜思': ('李白', '唐'),
    '茅屋为秋风所破歌': ('杜甫', '唐'),
    '石壕吏': ('杜甫', '唐'),
    '登鹳雀楼': ('王之涣', '唐'),
    '行路难': ('李白', '唐'),
    '观书有感': ('朱熹', '宋'),
    '题都城南庄': ('崔护', '唐'),
    '山行': ('杜牧', '唐'),
    '如梦令': ('李清照', '宋'),
    '满江红': ('岳飞', '宋'),
    '沁园春·雪': ('毛泽东', '近现代'),
    '忆江南': ('白居易', '唐'),
    '琵琶行': ('白居易', '唐'),
    '送元二使安西': ('王维', '唐'),
    '赠汪伦': ('李白', '唐'),
    '九月九日忆山东兄弟': ('王维', '唐'),
    '乐游原': ('李商隐', '唐'),
    '过零丁洋': ('文天祥', '宋'),
    '示儿': ('陆游', '宋'),
    '黄鹤楼': ('崔颢', '唐'),
    '兰亭集序': ('王羲之', '东晋'),
    '归去来兮辞': ('陶渊明', '东晋'),
    '归园田居': ('陶渊明', '东晋'),
    '离骚': ('屈原', '战国'),
    '劝学': ('荀子', '战国'),
    '种树郭橐驼传': ('柳宗元', '唐'),
    '始得西山宴游记': ('柳宗元', '唐'),
    '促织': ('蒲松龄', '清'),
    '鸿门宴': ('司马迁', '西汉'),
    '信陵君窃符救赵': ('司马迁', '西汉'),
    '苏武传': ('班固', '东汉'),
    '张衡传': ('范晔', '南朝宋'),
    '报任安书': ('司马迁', '西汉'),
    '屈原列传': ('司马迁', '西汉'),
    '指南录后序': ('文天祥', '宋'),
    '左忠毅公逸事': ('方苞', '清'),
    '柳敬亭传': ('黄宗羲', '清'),
    '病梅馆记': ('龚自珍', '清'),
    '治水必躬亲': ('钱泳', '清'),
    '卖炭翁': ('白居易', '唐'),
    '卖柑者言': ('刘基', '明'),
    '三国志': ('陈寿', '西晋'),
    '史记': ('司马迁', '西汉'),
    '汉书': ('班固', '东汉'),
    '战国策': ('刘向编', '西汉'),
    '左传': ('左丘明', '春秋'),
    '荀子': ('荀子', '战国'),
    '韩非子': ('韩非', '战国'),
    '庄子': ('庄子及其后学', '战国'),
    '孔雀东南飞': ('佚名', '汉末'),
    '短歌行': ('曹操', '东汉'),
    '晋书': ('房玄龄等', '唐'),
    '宋东阳马生序': ('宋濂', '明'),
    '六国论': ('苏洵', '宋'),
    '阿房宫赋': ('杜牧', '唐'),
    '滕王阁序': ('王勃', '唐'),
    '论贵粟疏': ('晁错', '西汉'),
    '谏太宗十思疏': ('魏征', '唐'),
    '螳螂捕蝉': ('刘向', '西汉'),
    '果合传': ('佚名', '清'),
    '毛遂自荐': ('司马迁', '西汉'),
    '巢谷传': ('苏轼', '宋'),
    '问说': ('刘开', '清'),
    '熟读精思（课外）': ('朱熹', '宋'),
    '进学解': ('韩愈', '唐'),
    '西塞山怀古': ('刘禹锡', '唐'),
    '登飞来峰': ('王安石', '宋'),
    '题西林壁': ('苏轼', '宋'),
    '冯婉贞': ('徐珂', '清'),
    '河中石兽': ('纪昀', '清'),
    '伯牙鼓琴': ('列御寇', '战国'),
    '孙权劝学': ('司马光', '宋'),
    '陈太丘与友期行': ('刘义庆', '南朝宋'),
    '龟虽寿': ('曹操', '东汉'),
    '明史': ('张廷玉等', '清'),
    '商君书': ('商鞅及后学', '战国'),
    '周易': ('佚名', '先秦'),
    '尚书': ('佚名', '先秦'),
    '诗经·硕鼠': ('佚名', '先秦'),
    '诗经': ('佚名', '先秦'),
    '礼记·礼运': ('佚名', '先秦'),
    '礼记': ('佚名', '先秦'),
    '日知录': ('顾炎武', '清'),
    '原毁': ('韩愈', '唐'),
    '闻官军收河南河北': ('杜甫', '唐'),
    '论积贮疏': ('贾谊', '西汉'),
    '与陈伯之书': ('丘迟', '南朝梁'),
    '陈情表': ('李密', '西晋'),
    '论衡': ('王充', '东汉'),
    '晏子春秋': ('佚名', '战国'),
    '触龙说赵太后': ('刘向', '西汉'),
    '卜算子·咏梅': ('陆游', '宋'),
    '击壤歌': ('佚名', '先秦'),
    '中夜起望西园值月上': ('柳宗元', '唐'),
    '说文解字': ('许慎', '东汉'),
    '聊斋志异': ('蒲松龄', '清'),
    '世说新语': ('刘义庆', '南朝宋'),
    '日常用语': ('', ''),
    '成语': ('', ''),
    '文学术语': ('', ''),
    '历史': ('', ''),
    '古代官职': ('', ''),
    '医学术语': ('', ''),
}


# ======================== CSV 解析逻辑（纯计算，无数据库依赖） ========================

CHINESE_NUMERALS = ['⑩', '①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨']


def split_by_numerals(text):
    """按中文序号将内容分割成多个块"""
    positions = []
    for ch in CHINESE_NUMERALS:
        idx = 0
        while True:
            pos = text.find(ch, idx)
            if pos == -1:
                break
            positions.append((pos, ch))
            idx = pos + 1

    if not positions:
        return [('', text)]

    positions.sort(key=lambda x: x[0])
    blocks = []
    for i, (pos, numeral) in enumerate(positions):
        start = pos + len(numeral)
        end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
        block_text = text[start:end].strip()
        blocks.append((numeral, block_text))

    return blocks


def parse_block(block_text):
    """
    解析单个释义块
    格式：释义 例句1《出处1》；例句2《出处2》...
    """
    block_text = block_text.strip()
    if not block_text:
        return '', []

    book_pattern = re.compile(r'《([^《》]+)》')
    first_match = book_pattern.search(block_text)
    if not first_match:
        return block_text, []

    before_first_book = block_text[:first_match.start()]

    space_pos = -1
    for i, ch in enumerate(before_first_book):
        if ch in (' ', '\u3000', '\xa0'):
            space_pos = i
            break

    if space_pos != -1:
        definition = before_first_book[:space_pos].strip()
        first_ex_text = before_first_book[space_pos + 1:].strip()
    else:
        definition = before_first_book.strip()
        first_ex_text = ''

    examples = []
    parts = book_pattern.split(block_text)

    if len(parts) >= 3:
        s1 = parts[1].strip()
        if first_ex_text and s1:
            meta = ARTICLE_META.get(s1, ('', ''))
            examples.append({
                'sentence': first_ex_text,
                'source_article': s1,
                'author': meta[0],
                'dynasty': meta[1]
            })

    i = 2
    while i + 1 < len(parts):
        ti = parts[i]
        si1 = parts[i + 1].strip()
        if not si1:
            i += 2
            continue
        if '；' in ti:
            ti_parts = ti.split('；')
            ex_text = ti_parts[-1].strip()
        else:
            ex_text = ti.strip()

        if ex_text:
            meta = ARTICLE_META.get(si1, ('', ''))
            examples.append({
                'sentence': ex_text,
                'source_article': si1,
                'author': meta[0],
                'dynasty': meta[1]
            })
        i += 2

    return definition, examples


def parse_definitions_and_examples(word, content):
    """解析实词的释义和例句"""
    blocks = split_by_numerals(content)
    result = []
    for numeral, block_text in blocks:
        if not block_text.strip():
            continue
        definition, examples = parse_block(block_text)
        if definition or examples:
            result.append({'definition': definition, 'examples': examples})
    return result if result else [{'definition': content.strip(), 'examples': []}]


def get_csv_data():
    """读取并解析CSV文件，返回原始数据列表
    返回: [(word, [{definition, examples: [{sentence, source_article, author, dynasty}]}]), ...]
    """
    if not os.path.exists(CSV_PATH):
        # 尝试相对于脚本所在目录查找
        alt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.csv')
        if os.path.exists(alt_path):
            csv_file = alt_path
        else:
            raise FileNotFoundError(f"CSV 文件不存在: {CSV_PATH} 或 data.csv")
    else:
        csv_file = CSV_PATH

    print(f"读取CSV文件: {csv_file}")
    all_data = []
    seen_words = set()

    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()

    skipped = 0
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue

        parts = line.split(',', 2)
        if len(parts) < 3:
            skipped += 1
            continue

        try:
            int(parts[0].strip())
        except ValueError:
            skipped += 1
            continue

        word = parts[1].strip()
        content = parts[2].strip()
        if not word or word in seen_words:
            if word in seen_words:
                skipped += 1
            continue
        seen_words.add(word)

        defs_data = parse_definitions_and_examples(word, content)
        all_data.append((word, defs_data))

    print(f"CSV 解析完成：{len(all_data)} 个实词（跳过 {skipped} 个）")
    return all_data


# ======================== 数据库导入（双模式支持） ========================

def import_init_data(conn_func=None, close_func=None, commit_func=None,
                     ph='?', query_one_fn=None, query_all_fn=None):
    """
    将CSV数据导入数据库。
    
    参数由调用方注入以适配不同数据库后端：
      conn_func() -> (conn, cursor)
      close_func(conn, cursor)
      commit_func(conn)
      ph: SQL 占位符 ('?' for sqlite, '%s' for postgres)
      query_one_fn(conn, c, sql, params) -> dict|None
      query_all_fn(conn, c, sql, params) -> [dict]
      
    如果不提供参数（本地模式），使用 SQLite 直接操作。
    """
    # 解析CSV获取数据
    try:
        all_data = get_csv_data()
    except FileNotFoundError as e:
        print(f"错误: {e}")
        return False

    if not all_data:
        print("没有可导入的数据")
        return False

    # 判断是否为外部注入模式
    external_mode = conn_func is not None

    if external_mode:
        _import_with_adapter(all_data, conn_func, close_func, commit_func,
                             ph, query_one_fn, query_all_fn)
    else:
        _import_sqlite_local(all_data)

    return True


def _import_with_adapter(data_list, conn_func, close_func, commit_func,
                         ph, query_one_fn, query_all_fn):
    """通过注入的适配器函数导入数据（PostgreSQL 模式）"""
    imported = 0
    batch_size = 50  # 分批提交

    for batch_start in range(0, len(data_list), batch_size):
        batch = data_list[batch_start:batch_start + batch_size]
        conn, c = conn_func()

        for word, defs_data in batch:
            # 检查是否已存在
            existing = query_one_fn(conn, c, 'SELECT id FROM words WHERE word=?', (word,))
            if existing:
                continue

            try:
                c.execute(f'INSERT INTO words (word) VALUES ({ph})', (word,))
                # 获取刚插入的 id
                result = query_one_fn(conn, c, 'SELECT id FROM words WHERE word=?', (word,))
                if not result:
                    continue
                word_id = result['id']

                for i, def_data in enumerate(defs_data[:5]):
                    definition = def_data.get('definition', '').strip()
                    if not definition:
                        continue
                    c.execute(
                        f'INSERT INTO definitions (word_id, definition, sort_order) VALUES ({ph}, {ph}, {ph})',
                        (word_id, definition, i)
                    )
                    def_result = query_one_fn(
                        conn, c,
                        'SELECT id FROM definitions WHERE word_id=? AND definition=?',
                        (word_id, definition))
                    if not def_result:
                        continue
                    def_id = def_result['id']

                    for j, ex in enumerate(def_data.get('examples', [])):
                        sentence = ex.get('sentence', '').strip()
                        if not sentence:
                            continue
                        c.execute(
                            f'''INSERT INTO examples
                               (definition_id, sentence, source_article, author, dynasty, sort_order)
                               VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph})''',
                            (def_id, sentence,
                             ex.get('source_article', ''),
                             ex.get('author', ''),
                             ex.get('dynasty', ''), j))
                imported += 1
            except Exception as e:
                print(f"  导入失败 [{word}]: {e}")

        commit_func(conn)
        close_conn, close_cur = conn, c
        close_func(close_conn, close_cur)

    print(f"PostgreSQL 模式导入完成：{imported} 个实词")


def _import_sqlite_local(data_list):
    """本地 SQLite 直接导入模式"""
    import sqlite3

    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wenyan.db')
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 建表
    c.execute('''CREATE TABLE IF NOT EXISTS words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT NOT NULL UNIQUE,
        weight REAL DEFAULT 1.0,
        correct_count INTEGER DEFAULT 0,
        wrong_count INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS definitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word_id INTEGER NOT NULL,
        definition TEXT NOT NULL,
        sort_order INTEGER DEFAULT 0,
        FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS examples (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        definition_id INTEGER NOT NULL,
        sentence TEXT NOT NULL,
        source_article TEXT,
        author TEXT,
        dynasty TEXT,
        sort_order INTEGER DEFAULT 0,
        FOREIGN KEY (definition_id) REFERENCES definitions(id) ON DELETE CASCADE
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS game_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        played_at TEXT DEFAULT (datetime('now', 'localtime')),
        total_questions INTEGER DEFAULT 10,
        correct_count INTEGER DEFAULT 0,
        is_perfect INTEGER DEFAULT 0,
        correct_words TEXT,
        wrong_words TEXT
    )''')

    count = c.execute('SELECT COUNT(*) FROM words').fetchone()[0]
    if count > 0:
        print(f"SQLite 中已有 {count} 个实词，跳过初始化")
        conn.close()
        return

    imported = 0
    for word, defs_data in data_list:
        try:
            c.execute('INSERT INTO words (word) VALUES (?)', (word,))
            word_id = c.lastrowid
        except sqlite3.IntegrityError:
            continue

        for i, def_data in enumerate(defs_data[:5]):
            definition = def_data.get('definition', '').strip()
            if not definition:
                continue
            c.execute('INSERT INTO definitions (word_id, definition, sort_order) VALUES (?, ?, ?)',
                      (word_id, definition, i))
            def_id = c.lastrowid

            for j, ex in enumerate(def_data.get('examples', [])):
                sentence = ex.get('sentence', '').strip()
                if not sentence:
                    continue
                c.execute(
                    '''INSERT INTO examples (definition_id, sentence, source_article, author, dynasty, sort_order)
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (def_id, sentence,
                     ex.get('source_article', ''),
                     ex.get('author', ''),
                     ex.get('dynasty', ''), j))
        imported += 1

    conn.commit()
    conn.close()
    print(f"SQLite 本地导入完成：{imported} 个实词")


if __name__ == '__main__':
    # 本地运行时默认用 SQLite 模式
    import_init_data()

    # 验证
    import sqlite3
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wenyan.db')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    words = c.execute('SELECT COUNT(*) FROM words').fetchone()[0]
    defs = c.execute('SELECT COUNT(*) FROM definitions').fetchone()[0]
    exs = c.execute('SELECT COUNT(*) FROM examples').fetchone()[0]
    print(f"\n验证结果：实词 {words} 个，释义 {defs} 条，例句 {exs} 条")

    rows = c.execute('''SELECT w.word, d.definition, e.sentence, e.source_article
        FROM words w JOIN definitions d ON d.word_id = w.id
        LEFT JOIN examples e ON e.definition_id = d.id WHERE w.word="比"
        ORDER BY d.sort_order, e.sort_order LIMIT 5''').fetchall()
    for r in rows:
        print(f"  词:{r[0]} 释义:{r[1]}  例句:{r[2][:30]}... 出处:{r[3]}")
    conn.close()
    print("\n数据初始化完成！")
