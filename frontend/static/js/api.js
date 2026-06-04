/**
 * 文言文实词测试 - API 客户端
 */
const BASE_URL = '';  // 使用相对路径，同源请求

async function apiFetch(path, options = {}) {
    try {
        const resp = await fetch(BASE_URL + path, {
            headers: { 'Content-Type': 'application/json', ...options.headers },
            ...options,
        });
        const data = await resp.json();
        if (!resp.ok) {
            throw new Error(data.error || `HTTP ${resp.status}`);
        }
        return data;
    } catch (err) {
        console.error('API Error:', path, err);
        throw err;
    }
}

const API = {
    // 统计
    getStats: () => apiFetch('/api/stats'),

    // 词库
    getWords: (page = 1, perPage = 20, q = '') => {
        let url = `/api/words?page=${page}&per_page=${perPage}`;
        if (q) url += `&q=${encodeURIComponent(q)}`;
        return apiFetch(url);
    },
    getWord: (id) => apiFetch(`/api/words/${id}`),
    addWord: (data) => apiFetch('/api/words', { method: 'POST', body: JSON.stringify(data) }),
    deleteWord: (id) => apiFetch(`/api/words/${id}`, { method: 'DELETE' }),
    searchExternal: (word) => apiFetch(`/api/words/search-external?word=${encodeURIComponent(word)}`),

    // 游戏
    startGame: () => apiFetch('/api/game/start', { method: 'POST', body: '{}' }),
    submitGame: (results) => apiFetch('/api/game/submit', { method: 'POST', body: JSON.stringify({ results }) }),
    getRecords: (page = 1) => apiFetch(`/api/game/records?page=${page}&per_page=20`),
};
