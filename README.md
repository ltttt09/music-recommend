# SoundMind

SoundMind 是一个面向毕设/课程展示的全栈智能音乐推荐平台。后端使用 **Flask**，前端使用 **Vue 3 + Vite**，数据库使用 **SQLite**，推荐引擎包含 6 个模型：**ItemCF**（物品协同过滤）、**UserCF**（用户协同过滤）、**ALS**（隐式反馈矩阵分解）、**Song2Vec**（歌曲向量召回）、**Sequence**（序列行为推荐）和 **Hybrid**（加权融合）。

系统演示重点是：用户登录、浏览歌曲、收藏和反馈、获取可解释推荐、查看相似歌曲、生成歌单、后台查看统计和模型状态。支持离线评估（NDCG、命中率、覆盖率）和公网部署。

## 功能范围

- 用户端：注册登录、歌曲浏览、筛选搜索、歌曲详情、收藏、喜欢/跳过反馈、评论、推荐结果、冷启动选择、生成歌单、我的音乐。
- 推荐端：默认使用 Hybrid 混合推荐，统一返回 `score`、`reason`、`source_models`，并过滤已听、已收藏、已喜欢、已跳过和重复歌曲。
- 后台端：概览统计、用户管理、歌曲管理、反馈统计、评论审核、iTunes 数据状态、推荐日志、模型评估、系统状态、模型重新训练。
- 运行日志：记录播放请求、开始播放、暂停、播放错误、缺少音频、拖动进度、用户反馈等操作状态。
- 数据源：当前只使用 iTunes Search API，优先导入主流歌曲、封面和 30 秒试听地址。
- 封面策略：歌曲无封面时按流派生成稳定渐变封面；中文歌曲不再取中文首字，统一显示音乐符号，避免乱码。

## 项目结构

```text
SoundMind/
├── backend/                 # Flask 后端
│   ├── app/
│   │   ├── main.py          # Flask 应用入口
│   │   ├── api/             # 认证、歌曲、用户、后台 API
│   │   └── services/        # 推荐引擎
│   └── run.py               # 后端启动脚本
├── frontend/                # Vue 3 + Vite 前端
│   ├── src/
│   │   ├── pages/           # 页面
│   │   ├── components/      # 公共组件
│   │   └── cover.js         # 无封面歌曲生成策略
│   └── package.json
├── src/                     # 推荐算法、数据、数据库访问
├── jobs/                    # 数据导入、离线推荐缓存脚本
├── data/                    # SQLite 数据库和离线缓存
├── .vscode/                 # VS Code 运行配置
└── .idea/                   # PyCharm 运行配置
```

## 后台登录

- 后台地址：`http://localhost:5173/#/admin`
- 也可以直接访问 `http://localhost:8000/#/admin`（前端打包后 Flask 同时提供页面和 API，无需启动前端开发服务器）
- 本地演示默认账号：`admin`
- 本地演示默认密码：`admin`
- 修改方式：启动后端前设置环境变量 `SOUNDMIND_ADMIN_USERNAME` 和 `SOUNDMIND_ADMIN_PASSWORD`
- 生产环境要求：设置 `SOUNDMIND_ENV=production` 时必须显式设置 `SOUNDMIND_ADMIN_USERNAME` 和 `SOUNDMIND_ADMIN_PASSWORD`，不能依赖默认账号。

PowerShell 示例：

```powershell
$env:SOUNDMIND_ADMIN_USERNAME="你的后台账号"
$env:SOUNDMIND_ADMIN_PASSWORD="你的后台密码"
python backend/run.py
```

可选安全配置：

```powershell
$env:SOUNDMIND_ENV="production"
$env:SOUNDMIND_CORS_ORIGINS="https://你的前端域名"
$env:SOUNDMIND_TOKEN_TTL_SECONDS="86400"
```

## 命令行运行

建议在项目根目录 `D:\codexProject\SoundMind` 执行。

### 1. 安装后端依赖

```powershell
pip install -r requirements.txt
```

如果使用项目内虚拟环境：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. 启动后端

```powershell
python backend/run.py
```

或：

```powershell
.\.venv\Scripts\python.exe backend/run.py
```

后端默认地址：

```text
http://localhost:8000
```

健康检查：

```text
http://localhost:8000/api/health
```

健康检查会返回推荐引擎状态：

```json
{
  "status": "ok",
  "engine_initialized": true,
  "engine_initializing": false,
  "engine_error": ""
}
```

### 3. 安装前端依赖

```powershell
cd frontend
npm install
```

### 4. 启动前端

```powershell
npm run dev
```

前端默认地址：

```text
http://localhost:5173
```

如果 5173 被占用，Vite 会自动切换到 5174、5175 等端口，以终端输出为准。

## PyCharm 运行后端

项目已提供 PyCharm 运行配置：

```text
.idea/runConfigurations/Backend_Flask.xml
```

打开方式：

1. 用 PyCharm 打开 `D:\codexProject\SoundMind`。
2. 确认 Python 解释器为项目虚拟环境：`D:\codexProject\SoundMind\.venv\Scripts\python.exe`。
3. 在右上角运行配置中选择 `Backend Flask`。
4. 点击运行。

如果 PyCharm 没有自动识别配置，手动新建 Python 配置：

| 配置项 | 值 |
|---|---|
| Name | `Backend Flask` |
| Script path | `D:\codexProject\SoundMind\backend\run.py` |
| Working directory | `D:\codexProject\SoundMind` |
| Python interpreter | `D:\codexProject\SoundMind\.venv\Scripts\python.exe` |
| Environment variables | `SOUNDMIND_ADMIN_USERNAME=admin;SOUNDMIND_ADMIN_PASSWORD=admin` |

注意：后端不是 FastAPI 项目，不要使用 `uvicorn app.main:app` 启动。
另外，`.venv\Scripts\python.exe` 是 Python 解释器二进制文件，只用于配置解释器或执行命令，不要在编辑器中作为源码文件打开。

## VS Code 运行前后端

项目已提供：

```text
.vscode/launch.json
.vscode/tasks.json
```

### 后端

1. 用 VS Code 打开 `D:\codexProject\SoundMind`。
2. 打开“运行和调试”。
3. 选择 `Backend: Flask`。
4. 点击运行。

### 前端

方式一，使用调试配置：

1. 选择 `Frontend: Dev Server`。
2. 点击运行。

方式二，使用终端：

```powershell
cd frontend
npm run dev
```

## 数据源导入

当前采用 **iTunes 单一数据源**：

| 来源 | 用途 | 是否可播放 | 说明 |
|---|---|---|---|
| iTunes Search API | 主流歌曲、封面、试听 | 可播放 30 秒试听 | 当前唯一数据源，不需要密钥 |

复制环境变量示例：

```powershell
copy .env.example .env
```

大批量增量导入 iTunes 试听数据：

```powershell
python jobs/import_itunes_music.py --itunes-target 20000 --itunes-limit-per-query 200
```

当前脚本会使用多国家、多流派、多语言、多艺人关键词组合查询 iTunes，并按 iTunes `trackId` 和歌曲/艺人去重。iTunes 单次查询结果有限，实际新增数量取决于 API 返回和去重结果。

重建音乐数据和模拟行为：

```powershell
python jobs/import_itunes_music.py --reset --itunes-target 3000 --synthetic-users 150
```

清理缺少试听地址的历史歌曲：

```powershell
python jobs/cleanup_unplayable_tracks.py
```

注意：`--reset` 会清空歌曲、播放历史、反馈、收藏、评论和歌单数据，再重新导入，执行前需要确认本地数据可以重建。

## 离线推荐缓存

生成离线推荐候选缓存：

```powershell
python jobs/build_recommend_cache.py --model hybrid --n 50 --limit-users 200
```

输出位置：

```text
data/cache/hybrid_candidates.json
```

该缓存用于展示“离线召回候选”，在线接口仍会结合用户最新反馈、收藏、点踩和画像进行实时过滤与重排。

## 操作日志

前端播放组件会把用户动作写入后端：

```text
POST /api/users/actions
```

后台查看：

```text
GET /api/admin/action-logs
```

主要记录类型：

| 类型 | 说明 |
|---|---|
| `audio_play_request` | 用户点击播放 |
| `audio_loadedmetadata` | 音频元数据加载成功 |
| `audio_playing` | 浏览器实际开始播放 |
| `audio_paused` | 暂停播放 |
| `audio_ended` | 播放结束 |
| `audio_error` | 音频元素报错 |
| `audio_play_error` | 调用 `audio.play()` 失败 |
| `audio_missing_source` | 歌曲缺少可播放地址 |
| `audio_seek` | 用户拖动播放进度 |
| `feedback` | 用户喜欢或跳过 |

这些日志存储在 SQLite 的 `user_action_logs` 表中，后台“操作日志”页面可以筛选查看。

## Redis 使用建议

当前项目默认不依赖 Redis。SQLite + 内存模型适合本地课程展示。

建议在以下场景再引入 Redis：

- 歌曲量达到 5 万首以上，推荐候选和画像读取明显变慢。
- 多用户并发访问，SQLite 写入动作日志和反馈产生锁等待。
- 需要把用户 token、用户画像、热门榜、推荐候选缓存放到内存中。
- 需要异步处理操作日志，例如先写 Redis 队列，再批量落库。

当前阶段更建议先保留 SQLite，使用 `data/cache/` 做离线推荐缓存；后续再将热门榜、用户画像和推荐候选迁移到 Redis。

## 测试和质量检查

后端已经提供最小 pytest 用例，覆盖普通用户越权访问和歌曲状态接口鉴权：

```powershell
.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider
```

后端静态检查：

```powershell
$env:RUFF_CACHE_DIR="$env:TEMP\soundmind-ruff-cache"
.\.venv\Scripts\ruff.exe check backend src jobs
```

前端单元测试：

```powershell
cd frontend
npm run test
```

前端构建：

```powershell
cd frontend
npm run build
```

## 推荐接口

主要接口保持现有路径：

```text
GET  /api/users/{user_id}/recommend?model=hybrid&n=10
GET  /api/tracks/{track_id}/similar?n=10
POST /api/users/feedback
POST /api/users/cold-start/recommend
```

推荐结果包含：

```json
{
  "score": 0.92,
  "reason": "与你偏好的 CN-Pop 风格相似",
  "source_models": ["itemcf", "usercf", "svd", "song2vec", "sequence"]
}
```

## 演示流程

1. 打开前端并注册或登录普通用户。
2. 进入“全部歌曲”，浏览或筛选歌曲。
3. 打开歌曲详情，执行收藏、喜欢、跳过、评论。
4. 进入“个性化推荐”，选择 Hybrid 模型并获取推荐。
5. 点击推荐项的解释按钮，查看推荐理由、来源模型和匹配分数。
6. 在歌曲详情中生成歌单。
7. 进入后台，查看概览、反馈、评论、模型评估和系统状态。

## 常见问题

### 后端端口被占用

检查 8000 端口：

```powershell
netstat -ano | findstr :8000
```

结束对应进程：

```powershell
Stop-Process -Id 进程ID -Force
```

### 前端端口不是 5173

Vite 在端口占用时会自动换端口。以前端终端输出的 `Local:` 地址为准。

### 后台无法登录

确认后端已启动，并确认当前后端环境变量中的 `SOUNDMIND_ADMIN_USERNAME` 和 `SOUNDMIND_ADMIN_PASSWORD`。如果没有设置，本地演示默认账号密码是 `admin/admin`。

### 推荐首次加载较慢

后端启动时会初始化数据库并训练轻量模型。首次运行耗时更长，后续启动会复用已有 SQLite 数据。

### 中文封面显示异常

当前无封面歌曲使用 `frontend/src/cover.js` 生成封面。中文歌曲不使用中文首字作为封面字符，而使用音乐符号，避免字体或编码导致乱码。

## 推荐算法说明

系统包含 6 个推荐模型，分为召回层（5 个独立模型）和融合层（1 个 Hybrid 模型），最终经过重排序返回给用户。

### ItemCF — 物品协同过滤

基于物品之间的相似度推荐。核心思路：如果用户听过歌曲 A，系统找到与 A 最相似的其他歌曲推荐给用户。相似度使用余弦相似度计算，加入了时间衰减（近期播放权重更高）和 shrinkage 修正（减少小样本噪声）。评分公式为归一化加权求和：`score = Σ(sim × weight) / Σ|sim|`。

### UserCF — 用户协同过滤

基于用户之间的相似度推荐。核心思路：找到与目标用户品味最相似的其他用户，把他们喜欢但目标用户没听过的歌曲推荐出来。使用调整余弦相似度（减去用户均值后再计算，消除不同用户播放量差异），同样加入时间衰减。

### ALS — 隐式反馈矩阵分解

基于 Hu, Koren, Volinsky (2008) 的隐式反馈 ALS 算法。不使用显式评分，而是把"播放次数"转化为置信度：`confidence = 1 + α × play_count`。通过交替最小二乘法（ALS）学习用户和歌曲的 50 维隐向量，预测用户对未听歌曲的兴趣程度。参数：α=40，正则化 λ=0.1，迭代 20 次。相比传统 SVD 分解，ALS 能正确处理"未播放 ≠ 不喜欢"的问题。

### Song2Vec — 歌曲向量召回

将用户的播放序列视为"句子"，歌曲视为"词"，使用 Word2Vec 学习每首歌曲的 100 维向量表示。推荐时计算用户画像向量（听过的歌曲向量的时间加权平均，近期歌曲权重更高）与所有候选歌曲的余弦相似度，返回最相似的歌曲。按 60 分钟间隔切分会话，会话内至少 2 首歌才参与训练。

### Sequence — 序列行为推荐

基于马尔可夫链建模歌曲之间的转移概率。使用回退 N-gram 策略：先尝试 3-gram 上下文匹配，未命中则回退到 2-gram，再到 1-gram，最后回退到全局热门。加入 Laplace 平滑（ε=0.1）处理零计数问题。不同长度的上下文按权重融合：3-gram 权重 0.5，2-gram 权重 0.3，1-gram 权重 0.2。

### Hybrid — 加权融合

收集以上 5 个模型各自的推荐候选（每个模型提供 n×4 个候选），使用 rank-based 归一化统一分数尺度（排名第 1 的得 1.0 分，最后一名得 0 分），按权重加权求和。如果多个模型同时推荐了同一首歌曲，给予一致性加权（每多一个模型 +10%）。最终注入 10% 的探索歌曲（随机采样，极低分数）以提升覆盖率。

### 重排序

模型输出经过在线重排序：偏好加权（用户喜欢的歌手/风格加分，不喜欢的风格减分）+ MMR 多样性控制（λ=0.7，70% 相关性 + 30% 多样性，避免推荐列表被同一风格歌曲占满）。

## 离线评估指标

系统内置异步离线评估，使用 leave-one-out 方法：每个用户留最后一首歌作为测试集，用剩余历史训练模型，检查推荐列表是否包含相关歌曲。

| 指标 | 含义 | 当前数据（3 次均值） |
|------|------|---------------------|
| 相关 NDCG@100 | 推荐列表中相关歌曲（同歌手或同风格）的排名质量，IDCG 封顶 2 首 | ~57% |
| 相关命中率@100 | 推荐列表中至少包含 1 首相关歌曲的用户比例 | ~66% |
| 覆盖率 | 所有推荐结果中不同歌曲占可播放歌曲总数的比例 | ~9.8% |

各模型对比（NDCG@100）：

| 模型 | NDCG 范围 | 命中率范围 |
|------|----------|-----------|
| Hybrid | 57–62% | 65–69% |
| Sequence | 58–64% | 70–76% |
| Song2Vec | 60–67% | 55–59% |
| ALS | 56–60% | 66–73% |
| UserCF | 48–58% | 64–70% |
| ItemCF | 42–48% | 58–66% |

在后台"模型训练"面板点击"仅评估"可触发异步评估，实时查看进度和各模型得分。

## 公网访问

通过 localtunnel 可以将本地服务暴露到公网，让其他人直接体验：

### 1. 打包前端

```powershell
cd frontend
npm run build
```

### 2. 启动后端

```powershell
python backend/run.py
```

Flask 在 8000 端口同时提供前端页面和 API。

### 3. 启动隧道

新开一个终端，在项目根目录执行：

```powershell
cd frontend
npx localtunnel --port 8000
```

终端会输出一个类似 `https://xxxx.loca.lt` 的链接，把这个链接发给别人即可访问。

### 注意事项

- 首次访问 localtunnel 链接会看到 IP 验证页面，输入页面显示的 IP 地址后点击继续即可
- 你的电脑必须保持开机且终端不关闭
- 每次重启 localtunnel 地址会变
- 别人注册的账号和产生的数据会存到本地数据库
