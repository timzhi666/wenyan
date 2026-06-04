# 文言文实词测试 - Render 免费部署指南

> 预计耗时：**10-15 分钟** | 费用：**完全免费**

---

## 第一步：注册 Render 账号

1. 打开 https://dashboard.render.com
2. 点击 **Sign Up Free**（免费注册）
3. 选择用 **GitHub 账号登录**（推荐，方便后续自动部署）

## 第二步：创建 GitHub 仓库

### 2.1 如果没有 GitHub 账号
1. 打开 https://github.com/signup 注册
2. 完成邮箱验证

### 2.2 创建新仓库
1. 登录 GitHub，点击右上角 **+** → **New repository**
2. 仓库名填：`wenyan-app`（或你喜欢的名字）
3. 选择 **Private**（私有，只有你能看到）
4. **不要勾选** Add a README 等选项
5. 点击 **Create repository**

### 2.3 上传代码到仓库

在本地终端执行以下命令（把代码推送到 GitHub）：

```bash
# 进入项目目录
cd /Users/zhifangzhu/WorkBuddy/2026-06-03-15-29-36/wenyan_app

# 初始化 Git（如果是第一次）
git init
git add .
git commit -m "文言文实词测试 v1.0"

# 关联你的 GitHub 仓库（替换 YOUR_USERNAME 为你的GitHub用户名）
git remote add origin https://github.com/YOUR_USERNAME/wenyan-app.git
git branch -M main
git push -u origin main
```

> 如果提示输入账号密码，使用 GitHub 的 **Personal Access Token**：
> GitHub → Settings → Developer settings → Personal access tokens → Generate new token，勾选 `repo` 权限。

## 第三步：在 Render 上创建 Web 服务

### 3.1 创建 Web Service
1. 在 Render Dashboard 点击 **New +** → **Web Service**
2. 选择 **Connect** 你的 `wenyan-app` 仓库
3. 点击底部 **Connect** 确认

### 3.2 配置构建和启动（关键！）

在配置页面填写以下信息：

| 设置项 | 填写内容 |
|--------|----------|
| **Name** | `wenyan-test`（随意） |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r backend/requirements.txt` |
| **Start Command** | `cd backend && python app.py` |
| **Plan** | 选择 **Free** |

### 3.3 添加免费 PostgreSQL 数据库

1. 在同一个配置页面向下滚动找到 **Database** 区域
2. 点击 **+ Add Database**
3. 类型选择 **PostgreSQL**
4. Plan 选择 **Free**（免费版提供 1GB 存储，完全够用）
5. Region 选择离你近的区域（建议 Singapore 或 Frankfurt）
6. 点击 **Create Database**
7. 创建后，Render 会自动生成一个 **DATABASE_URL** 环境变量

> ⚠️ 重要：确认 DATABASE_URL 已自动添加到 Web Service 的环境变量中。
> 方法：在 Web Service 设置 → Environment 页面查看是否有 `DATABASE_URL` 变量。

### 3.4 设置环境变量

在 Environment 部分确保有：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `PORT` | `10000` | Render 指定的端口 |
| `DATABASE_URL` | （自动填充）| PostgreSQL 连接地址 |

### 3.5 点击 Deploy

点击页面底部的 **Create Web Service** 按钮。

Render 会开始自动构建和部署。首次部署大约需要 **2-3 分钟**。

## 第四步：获取公网访问地址

1. 部署成功后，Render 会显示一个 URL，格式如：
   ```
   https://wenyan-test.onrender.com
   ```

2. 点击这个链接即可访问你的应用！

3. **首次访问会稍慢**（因为要导入146个实词数据到数据库），请耐心等待 10-30 秒。之后每次访问都会很快。

---

## 常见问题

### Q: 首次打开页面显示错误？
A: 正常现象。首次启动时应用正在将 CSV 词库数据导入 PostgreSQL 数据库（约 10-30 秒）。刷新页面即可。

### Q: 免费 Plan 有什么限制？
A:
- **休眠**：15 分钟无人访问后服务会自动"睡眠"
- **唤醒**：有人访问时会在 ~30 秒内重新启动（会看到加载动画）
- **数据不会丢失**：PostgreSQL 是持久化的，游戏记录、答题统计都保留

### Q: 如何避免休眠（保持常在线）？
A: 免费版无法完全避免休眠。如果想 7x24 小时在线，可以升级到 **Starter 计划（$7/月）**。
> 对孩子学习来说，免费版的休眠机制完全够用——每次打开等几秒就好。

### Q: 如何更新词库或修改功能？
A: 只需把修改后的代码 `git push` 到 GitHub，Render 会**自动重新部署**！

### Q: 可以绑定自己的域名吗？
A: 可以！但免费版不支持自定义域名。需升级到 Starter 计划（$7/月）后才能在 Settings → Custom Domain 中设置。

### Q: 数据安全吗？
A: PostgreSQL 数据库是独立存储的，即使重新部署代码也不会丢失数据。但建议定期关注 Render 的免费额度使用情况。

---

## 文件结构说明

```
wenyan_app/
├── backend/
│   ├── app.py              # Flask 主程序（支持 SQLite + PostgreSQL 双模式）
│   ├── init_data.py        # CSV 数据解析与导入脚本
│   ├── data.csv            # 词库数据文件（146个实词）
│   ├── requirements.txt    # Python 依赖
│   └── wenyan.db           # SQLite 数据库（仅本地开发用）
├── frontend/
│   ├── index.html          # 前端主页
│   ├── static/css/style.css
│   └── static/js/{api.js, app.js}
├── render.yaml             # Render 部署配置（可选）
└── .gitignore
```

---

## 一键检查清单

- [ ] GitHub 仓库已创建并推送代码
- [ ] Render 账号已注册（用 GitHub 登录）
- [ ] Web Service 已连接仓库
- [ ] Build Command: `pip install -r backend/requirements.txt`
- [ ] Start Command: `cd backend && python app.py`
- [ ] PostgreSQL 数据库已添加（Free Plan）
- [ ] `DATABASE_URL` 环境变量已自动设置
- [ ] `PORT` 设为 `10000`
- [ ] 点击了 Create Web Service
- [ ] 看到 "Live" 状态 ✅

祝你部署顺利！🎉
