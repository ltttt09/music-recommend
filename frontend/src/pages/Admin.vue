<template>
  <div class="container">
    <div v-if="!loggedIn" class="auth-card">
      <h1>管理员登录</h1>
      <p class="desc">请输入管理员账号以访问独立后台控制台</p>
      <form @submit.prevent="doLogin">
        <input v-model.trim="adminUsername" placeholder="管理员账号" autocomplete="username" required />
        <input v-model="password" type="password" placeholder="管理员密码" required />
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" class="btn btn-primary" :disabled="loading">{{ loading ? '验证中...' : '登录' }}</button>
      </form>
      <p class="hint">初始账号：admin / admin，可通过 SOUNDMIND_ADMIN_USERNAME 与 SOUNDMIND_ADMIN_PASSWORD 修改</p>
    </div>

    <div v-else>
      <div class="topbar">
        <div>
          <h1>管理控制台</h1>
          <p class="topbar-sub">SoundMind 演示后台</p>
        </div>
        <div class="topbar-right">
          <button class="theme-btn" @click="toggleAdminTheme" :title="adminIsDark ? '浅色模式' : '深色模式'">
            {{ adminIsDark ? '☀' : '☾' }}
          </button>
          <button class="btn btn-ghost btn-sm" @click="logout">退出登录</button>
        </div>
      </div>

      <div class="tabs">
        <button v-for="t in tabs" :key="t.id" :class="{ active: tab === t.id }" @click="switchTab(t.id)">
          {{ t.label }}
        </button>
      </div>

      <section v-if="tab === 'overview'">
        <div v-if="statsLoading" class="spinner"></div>
        <template v-else>
          <div class="stat-grid">
            <div class="stat-card"><span class="sv">{{ stats.users || 0 }}</span><span class="sl">用户数</span></div>
            <div class="stat-card"><span class="sv">{{ stats.tracks || 0 }}</span><span class="sl">歌曲数</span></div>
            <div class="stat-card"><span class="sv">{{ stats.listens || 0 }}</span><span class="sl">播放记录</span></div>
            <div class="stat-card"><span class="sv like">{{ stats.likes || 0 }}</span><span class="sl">喜欢数</span></div>
            <div class="stat-card"><span class="sv dislike">{{ stats.dislikes || 0 }}</span><span class="sl">黑名单数</span></div>
            <div class="stat-card"><span class="sv">{{ stats.comments || 0 }}</span><span class="sl">评论数</span></div>
          </div>
          <div class="admin-actions">
            <button class="btn btn-primary btn-sm" @click="seedEngagement" :disabled="seedLoading">
              {{ seedLoading ? '生成中...' : '生成演示点赞和评论' }}
            </button>
            <span v-if="seedMsg" class="seed-msg">{{ seedMsg }}</span>
          </div>
          <div class="overview-rank-layout">
            <section ref="playRankPanel" class="play-rank-panel">
              <div class="rank-section-head">
                <div>
                  <h2>播放量排行榜</h2>
                  <p>按用户真实播放记录统计，展示 Top 10 歌曲。</p>
                </div>
                <span>Top 10</span>
              </div>
              <div v-if="podiumTracks.length" class="podium">
                <router-link
                  v-for="entry in podiumTracks"
                  :key="entry.rank + '-' + (entry.track.id || entry.track.title)"
                  class="podium-item"
                  :class="entry.tone"
                  :to="adminTrackLink(entry.track)"
                >
                  <div class="podium-cover" :style="adminRankCoverStyle(entry.track, entry.rank)">
                    <img v-if="entry.track.image_url" :src="entry.track.image_url" alt="" referrerpolicy="no-referrer" />
                    <span v-else class="podium-char">{{ adminRankCoverChar(entry.track) }}</span>
                  </div>
                  <div class="podium-medal">{{ entry.rank }}</div>
                  <div class="podium-info">
                    <div class="podium-title">{{ entry.track.title || '未知歌曲' }}</div>
                    <div class="podium-artist">{{ entry.track.artist || entry.track.artist_name || '未知艺人' }}</div>
                    <div class="podium-count">{{ rankCount(entry.track) }} 次播放</div>
                  </div>
                </router-link>
              </div>
              <p v-else class="empty-mini">暂无播放排行数据</p>

              <div class="rank-list-section">
                <h3>第 4-10 名</h3>
                <div v-if="playRankRows.length" class="rank-list">
                  <router-link
                    v-for="row in playRankRows"
                    :key="row.rank + '-' + (row.track.id || row.track.title)"
                    class="rank-row"
                    :to="adminTrackLink(row.track)"
                  >
                    <span class="rank-pos">{{ row.rank }}</span>
                    <span class="rank-mini-cover" :style="adminRankCoverStyle(row.track, row.rank)">
                      <img v-if="row.track.image_url" :src="row.track.image_url" alt="" referrerpolicy="no-referrer" />
                      <span v-else>{{ adminRankCoverChar(row.track) }}</span>
                    </span>
                    <span class="rank-main">
                      <b>{{ row.track.title || '未知歌曲' }}</b>
                      <small>{{ row.track.artist || row.track.artist_name || '未知艺人' }}</small>
                    </span>
                    <span class="rank-value">{{ rankCount(row.track) }} 次</span>
                    <span class="rank-bar"><span class="rank-bar-fill" :style="{ width: rankPercent(row.track) }"></span></span>
                  </router-link>
                </div>
                <p v-else class="empty-mini">暂无第 4-10 名数据</p>
              </div>
            </section>

            <section
              class="genre-panel"
              :style="genrePanelHeight ? { height: genrePanelHeight + 'px', maxHeight: genrePanelHeight + 'px' } : null"
            >
              <div class="rank-section-head compact">
                <div>
                  <h2>流派分布</h2>
                  <p>歌曲库主要流派占比。</p>
                </div>
              </div>
              <div class="genre-bars">
                <div v-for="g in genreDistribution" :key="g.genre" class="genre-row">
                  <span class="genre-label">{{ g.genre }}</span>
                  <div class="bar-track"><div class="bar-fill" :style="{ width: barWidth(g.cnt) + '%' }"></div></div>
                  <span class="genre-cnt">{{ g.cnt }}</span>
                </div>
              </div>
            </section>
          </div>

          <div class="rank-grid">
            <section v-for="card in metricRankCards" :key="card.key" class="rank-card">
              <div class="rank-card-head">
                <h3>{{ card.title }}</h3>
                <span>Top {{ card.items.length }}</span>
              </div>
              <div v-if="card.items.length" class="rank-card-list">
                <router-link
                  v-for="(track, index) in card.items"
                  :key="card.key + '-' + (track.id || track.title || index)"
                  :to="adminTrackLink(track)"
                  class="rank-card-row"
                >
                  <span class="rank-card-pos" :class="{ top: index === 0 }">{{ index + 1 }}</span>
                  <span class="rank-card-cov" :style="adminRankCoverStyle(track, index + 1)">
                    <img v-if="track.image_url" :src="track.image_url" alt="" referrerpolicy="no-referrer" />
                    <span v-else>{{ adminRankCoverChar(track) }}</span>
                  </span>
                  <span class="rank-card-main">
                    <b>{{ track.title || '未知歌曲' }}</b>
                    <small>{{ track.artist || track.artist_name || '未知艺人' }}</small>
                  </span>
                  <span class="rank-card-metric">{{ rankCount(track) }} {{ card.suffix }}</span>
                </router-link>
              </div>
              <p v-else class="empty-mini">暂无{{ card.title }}数据</p>
            </section>
          </div>
        </template>
      </section>

      <section v-if="tab === 'users'">
        <div class="toolbar">
          <input v-model="userSearch" placeholder="搜索用户名或显示名..." class="search-input" @keyup.enter="loadUsers(1)" />
          <select v-model="userGenreFilter" class="search-input compact-input" @change="loadUsers(1)">
            <option value="">全部流派</option>
            <option v-for="g in adminGenreList" :key="g" :value="g">{{ g }}</option>
          </select>
          <select v-model="userSortBy" class="search-input compact-input" @change="loadUsers(1)">
            <option value="id">ID</option>
            <option value="username">用户名</option>
            <option value="join_date">注册时间</option>
          </select>
          <select v-model="userSortOrder" class="search-input compact-input" @change="loadUsers(1)">
            <option value="asc">升序</option>
            <option value="desc">降序</option>
          </select>
          <button class="btn btn-primary btn-xs" @click="loadUsers(1)">搜索</button>
          <button class="btn btn-ghost btn-xs" v-if="userSearch || userGenreFilter" @click="userSearch=''; userGenreFilter=''; loadUsers(1)">清除</button>
        </div>
        <div v-if="usersLoading" class="spinner"></div>
        <table v-else class="data-table">
          <thead><tr><th>ID</th><th>用户名</th><th>显示名称</th><th>偏好流派</th><th>注册时间</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="u in userList" :key="u.id">
              <td>{{ u.id }}</td><td>{{ u.username }}</td><td>{{ u.display_name }}</td>
              <td>{{ u.preferred_genres || '-' }}</td><td>{{ u.join_date?.slice(0, 10) }}</td>
              <td><button class="btn btn-dislike btn-xs" @click="deleteUser(u.id)">删除</button></td>
            </tr>
          </tbody>
        </table>
        <Pagination :current="usersPage" :total="usersMaxPage" :total-items="usersTotal" item-name="个用户" @page-change="loadUsers" />
      </section>

      <section v-if="tab === 'tracks'">
        <div class="toolbar">
          <input v-model="trackSearch" placeholder="搜索歌曲或艺人..." class="search-input" @keyup.enter="resetTrackPage" />
          <select v-model="trackSortBy" @change="resetTrackPage">
            <option value="id">ID</option>
            <option value="popularity">热度</option>
            <option value="year">年份</option>
            <option value="title">歌名</option>
            <option value="artist">艺人</option>
            <option value="genre">流派</option>
            <option value="created">新增时间</option>
          </select>
          <select v-model="trackSortOrder" @change="resetTrackPage">
            <option value="asc">升序</option>
            <option value="desc">降序</option>
          </select>
          <button class="btn btn-primary btn-sm" @click="resetTrackPage">搜索</button>
        </div>
        <div v-if="tracksLoading" class="spinner"></div>
        <table v-else class="data-table">
          <thead><tr><th>ID</th><th>歌曲名</th><th>艺人</th><th>专辑</th><th>流派</th><th>年份</th><th>来源</th><th>音频</th><th>封面</th><th>试听</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="t in trackList" :key="t.id">
              <td>{{ t.id }}</td><td class="td-title">{{ t.title }}</td><td>{{ t.artist_name }}</td>
              <td class="td-album">{{ t.album || '-' }}</td><td>{{ t.genre || '-' }}</td><td>{{ t.year || '-' }}</td>
              <td>{{ t.source || 'itunes' }}</td><td>{{ t.audio_type || 'preview' }}</td>
              <td><span :class="t.image_url ? 'badge-ok' : 'badge-no'">{{ t.image_url ? '有' : '无' }}</span></td>
              <td><span :class="t.preview_url ? 'badge-ok' : 'badge-no'">{{ t.preview_url ? '有' : '无' }}</span></td>
              <td class="row-actions">
                <button class="btn btn-ghost btn-xs" @click="openEdit(t)">编辑</button>
                <button class="btn btn-dislike btn-xs" @click="deleteTrack(t.id)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
        <Pagination :current="trackPage" :total="trackMaxPage" :total-items="trackTotal" @page-change="loadTracks" />
      </section>

      <section v-if="tab === 'comments'">
        <div class="admin-actions" style="margin-bottom:12px">
          <input v-model="commentSearch" placeholder="搜索评论内容、用户、歌曲..." class="search-input" @keyup.enter="loadComments(1)" style="width:260px" />
          <button class="btn btn-primary btn-xs" @click="loadComments(1)">搜索</button>
          <button v-if="commentSearch" class="btn btn-xs" @click="commentSearch='';loadComments(1)">清除</button>
        </div>
        <div v-if="commentsLoading" class="spinner"></div>
        <table v-else class="data-table">
          <thead><tr><th>序号</th><th>用户</th><th>歌曲</th><th>内容</th><th>时间</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="(c, idx) in commentList" :key="c.id">
              <td>{{ commentsTotal - (commentsPage - 1) * commentsSize - idx }}</td>
              <td>{{ c.display_name || c.username }}</td>
              <td class="td-title">{{ c.track_title }}</td>
              <td class="td-comment">{{ c.content }}</td>
              <td>{{ c.created_at?.slice(0, 16) }}</td>
              <td><button class="btn btn-dislike btn-xs" @click="deleteComment(c.id)">删除</button></td>
            </tr>
          </tbody>
        </table>
        <Pagination :current="commentsPage" :total="commentsMaxPage" :total-items="commentsTotal" item-name="条评论" @page-change="loadComments" />
      </section>

      <section v-if="tab === 'data'">
        <div class="admin-actions">
          <template v-if="!itunesImporting">
            <input v-model.number="itunesTarget" type="number" min="100" max="50000" step="1000" class="search-input" style="width:100px" placeholder="数量" />
            <button class="btn btn-primary btn-sm" @click="startItunesImport">
              导入 iTunes 数据
            </button>
            <span class="note" style="margin-left:4px">目标数量（100-50000）</span>
          </template>
          <template v-else>
            <button class="btn btn-danger btn-sm" @click="cancelItunesImport">取消导入</button>
            <span class="seed-msg">{{ itunesImportMsg }}</span>
          </template>
        </div>
        <div v-if="itunesImporting" class="import-progress">
          <p>已导入 {{ itunesImportProgress.imported || 0 }} / {{ itunesImportProgress.target || 0 }} 首，查询 {{ itunesImportProgress.queries || 0 }} 组
            <span v-if="itunesImportProgress.status === 'cancelled'" style="color:#E53935;font-weight:bold">（已取消）</span>
          </p>
          <div class="progress-bar"><div class="progress-fill" :style="{ width: importPercent + '%' }"></div></div>
        </div>
        <div v-if="dataLoading" class="spinner"></div>
        <template v-else>
          <div class="section">
            <h2>iTunes 数据概览</h2>
            <p class="note">当前用户端仅使用 iTunes 30 秒试听数据，其他旧数据源不再作为前台入口展示。</p>
            <table class="data-table">
              <thead><tr><th>数据源</th><th>歌曲数</th><th>可播放</th><th>完整音频</th></tr></thead>
              <tbody>
                <tr v-for="s in itunesSources" :key="s.source">
                  <td>{{ s.source || 'itunes' }}</td>
                  <td>{{ s.tracks }}</td>
                  <td>{{ s.playable }}</td>
                  <td>{{ s.full_audio }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="section">
            <h2>最近导入记录</h2>
            <table class="data-table">
              <thead><tr><th>时间</th><th>来源</th><th>状态</th><th>数量</th><th>说明</th></tr></thead>
              <tbody>
                <tr v-for="r in itunesImportRuns" :key="r.id">
                  <td>{{ r.created_at?.slice(0, 16) }}</td>
                  <td>{{ r.source }}</td>
                  <td>{{ r.status }}</td>
                  <td>{{ r.imported_tracks }}</td>
                  <td class="td-comment">{{ r.message }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
      </section>

      <section v-if="tab === 'actions'">
        <div class="toolbar">
          <select v-model="actionFilter" class="search-input" @change="loadActionLogs">
            <option value="">全部动作</option>
            <option value="audio_play_request">播放请求</option>
            <option value="audio_playing">开始播放</option>
            <option value="audio_paused">暂停播放</option>
            <option value="audio_ended">播放结束</option>
            <option value="audio_error">播放错误</option>
            <option value="audio_missing_source">缺少音频</option>
            <option value="audio_seek">拖动进度</option>
            <option value="feedback">用户反馈</option>
          </select>
          <select v-model="actionStatus" class="search-input compact-input" @change="loadActionLogs">
            <option value="">全部状态</option>
            <option value="requested">请求</option>
            <option value="success">成功</option>
            <option value="error">错误</option>
            <option value="blocked">阻止</option>
          </select>
          <input v-model="actionSearch" placeholder="搜索说明、页面或对象 ID" class="search-input" @keyup.enter="loadActionLogs" />
          <button class="btn btn-primary btn-sm" @click="loadActionLogs">刷新</button>
        </div>
        <div v-if="actionLogsLoading" class="spinner"></div>
        <table v-else class="data-table">
          <thead><tr><th>时间</th><th>用户</th><th>动作</th><th>对象</th><th>状态</th><th>说明</th><th>页面</th></tr></thead>
          <tbody>
            <tr v-for="r in actionLogList" :key="r.id">
              <td>{{ r.created_at?.slice(0, 16) }}</td>
              <td>{{ r.display_name || r.username || r.session_id || '-' }}</td>
              <td>{{ actionLabel(r.action_type) }}</td>
              <td>{{ r.entity_type || '-' }} #{{ r.entity_id || '-' }}</td>
              <td>{{ r.status || '-' }}</td>
              <td class="td-comment">{{ r.message }}</td>
              <td class="td-comment">{{ r.page_url }}</td>
            </tr>
          </tbody>
        </table>
        <Pagination :current="actionLogsPage" :total="actionLogsMaxPage" :total-items="actionLogsTotal" item-name="条日志" @page-change="loadActionLogs" />
      </section>

      <section v-if="tab === 'models'">
        <div class="model-dashboard">
          <div class="models-header">
            <h2>🧠 <span>模型管理中心</span></h2>
            <div class="models-header-actions">
              <button class="btn btn-ghost" @click="exportModelReport" :disabled="!modelCards.length">导出评估报告</button>
              <button class="btn btn-primary" @click="startTraining" :disabled="retraining">
                {{ retraining ? '训练中...' : '一键全量训练' }}
              </button>
            </div>
          </div>

          <div class="models-status-bar">
            <div class="models-status-main">
              <span :class="['models-status-pill', modelStatusClass]">{{ modelStatusText }}</span>
              <div>
                <h2>模型管理中心</h2>
                <p>查看推荐模型指标、执行离线评估，并调整前端展示用的混合权重。</p>
              </div>
            </div>
            <div class="models-status-side">
              <span><b>{{ loadedModelCount }}</b><small>加载模型</small></span>
              <span><b>{{ metrics.sample_users || 0 }}</b><small>样本用户</small></span>
              <span><b>{{ percent(metrics.related_hit_rate_at_100 ?? metrics.hit_rate_at_100) }}</b><small>相关命中率@100</small></span>
              <span><b>{{ percent(metrics.related_ndcg_at_100 ?? metrics.ndcg_at_100) }}</b><small>相关NDCG@100</small></span>
              <button class="btn btn-ghost" @click="loadMetrics" :disabled="metricsLoading || metricsRefreshing">
                {{ metricsRefreshing ? '刷新中...' : '刷新指标' }}
              </button>
            </div>
          </div>

          <div v-if="metricsError" class="error-msg">{{ metricsError }}</div>
          <p v-if="retrainMsg" class="retrain-msg" :class="retrainOk ? 'success' : 'error'">{{ retrainMsg }}</p>
          <p v-if="modelWeightSavedMsg" class="retrain-msg success">{{ modelWeightSavedMsg }}</p>

          <div class="models-grid">
            <article v-for="(item, index) in modelCards" :key="item.model" :class="['models-card', modelToneClass(index), { expanded: expandedModel === item.model }]" @click="toggleModelExpanded(item.model)">
              <div class="models-card-head">
                <span class="models-card-icon">{{ modelIcon(item.model) }}</span>
                <span :class="['models-card-badge', item.loaded ? 'active' : 'idle']">{{ item.loaded ? '已加载' : '待评估' }}</span>
              </div>
              <h3>{{ modelLabel(item.model) }}</h3>
              <p>{{ modelDescription(item.model) }}</p>
              <div class="models-card-stats">
                <span>
                  <b>{{ item.related_hits ?? item.hits }}<small style="font-size:.6em;opacity:.6">/{{ item.cases }}</small></b>
                  <small>相关命中数</small>
                </span>
                <span>
                  <b>{{ percent(item.related_hit_rate_at_100 ?? item.hit_rate_at_100) }}</b>
                  <small>相关命中率@100</small>
                </span>
                <span>
                  <b>{{ percent(item.related_ndcg_at_100 ?? item.ndcg_at_100) }}</b>
                  <small>相关NDCG@100</small>
                </span>
              </div>
              <div class="models-weight-line">
                <div>
                  <small>{{ item.model === 'hybrid' ? '融合输出' : '混合权重' }}</small>
                  <b>{{ item.weight }}%</b>
                </div>
                <div class="models-weight-track">
                  <span :style="{ width: item.weight + '%' }"></span>
                </div>
              </div>
              <button class="models-expand-btn" type="button" @click.stop="toggleModelExpanded(item.model)">
                {{ expandedModel === item.model ? '收起详情' : '展开详情' }}
              </button>
              <div v-show="expandedModel === item.model" class="models-detail-grid">
                <span><b>{{ item.related_hits ?? item.hits }}/{{ item.cases }}</b><small>相关命中/样本</small></span>
                <span><b>{{ percent(item.related_hit_rate_at_100 ?? item.hit_rate_at_100) }}</b><small>相关命中率@100</small></span>
                <span><b>{{ percent(item.related_ndcg_at_100 ?? item.ndcg_at_100) }}</b><small>相关NDCG@100</small></span>
                <span><b>{{ percent(item.coverage ?? item.coverage_percent) }}</b><small>覆盖率</small></span>
              </div>
            </article>
          </div>

          <div v-show="showTrainProgress" class="models-progress-panel" :class="{ done: trainDone && !retraining && !metricsLoading }">
            <div class="progress-ring" :class="{ done: trainDone && !retraining && !metricsLoading }" :style="{ '--p': trainPercent + '%' }">
              <span v-if="trainDone && !retraining && !metricsLoading">✓</span>
              <span v-else>{{ trainPercent.toFixed(0) }}%</span>
            </div>
            <div class="progress-body">
              <h3>{{ trainProgressTitle }}</h3>
              <p>{{ trainProgressDesc }}</p>
              <div class="progress-track" :class="{ striped: trainProgress.running }"><div class="progress-fill" :class="{ done: trainDone && !retraining && !metricsLoading }" :style="{ width: trainPercent + '%' }"></div></div>
              <div class="progress-meta">
                <span>模型 {{ trainProgress.current_model || metricJob?.current_model || '-' }}</span>
                <span>步骤 {{ trainProgress.total_models || modelCards.length || 0 }}</span>
                <span>耗时 {{ metricElapsed }}</span>
              </div>
              <div class="tp-log" ref="trainLogBox">
                <div v-for="log in trainingLogs" :key="log.id" :class="['line', log.cls]">
                  {{ log.cls === 'done' ? '✓' : log.cls === 'warn' ? '!' : '→' }} [{{ log.time }}] {{ log.text }}
                </div>
              </div>
            </div>
          </div>

          <div class="models-console-grid">
            <section class="models-panel models-training">
              <div class="models-panel-head">
                <h3>训练控制台</h3>
                <span>{{ metrics.type || '快速指标' }}</span>
              </div>
              <div class="train-config">
                <label class="config-item">
                  <span>训练范围</span>
                  <select v-model="trainConfig.scope" @change="trainScopeChanged">
                    <option value="all">全部模型</option>
                    <option value="hybrid">混合推荐</option>
                    <option value="itemcf">物品协同过滤</option>
                    <option value="usercf">用户协同过滤</option>
                    <option value="svd">矩阵分解 SVD</option>
                    <option value="song2vec">歌曲向量</option>
                    <option value="sequence">序列推荐</option>
                  </select>
                </label>
                <label class="config-item">
                  <span>数据分割</span>
                  <select v-model="trainConfig.split">
                    <option value="holdout">最近一次留出</option>
                    <option value="random">随机留出</option>
                    <option value="time">时间切分</option>
                  </select>
                </label>
                <label>
                  <span>最小交互数</span>
                  <input v-model.number="trainConfig.minInteractions" type="number" min="1" max="20" />
                </label>
                <label>
                  <span>随机种子</span>
                  <input v-model.number="trainConfig.seed" type="number" min="1" max="999999" />
                </label>
              </div>
              <div class="train-actions">
                <div class="train-options">
                  <label class="switch-row">
                    <button type="button" :class="['switch', { on: trainConfig.incremental }]" @click="toggleIncremental"></button>
                    <span>增量训练</span>
                  </label>
                  <label class="sample-control">
                    评估样本
                    <input v-model.number="metricSampleUsers" type="number" min="1" :max="stats.users || 300" />
                    <span class="note" style="font-size:11px">当前用户总数：{{ stats.users || '-' }}</span>
                  </label>
                </div>
                <div class="train-buttons">
                  <button class="btn btn-primary" @click="startTraining" :disabled="retraining || metricsLoading">
                    {{ retraining ? '训练中...' : '开始训练' }}
                  </button>
                  <button class="btn btn-ghost" @click="startMetricsEvaluation" :disabled="metricsLoading || retraining">
                    {{ metricsLoading ? '评估中...' : '仅评估' }}
                  </button>
                  <button class="btn btn-danger" @click="resetAllModels" :disabled="retraining || metricsLoading">
                    重置所有模型
                  </button>
                </div>
              </div>
              <div class="models-log-list">
                <div v-for="log in modelTrainingLogs" :key="log.id" class="models-log-row">
                  <span>{{ log.time }}</span>
                  <b>{{ log.type }}</b>
                  <small>{{ log.message }}</small>
                </div>
              </div>
            </section>

            <section class="models-panel models-weight-panel">
              <div class="models-panel-head">
                <h3>混合权重配置</h3>
                <span>后端保存</span>
              </div>
              <div class="models-slider-list">
                <label v-for="row in modelWeightRows" :key="row.key" class="models-slider-row">
                  <span>{{ row.label }}</span>
                  <input v-model.number="modelWeights[row.key]" type="range" min="0" max="100" />
                  <b>{{ modelWeights[row.key] }}%</b>
                </label>
              </div>
              <button class="btn btn-primary models-save-btn" @click="saveModelWeights">保存权重</button>
            </section>
          </div>

          <section class="models-panel">
            <div class="models-panel-head">
              <h3>离线评估对比</h3>
              <span>{{ sortedEvaluationRows.length }} 个模型</span>
            </div>
            <table v-if="sortedEvaluationRows.length" class="eval-table">
              <thead>
                <tr>
                  <th @click="sortEvaluation('model')">模型{{ sortMark('model') }}</th>
                  <th @click="sortEvaluation('related_hit_rate_at_100')">命中率@100{{ sortMark('related_hit_rate_at_100') }}</th>
                  <th @click="sortEvaluation('related_ndcg_at_100')">NDCG@100{{ sortMark('related_ndcg_at_100') }}</th>
                  <th @click="sortEvaluation('coverage')">覆盖率{{ sortMark('coverage') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in sortedEvaluationRows" :key="row.model">
                  <td><b>{{ modelLabel(row.model) }}</b></td>
                  <td><div class="eval-bar-wrap"><span class="eval-bar"><span class="eval-bar-fill hitrate" :style="{ width: evalBarWidth(row, 'related_hit_rate_at_100') }"></span></span><b class="eval-val">{{ percent(row.related_hit_rate_at_100 ?? row.hit_rate_at_100) }}</b></div></td>
                  <td><div class="eval-bar-wrap"><span class="eval-bar"><span class="eval-bar-fill precision" :style="{ width: evalBarWidth(row, 'related_ndcg_at_100') }"></span></span><b class="eval-val">{{ percent(row.related_ndcg_at_100 ?? row.ndcg_at_100) }}</b></div></td>
                  <td>{{ row.coverage > 1 ? row.coverage.toFixed(1) + '%' : percent(row.coverage) }}</td>
                </tr>
              </tbody>
            </table>
            <p v-else class="empty-mini">暂无模型指标。</p>
          </section>
        </div>
      </section>

      <section v-if="tab === 'system'">
        <div v-if="sysLoading" class="spinner"></div>
        <template v-else>
          <div class="stat-grid stat-grid-sm">
            <div class="stat-card"><span class="sv">{{ formatUptime(sysData.uptime_seconds) }}</span><span class="sl">运行时间</span></div>
            <div class="stat-card"><span class="sv">{{ sysData.memory_mb }} MB</span><span class="sl">内存</span></div>
            <div class="stat-card"><span class="sv">{{ sysData.cpu_percent }}%</span><span class="sl">CPU</span></div>
            <div class="stat-card"><span class="sv">{{ sysData.models_loaded?.length || 0 }}</span><span class="sl">模型数</span></div>
          </div>
          <div class="section">
            <h2>系统信息</h2>
            <p class="system-text">{{ sysData.python_version }}</p>
          </div>
        </template>
      </section>
    </div>

    <div v-if="editTrack" class="modal-mask" @click.self="closeEdit">
      <form class="edit-modal" @submit.prevent="saveTrack">
        <div class="modal-head">
          <h2>编辑歌曲</h2>
          <button type="button" class="modal-close" @click="closeEdit">×</button>
        </div>
        <label>歌曲名<input v-model="editForm.title" required /></label>
        <label>专辑<input v-model="editForm.album" /></label>
        <div class="form-grid">
          <label>年份<input v-model.number="editForm.year" type="number" /></label>
          <label>流派<input v-model="editForm.genre" /></label>
          <label>热度<input v-model.number="editForm.popularity" type="number" step="0.1" /></label>
        </div>
        <label>封面地址<input v-model="editForm.image_url" /></label>
        <label>试听地址<input v-model="editForm.preview_url" /></label>
        <p v-if="editError" class="error">{{ editError }}</p>
        <div class="modal-actions">
          <button type="button" class="btn btn-ghost" @click="closeEdit">取消</button>
          <button type="submit" class="btn btn-primary" :disabled="savingTrack">{{ savingTrack ? '保存中...' : '保存' }}</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { computed, h, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import Pagination from '../components/Pagination.vue'

const AdminRank = {
  props: { title: String, items: Array, suffix: String },
  setup(props) {
    function formatCount(value) {
      const n = Number(value) || 0
      return Number.isInteger(n) ? n : n.toFixed(1)
    }
    function width(value) {
      const rows = props.items || []
      const max = Math.max(...rows.map((row) => Number(row.cnt) || 0), 1)
      return `${Math.max(4, ((Number(value) || 0) / max) * 100)}%`
    }
    function coverText(track, index) {
      const title = String(track.title || '').trim()
      if (!title) return index + 1
      const first = title.charAt(0)
      return /[^\x00-\x7F]/.test(first) ? '♪' : first.toUpperCase()
    }
    return () => h('div', { class: 'section rank-box rank-card-box' }, [
      h('div', { class: 'rank-box-head' }, [
        h('h2', props.title),
        h('span', `${props.items?.length || 0} 条`),
      ]),
      props.items?.length
        ? h('div', { class: 'rank-card-list' }, props.items.map((t, i) => h('div', { key: i, class: 'rank-card-row' }, [
            h('span', { class: ['rank-medal', i < 3 ? 'top' : ''] }, i + 1),
            h('span', { class: 'rank-cover-mini' }, coverText(t, i)),
            h('span', { class: 'rank-main' }, [
              h('b', t.title || '未知歌曲'),
              h('small', t.artist || t.artist_name || '未知艺人'),
            ]),
            h('span', { class: 'rank-metric' }, `${formatCount(t.cnt)} ${props.suffix}`),
            h('span', { class: 'rank-meter' }, [
              h('span', { class: 'rank-meter-fill', style: { width: width(t.cnt) } }),
            ]),
          ])))
        : h('p', { class: 'empty-mini' }, '暂无数据'),
    ])
  },
}

const ADMIN_TOKEN_KEY = 'soundmind_admin_token'
const ADMIN_USERNAME_KEY = 'soundmind_admin_username'
const adminUsername = ref(sessionStorage.getItem(ADMIN_USERNAME_KEY) || 'admin')
const password = ref('')
const error = ref('')
const loading = ref(false)
const loggedIn = ref(false)
const adminIsDark = ref(true)
const tab = ref('overview')
let adminToken = sessionStorage.getItem(ADMIN_TOKEN_KEY) || ''

function toggleAdminTheme() {
  adminIsDark.value = !adminIsDark.value
  document.documentElement.setAttribute('data-theme', adminIsDark.value ? 'dark' : 'light')
  localStorage.setItem('theme', adminIsDark.value ? 'dark' : 'light')
}

const tabs = [
  { id: 'overview', label: '概览' },
  { id: 'users', label: '用户' },
  { id: 'tracks', label: '歌曲' },
  { id: 'comments', label: '评论' },
  { id: 'data', label: 'iTunes数据' },
  { id: 'actions', label: '操作日志' },
  { id: 'models', label: '模型' },
  { id: 'system', label: '系统' },
]

const stats = ref({})
const statsLoading = ref(false)
const userList = ref([])
const usersLoading = ref(false)
const usersPage = ref(1)
const usersSize = ref(20)
const usersTotal = ref(0)
const userSearch = ref('')
const userGenreFilter = ref('')
const userSortBy = ref('id')
const userSortOrder = ref('asc')
const adminGenreList = ref([])
const trackList = ref([])
const tracksLoading = ref(false)
const trackSearch = ref('')
const trackTotal = ref(0)
const trackPage = ref(1)
const trackSize = ref(50)
const trackSortBy = ref('id')
const trackSortOrder = ref('asc')
const fbData = reactive({ total_likes: 0, total_dislikes: 0, top_liked: [], top_disliked: [] })
const feedbackLoading = ref(false)
const commentList = ref([])
const commentsTotal = ref(0)
const commentsLoading = ref(false)
const commentsPage = ref(1)
const commentsSize = ref(20)
const commentSearch = ref("")
const dataSources = reactive({ sources: [], import_runs: [] })
const dataLoading = ref(false)
const itunesImporting = ref(false)
const itunesImportMsg = ref('')
const itunesTarget = ref(5000)
const itunesImportProgress = reactive({ imported: 0, queries: 0, target: 0, running: false, error: '' })
const importPercent = computed(() => {
  if (!itunesImportProgress.target) return 0
  return Math.min(100, Math.round(itunesImportProgress.imported / itunesImportProgress.target * 100))
})
const logList = ref([])
const logsTotal = ref(0)
const logsLoading = ref(false)
const logSearch = ref('')
const logModel = ref('')
const logsPage = ref(1)
const logsSize = ref(20)
const actionLogList = ref([])
const actionLogsTotal = ref(0)
const actionLogsLoading = ref(false)
const actionLogsPage = ref(1)
const actionLogsSize = ref(20)
const actionFilter = ref('')
const actionStatus = ref('')
const actionSearch = ref('')
const metrics = ref({})
const metricsLoading = ref(false)
const metricsRefreshing = ref(false)
const metricsError = ref('')
const metricJob = ref(null)
const metricSampleUsers = ref(50)
let metricsPollTimer = null
let rankResizeObserver = null
let rankResizeFrame = 0
const sysData = reactive({ uptime_seconds: 0, memory_mb: 0, cpu_percent: 0, models_loaded: [], python_version: '' })
const sysLoading = ref(false)
const retraining = ref(false)
const retrainMsg = ref('')
const retrainOk = ref(false)
const seedLoading = ref(false)
const seedMsg = ref('')
const editTrack = ref(null)
const editForm = reactive({ title: '', album: '', year: 0, genre: '', popularity: 0, image_url: '', preview_url: '' })
const editError = ref('')
const savingTrack = ref(false)
const playRankPanel = ref(null)
const genrePanelHeight = ref(0)
const MODEL_ORDER = ['hybrid', 'itemcf', 'usercf', 'svd', 'song2vec', 'sequence']
const MODEL_WEIGHT_KEYS = ['itemcf', 'usercf', 'svd', 'song2vec', 'sequence']
const MODEL_WEIGHT_DEFAULTS = { itemcf: 25, usercf: 15, svd: 25, song2vec: 15, sequence: 20 }
const MODEL_DESCRIPTIONS = {
  hybrid: '多模型融合推荐，统一召回结果并做二次排序。',
  itemcf: '基于物品相似度推荐，适合从已听歌曲扩展相近歌曲。',
  usercf: '基于用户相似度推荐，利用相似用户的听歌行为召回歌曲。',
  svd: '矩阵分解隐语义模型，用低维向量表达用户和歌曲偏好。',
  song2vec: '歌曲向量召回模型，利用序列共现关系学习歌曲相似度。',
  sequence: '序列行为推荐模型，根据近期播放顺序预测下一批候选。',
}
const MODEL_ICONS = { hybrid: '融合', itemcf: '物品', usercf: '用户', svd: '分解', song2vec: '向量', sequence: '序列' }
const MODEL_SHORT_NAMES = { hybrid: 'Hybrid', itemcf: 'ItemCF', usercf: 'UserCF', svd: 'SVD', song2vec: 'S2V', sequence: 'Seq' }
const modelWeights = reactive({ ...MODEL_WEIGHT_DEFAULTS })
const expandedModel = ref(null)
const modelWeightSavedMsg = ref('')
const trainConfig = reactive({
  scope: 'all',
  split: 'holdout',
  minInteractions: 3,
  seed: Math.floor(Math.random() * 90000) + 10000,
  incremental: localStorage.getItem('admin_incremental_train') !== '0',
})
const trainProgress = ref({ percent: 0, stage: '等待训练', message: '', current_model: '', total_models: 6, running: false })
const trainingLogs = ref([])
const trainLogBox = ref(null)
const trainDone = ref(false)
const trainSuccessMsg = ref('')
const evalSortKey = ref('precision_at_100')
const evalSortDir = ref('desc')
let retrainPollTimer = null
let lastRetrainStage = ''
let lastRetrainMessage = ''

const genreDistribution = computed(() => stats.value.genre_distribution || [])
watch(stats, (s) => {
  if (s.genre_distribution) adminGenreList.value = s.genre_distribution.map(g => g.genre)
}, { immediate: true })
const trackMaxPage = computed(() => Math.max(1, Math.ceil((trackTotal.value || 0) / trackSize.value)))
const usersMaxPage = computed(() => Math.max(1, Math.ceil((usersTotal.value || 0) / usersSize.value)))
const commentsMaxPage = computed(() => Math.max(1, Math.ceil((commentsTotal.value || 0) / commentsSize.value)))
const logsMaxPage = computed(() => Math.max(1, Math.ceil((logsTotal.value || 0) / logsSize.value)))
const actionLogsMaxPage = computed(() => Math.max(1, Math.ceil((actionLogsTotal.value || 0) / actionLogsSize.value)))
const itunesSources = computed(() => (dataSources.sources || []).filter((s) => String(s.source || '').toLowerCase() === 'itunes'))
const itunesImportRuns = computed(() => (dataSources.import_runs || []).filter((r) => String(r.source || '').toLowerCase().includes('itunes')))
const metricProgress = computed(() => Math.max(0, Math.min(100, Number(metricJob.value?.progress || 0))))
const metricElapsed = computed(() => formatDurationSeconds(metricJob.value?.elapsed_seconds || 0))
const loadedModelKeys = computed(() => (Array.isArray(metrics.value.models_loaded) ? metrics.value.models_loaded : []).map(normalizeModelKey))
const loadedModelCount = computed(() => loadedModelKeys.value.length || modelCards.value.filter((m) => m.loaded).length)
const modelStatusText = computed(() => {
  if (retraining.value || trainProgress.value?.running) return '🟡 训练进行中'
  if (metricsLoading.value) return '🟡 评估进行中'
  if (metricsError.value) return '🔴 指标异常'
  return '🟢 全部就绪'
})
const modelStatusClass = computed(() => {
  if (metricsLoading.value || retraining.value || trainProgress.value?.running) return 'running'
  if (metricsError.value) return 'error'
  return 'ready'
})
const modelCards = computed(() => {
  const breakdown = Array.isArray(metrics.value.model_breakdown) ? metrics.value.model_breakdown : []
  const breakdownMap = new Map(breakdown.map((row) => [normalizeModelKey(row.model), row]))
  const orderedKeys = [...new Set([
    ...MODEL_ORDER.filter((key) => loadedModelKeys.value.includes(key) || breakdownMap.has(key)),
    ...MODEL_ORDER,
  ])].slice(0, 6)
  return orderedKeys.map((key) => {
    const row = breakdownMap.get(key) || {}
    const isHybrid = key === 'hybrid'
    return {
      model: key,
      loaded: loadedModelKeys.value.includes(key) || Boolean(row.model) || isHybrid,
      cases: Number(row.cases ?? metrics.value.sample_users ?? 0),
      hits: Number(row.hits ?? 0),
      related_hits: Number(row.related_hits ?? row.hits ?? 0),
      precision_at_100: Number(row.precision_at_100 ?? row.precision_at_50 ?? row.precision_at_10 ?? (isHybrid ? metrics.value.precision_at_100 : 0) ?? 0),
      recall_at_100: Number(row.recall_at_100 ?? row.recall_at_50 ?? row.recall_at_10 ?? (isHybrid ? metrics.value.recall_at_100 : 0) ?? 0),
      hit_rate_at_100: Number(row.hit_rate_at_100 ?? row.hit_rate_at_50 ?? row.hit_rate_at_10 ?? row.hit_rate ?? row.recall_at_100 ?? row.recall_at_10 ?? 0),
      related_hit_rate_at_100: Number(row.related_hit_rate_at_100 ?? row.related_hit_rate_at_50 ?? row.hit_rate_at_100 ?? row.hit_rate_at_50 ?? row.hit_rate_at_10 ?? row.hit_rate ?? 0),
      ndcg_at_100: Number(row.ndcg_at_100 ?? row.ndcg_at_50 ?? row.ndcg_at_10 ?? row.ndcg ?? 0),
      related_ndcg_at_100: Number(row.related_ndcg_at_100 ?? row.related_ndcg_at_50 ?? row.ndcg_at_100 ?? row.ndcg_at_50 ?? row.ndcg_at_10 ?? row.ndcg ?? 0),
      coverage: Number(row.coverage ?? row.coverage_percent ?? metrics.value.coverage_percent ?? 0),
      diversity: Number(row.diversity ?? metrics.value.diversity ?? 0),
      avg_recommendations: Number(row.avg_recommendations ?? (isHybrid ? metrics.value.avg_recommendations : 0) ?? 0),
      weight: modelWeightValue(key),
    }
  })
})
const maxModelPrecision = computed(() => Math.max(...modelCards.value.map((item) => Number(item.precision_at_100) || 0), 0))
const modelWeightRows = computed(() => MODEL_WEIGHT_KEYS.map((key) => ({ key, label: modelLabel(key) })))
const modelTrainingLogs = computed(() => {
  const rows = trainingLogs.value.slice(-5).reverse().map((log) => ({
    id: log.id,
    time: log.time,
    type: log.cls === 'done' ? '完成' : log.cls === 'warn' ? '提示' : '流程',
    message: log.text,
  }))
  if (metricJob.value) {
    rows.push({
      id: 'job-' + (metricJob.value.job_id || metricJob.value.status || 'current'),
      time: formatAdminDate(metricJob.value.updated_at || metricJob.value.started_at),
      type: '离线评估',
      message: metricJob.value.message || metricJob.value.stage || '评估任务正在运行',
    })
  }
  if (retrainMsg.value) {
    rows.push({
      id: 'retrain-' + retrainMsg.value,
      time: formatAdminDate(),
      type: '重新训练',
      message: retrainMsg.value,
    })
  }
  rows.push({
    id: 'metrics-current',
    time: formatAdminDate(metrics.value.updated_at || metrics.value.evaluated_at),
    type: metrics.value.type || '指标读取',
    message: metrics.value.notes || '已读取当前模型指标',
  })
  return rows.slice(0, 6)
})
const trainPercent = computed(() => Math.max(0, Math.min(100, Number(trainProgress.value?.percent ?? metricProgress.value ?? 0))))
const showTrainProgress = computed(() => retraining.value || metricsLoading.value || trainDone.value || trainingLogs.value.length > 0)
const trainProgressTitle = computed(() => {
  if (trainDone.value && !retraining.value && !metricsLoading.value) return '训练评估完成'
  if (metricsLoading.value) return metricJob.value?.stage || '正在评估模型'
  if (retraining.value || trainProgress.value?.running) return trainProgress.value?.stage || '正在训练模型'
  return trainProgress.value?.stage || '训练控制台'
})
const trainProgressDesc = computed(() => {
  if (trainDone.value && !retraining.value && !metricsLoading.value) return trainSuccessMsg.value || '所有模型训练与评估已完成，指标已更新'
  if (metricsLoading.value) return metricJob.value?.message || '正在执行离线评估任务'
  if (trainProgress.value?.current_model) {
    return `正在处理 ${trainProgress.value.current_model}，共 ${trainProgress.value.total_models || 6} 个步骤`
  }
  return trainProgress.value?.message || '等待训练任务'
})
const sortedEvaluationRows = computed(() => {
  const rows = modelCards.value.map((item) => ({
    ...item,
    hit_rate_at_100: Number(item.hit_rate_at_100 ?? item.hit_rate_at_50 ?? item.recall_at_100 ?? 0),
    related_hit_rate_at_100: Number(item.related_hit_rate_at_100 ?? item.related_hit_rate_at_50 ?? item.hit_rate_at_100 ?? 0),
    ndcg_at_100: Number(item.ndcg_at_100 ?? item.ndcg_at_50 ?? (Number(item.precision_at_100 || 0) * 0.82)),
    related_ndcg_at_100: Number(item.related_ndcg_at_100 ?? item.related_ndcg_at_50 ?? item.ndcg_at_100 ?? 0),
    coverage: Number(item.coverage ?? item.coverage_percent ?? metrics.value.coverage_percent ?? 0),
  }))
  return rows.sort((a, b) => {
    const av = evalMetricValue(a, evalSortKey.value)
    const bv = evalMetricValue(b, evalSortKey.value)
    const result = evalSortKey.value === 'model'
      ? String(av).localeCompare(String(bv), 'zh-CN')
      : (av === bv ? modelLabel(a.model).localeCompare(modelLabel(b.model), 'zh-CN') : av - bv)
    return evalSortDir.value === 'asc' ? result : -result
  })
})

const topTracks = computed(() => stats.value.top_tracks || [])
const podiumTracks = computed(() => {
  const rows = topTracks.value
  return [
    { rank: 2, tone: 'silver', track: rows[1] },
    { rank: 1, tone: 'gold', track: rows[0] },
    { rank: 3, tone: 'bronze', track: rows[2] },
  ].filter((entry) => entry.track)
})
const playRankRows = computed(() => topTracks.value.slice(3, 10).map((track, index) => ({ rank: index + 4, track })))
const playLeaderCount = computed(() => Math.max(rankCount(topTracks.value[0]), 1))
const metricRankCards = computed(() => [
  { key: 'liked', title: '点赞排行榜', suffix: '赞', items: (stats.value.top_liked || []).slice(0, 5) },
  { key: 'commented', title: '评论排行榜', suffix: '评', items: (stats.value.top_commented || []).slice(0, 5) },
  { key: 'disliked', title: '黑名单排行榜', suffix: '次', items: (stats.value.top_disliked || []).slice(0, 5) },
])

const ADMIN_RANK_GRADS = [
  'linear-gradient(145deg,#6c5ce7,#00cec9)',
  'linear-gradient(145deg,#0984e3,#6c5ce7)',
  'linear-gradient(145deg,#00b894,#55efc4)',
  'linear-gradient(145deg,#e17055,#fdcb6e)',
  'linear-gradient(145deg,#d63031,#e17055)',
  'linear-gradient(145deg,#e84393,#fd79a8)',
  'linear-gradient(145deg,#2d3436,#636e72)',
]

function rankCount(track) {
  return Number(track?.cnt || track?.count || track?.play_count || 0)
}

function adminTrackId(track = {}) {
  return track.id || track.track_id || ''
}

function adminTrackLink(track = {}) {
  const id = adminTrackId(track)
  return id ? { name: 'AdminTrackDetail', params: { id } } : '/admin'
}

function adminRankCoverChar(track = {}) {
  const first = String(track.title || '?').trim().charAt(0) || '?'
  return /[^\x00-\x7F]/.test(first) ? '♪' : first.toUpperCase()
}

function adminRankCoverStyle(track = {}, index = 0) {
  if (track.image_url) return {}
  const id = Number(track.id || index || 0)
  return { background: ADMIN_RANK_GRADS[Math.abs(id) % ADMIN_RANK_GRADS.length] }
}

function rankPercent(track) {
  return Math.max(4, Math.min(100, (rankCount(track) / playLeaderCount.value) * 100)) + '%'
}

function modelLabel(name) {
  const labels = {
    hybrid: '混合推荐',
    itemcf: '物品协同过滤',
    usercf: '用户协同过滤',
    svd: '矩阵分解 SVD',
    song2vec: '歌曲向量',
    sequence: '序列推荐',
  }
  return labels[name] || name
}

function normalizeModelKey(name) {
  const raw = String(name || '').toLowerCase().replace(/[\s_-]/g, '')
  if (raw.includes('hybrid')) return 'hybrid'
  if (raw.includes('itemcf') || raw.includes('item')) return 'itemcf'
  if (raw.includes('usercf') || raw.includes('user')) return 'usercf'
  if (raw.includes('song2vec') || raw.includes('word2vec')) return 'song2vec'
  if (raw.includes('sequence') || raw.includes('seq')) return 'sequence'
  if (raw.includes('svd')) return 'svd'
  return raw
}

function modelDescription(name) {
  return MODEL_DESCRIPTIONS[normalizeModelKey(name)] || '推荐模型指标来自后端评估接口。'
}

function modelIcon(name) {
  return MODEL_ICONS[normalizeModelKey(name)] || '模型'
}

function modelShortName(name) {
  return MODEL_SHORT_NAMES[normalizeModelKey(name)] || String(name || '-')
}

function modelWeightValue(name) {
  const key = normalizeModelKey(name)
  if (key === 'hybrid') return 100
  return Math.max(0, Math.min(100, Number(modelWeights[key] ?? 0)))
}

function modelToneClass(index) {
  return 'tone-' + (index % 6)
}

function precisionBarHeight(item) {
  const max = maxModelPrecision.value || 0
  const value = Number(item?.precision_at_100) || 0
  if (!max || !value) return '0%'
  return Math.max(6, (value / max) * 100) + '%'
}

function toggleModelExpanded(model) {
  const key = normalizeModelKey(model)
  expandedModel.value = expandedModel.value === key ? null : key
}

function modelParamText(model) {
  const params = {
    itemcf: 'k=50, min_interactions=3',
    usercf: 'k=50, min_interactions=3',
    svd: 'n_factors=50',
    song2vec: 'vector_size=100, window=5, min_count=3, epochs=15',
    sequence: 'k=3, session_gap=60min',
    hybrid: 'weights=[0.25, 0.15, 0.25, 0.15, 0.20]',
  }
  return params[normalizeModelKey(model)] || '使用默认参数'
}

function trainScopeChanged() {
  if (trainConfig.scope !== 'all') {
    appendTrainingLog('info', `训练范围切换为 ${modelLabel(trainConfig.scope)}，仅训练该模型后自动评估。`)
  } else {
    appendTrainingLog('info', '训练范围切换为全部模型。')
  }
  localStorage.setItem('admin_incremental_train', trainConfig.incremental ? '1' : '0')
}

function toggleIncremental() {
  trainConfig.incremental = !trainConfig.incremental
  localStorage.setItem('admin_incremental_train', trainConfig.incremental ? '1' : '0')
}

function appendTrainingLog(cls, text) {
  trainingLogs.value.push({
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    cls,
    time: new Date().toLocaleTimeString('zh-CN', { hour12: false }),
    text,
  })
  if (trainingLogs.value.length > 80) trainingLogs.value = trainingLogs.value.slice(-80)
  nextTick(() => {
    const box = trainLogBox.value
    if (box) box.scrollTop = box.scrollHeight
  })
}

function clearRetrainPoll() {
  if (retrainPollTimer) {
    clearInterval(retrainPollTimer)
    retrainPollTimer = null
  }
}

async function pollRetrainProgress() {
  try {
    const data = await adminFetch('/api/admin/retrain-progress')
    trainProgress.value = data || {}
    if (data.stage && data.stage !== lastRetrainStage) {
      lastRetrainStage = data.stage
      appendTrainingLog(data.error ? 'warn' : 'info', data.stage)
    }
    if (data.message && data.message !== lastRetrainMessage) {
      lastRetrainMessage = data.message
      appendTrainingLog(data.error ? 'warn' : 'info', data.message)
    }
    if (data.error) {
      appendTrainingLog('warn', `训练出错：${data.error}`)
      clearRetrainPoll()
    }
    if (Number(data.percent || 0) >= 100 && !data.running) {
      appendTrainingLog('done', '训练完成，正在启动自动评估...')
      clearRetrainPoll()
      await startMetricsEvaluation()
    }
  } catch (e) {
    appendTrainingLog('warn', e.message || '训练进度查询失败')
    clearRetrainPoll()
  }
}

function startTraining() {
  if (trainConfig.scope !== 'all') {
    appendTrainingLog('info', `仅训练 ${modelLabel(trainConfig.scope)} 模型，Hybrid 将自动重新融合。`)
  }
  return retrainModel(!trainConfig.incremental)
}

function resetAllModels() {
  if (!confirm('确定要重置所有模型并重新训练？此操作会重新构建模型状态。')) return
  return retrainModel(true)
}

async function loadModelWeights() {
  try {
    const result = await adminFetch('/api/admin/hybrid-weights')
    const saved = result.weights || {}
    MODEL_WEIGHT_KEYS.forEach((key) => {
      const value = Number(saved[key])
      modelWeights[key] = Number.isFinite(value) ? Math.max(0, Math.min(100, value)) : MODEL_WEIGHT_DEFAULTS[key]
    })
  } catch (e) {
    Object.assign(modelWeights, MODEL_WEIGHT_DEFAULTS)
    modelWeightSavedMsg.value = e.message || '混合权重加载失败，已使用默认值'
    setTimeout(() => { modelWeightSavedMsg.value = '' }, 2200)
  }
}

async function saveModelWeights() {
  const payload = {}
  MODEL_WEIGHT_KEYS.forEach((key) => { payload[key] = modelWeights[key] })
  try {
    const result = await adminFetch('/api/admin/hybrid-weights', {
      method: 'PUT',
      body: JSON.stringify({ weights: payload }),
    })
    Object.assign(modelWeights, result.weights || payload)
    modelWeightSavedMsg.value = '混合权重已保存到后端'
  } catch (e) {
    modelWeightSavedMsg.value = e.message || '混合权重保存失败'
  }
  setTimeout(() => { modelWeightSavedMsg.value = '' }, 2200)
}

function exportModelReport() {
  const m = metrics.value || {}
  const p = (v) => ((Number(v) || 0) * 100).toFixed(2) + '%'
  const dateStr = new Date().toLocaleString('zh-CN')
  const rows = sortedEvaluationRows.value
  const modelRowsHtml = rows.map((r, i) => `<tr><td>${i + 1}</td><td><b>${r.model_label || r.model}</b></td><td>${p(r.hit_rate_at_100)}</td><td>${p(r.related_hit_rate_at_100)}</td><td>${p(r.ndcg_at_100)}</td><td>${p(r.related_ndcg_at_100)}</td><td>${p(r.precision_at_100)}</td><td>${p(r.recall_at_100)}</td><td>${p(r.coverage)}</td><td>${p(r.diversity)}</td><td>${r.cases}</td></tr>`).join('\n')
  const weightsHtml = MODEL_WEIGHT_KEYS.map(k => `<tr><td>${modelLabel(k)}</td><td>${modelWeights[k]}%</td></tr>`).join('\n')
  const html = `<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><title>SoundMind 评估报告</title><style>body{font-family:"PingFang SC","Microsoft YaHei",sans-serif;max-width:960px;margin:40px auto;padding:0 20px;color:#333;background:#fafafa}h1{text-align:center;color:#2d3436;margin-bottom:4px}h2{color:#6c5ce7;margin-top:32px;border-bottom:2px solid #6c5ce7;padding-bottom:6px}.meta{text-align:center;color:#888;font-size:14px;margin-bottom:28px}.card{background:#fff;border-radius:16px;padding:24px;box-shadow:0 2px 12px rgba(0,0,0,.06);margin-bottom:24px}table{width:100%;border-collapse:collapse;font-size:14px}th{background:#6c5ce7;color:#fff;padding:10px 14px;text-align:left;font-size:12px}td{padding:10px 14px;border-bottom:1px solid #eee}tr:hover td{background:#f5f6fa}.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin-top:20px}.kpi{text-align:center;padding:16px;background:#f5f6fa;border-radius:12px}.kpi b{display:block;font-size:28px;color:#6c5ce7}.kpi small{color:#888;font-size:12px}.note{color:#888;font-size:13px;line-height:1.6;margin-top:16px}</style></head><body><h1>SoundMind 模型评估报告</h1><p class="meta">导出时间：${dateStr}　|　评估类型：${m.type || '快速指标'}　|　样本用户：${m.sample_users || '-'}　|　总用户：${m.total_users || '-'}</p><div class="card"><h2>综合指标</h2><div class="kpi-grid"><div class="kpi"><b>${p(m.hit_rate_at_100)}</b><small>命中率@100</small></div><div class="kpi"><b>${p(m.related_hit_rate_at_100)}</b><small>相关命中率@100</small></div><div class="kpi"><b>${p(m.ndcg_at_100)}</b><small>NDCG@100</small></div><div class="kpi"><b>${p(m.related_ndcg_at_100)}</b><small>相关NDCG@100</small></div><div class="kpi"><b>${p(m.coverage_percent || m.coverage)}</b><small>覆盖率</small></div><div class="kpi"><b>${p(m.diversity)}</b><small>多样性</small></div></div></div><div class="card"><h2>各模型详细指标</h2><table><thead><tr><th>#</th><th>模型</th><th>命中率@100</th><th>相关命中率@100</th><th>NDCG@100</th><th>相关NDCG@100</th><th>精确率@100</th><th>召回率@100</th><th>覆盖率</th><th>多样性</th><th>样本数</th></tr></thead><tbody>${modelRowsHtml}</tbody></table></div><div class="card"><h2>Hybrid 融合权重</h2><table><thead><tr><th>子模型</th><th>权重</th></tr></thead><tbody>${weightsHtml}</tbody></table></div>${m.notes ? `<p class="note">备注：${m.notes}</p>` : ''}</body></html>`
  const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `评估报告-${new Date().toISOString().slice(0, 10)}.html`
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

function resetModelPageState() {
  clearMetricsPoll()
  clearRetrainPoll()
  metricsLoading.value = false
  metricsError.value = ''
  metricJob.value = null
  retrainMsg.value = ''
  expandedModel.value = null
  trainProgress.value = { percent: 0, stage: '等待训练', message: '', current_model: '', total_models: 6, running: false }
  trainingLogs.value = []
  lastRetrainStage = ''
  lastRetrainMessage = ''
  void loadModelWeights()
}

function formatAdminDate(value) {
  const date = value ? new Date(value) : new Date()
  if (Number.isNaN(date.getTime())) return String(value || '-')
  return date.toLocaleString('zh-CN', { hour12: false })
}

function evalMetricValue(row, key) {
  if (key === 'model') return modelLabel(row.model)
  return Number(row?.[key] || 0)
}

function sortEvaluation(key) {
  if (evalSortKey.value === key) {
    evalSortDir.value = evalSortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    evalSortKey.value = key
    evalSortDir.value = 'desc'
  }
}

function sortMark(key) {
  if (evalSortKey.value !== key) return ''
  return evalSortDir.value === 'asc' ? ' ▲' : ' ▼'
}

function evalBarWidth(row, key) {
  const value = key === 'coverage' ? Number(row?.[key] || 0) / 100 : Number(row?.[key] || 0)
  return Math.max(4, Math.min(100, value * 100)) + '%'
}

async function doLogin() {
  loading.value = true
  error.value = ''
  try {
    const res = await fetch('/api/admin/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: adminUsername.value, password: password.value }),
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) throw new Error(data.detail || '登录失败')
    adminToken = data.token
    sessionStorage.setItem(ADMIN_TOKEN_KEY, adminToken)
    sessionStorage.setItem(ADMIN_USERNAME_KEY, data.username || adminUsername.value)
    loggedIn.value = true
    password.value = ''
    const savedTheme = localStorage.getItem('theme')
    if (savedTheme === 'light') { adminIsDark.value = false; document.documentElement.setAttribute('data-theme', 'light') }
    await loadStats()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function logout() {
  adminToken = ''
  sessionStorage.removeItem(ADMIN_TOKEN_KEY)
  sessionStorage.removeItem(ADMIN_USERNAME_KEY)
  loggedIn.value = false
  password.value = ''
}

async function adminFetch(url, opts = {}) {
  const res = await fetch(url, {
    ...opts,
    headers: { 'Content-Type': 'application/json', ...(opts.headers || {}), Authorization: 'Bearer ' + adminToken },
  })
  const data = await res.json().catch(() => ({}))
  if (res.status === 401) {
    logout()
    throw new Error(data.detail || '管理员登录已失效，请重新登录')
  }
  if (!res.ok) throw new Error(data.detail || '请求失败')
  return data
}

async function switchTab(next) {
  tab.value = next
  if (next === 'overview') await loadStats()
  if (next === 'users') await loadUsers()
  if (next === 'tracks') await loadTracks()
  if (next === 'comments') await loadComments()
  if (next === 'data') await loadDataSources()
  if (next === 'actions') await loadActionLogs()
  if (next === 'models') await loadMetrics()
  if (next === 'system') await loadSystem()
}

async function loadStats() {
  statsLoading.value = true
  try {
    stats.value = await adminFetch('/api/admin/stats')
  } finally {
    statsLoading.value = false
    syncGenrePanelHeight()
  }
}

function syncGenrePanelHeight() {
  nextTick(() => {
    ensureRankObserver()
    if (rankResizeFrame) cancelAnimationFrame(rankResizeFrame)
    rankResizeFrame = requestAnimationFrame(() => {
      rankResizeFrame = 0
      const height = playRankPanel.value?.getBoundingClientRect().height || 0
      genrePanelHeight.value = height ? Math.round(height) : 0
    })
  })
}

function ensureRankObserver() {
  if (typeof window === 'undefined' || !window.ResizeObserver || !playRankPanel.value || rankResizeObserver) return
  rankResizeObserver = new ResizeObserver(syncGenrePanelHeight)
  rankResizeObserver.observe(playRankPanel.value)
}

async function seedEngagement() {
  if (!confirm('将为每个用户随机生成少量喜欢和评论数据，用于填充后台排行榜。是否继续？')) return
  seedLoading.value = true
  seedMsg.value = ''
  try {
    const data = await adminFetch('/api/admin/seed-engagement', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ likes_per_user: 20, comments_per_user: 5, comment_likes_per_user: 3, playlists_per_user: 1 }),
    })
    seedMsg.value = `已生成：${data.likes_created} 点赞、${data.comments_created} 评论、${data.comment_likes_created} 评论点赞、${data.dislikes_created} 不喜欢、${data.history_created} 播放记录、${data.playlists_created} 歌单`
    await loadStats()
  } catch (e) {
    seedMsg.value = '生成失败: ' + (e.message || e)
  } finally {
    seedLoading.value = false
  }
}

async function startItunesImport() {
  const target = Math.max(100, Math.min(50000, itunesTarget.value || 5000))
  itunesTarget.value = target
  itunesImporting.value = true
  itunesImportMsg.value = ''
  try {
    await adminFetch('/api/admin/import-itunes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ target }) })
    itunesImportMsg.value = '导入已启动，正在从 iTunes API 获取数据...'
    pollImportProgress()
  } catch(e) {
    itunesImportMsg.value = '启动导入失败: ' + (e.message || e)
    itunesImporting.value = false
  }
}

async function cancelItunesImport() {
  try {
    await adminFetch('/api/admin/import-cancel', { method: 'POST' })
    itunesImportMsg.value = '已请求取消导入，等待当前查询完成...'
  } catch(e) {
    itunesImportMsg.value = '取消失败: ' + (e.message || e)
  }
}

function pollImportProgress() {
  const timer = setInterval(async () => {
    try {
      const data = await adminFetch('/api/admin/import-progress')
      Object.assign(itunesImportProgress, data)
      if (!data.running) {
        clearInterval(timer)
        itunesImporting.value = false
        if (data.status === 'cancelled') {
          itunesImportMsg.value = `导入已取消：已导入 ${data.imported} 首歌`
        } else {
          itunesImportMsg.value = `导入完成：已导入 ${data.imported} 首歌`
        }
        loadStats()
        loadDataSources()
      }
    } catch(e) {
      clearInterval(timer)
      itunesImporting.value = false
      itunesImportMsg.value = '查询进度失败'
    }
  }, 3000)
}

async function loadUsers(nextPage = usersPage.value) {
  usersLoading.value = true
  if (typeof nextPage !== 'number') nextPage = 1
  usersPage.value = Math.max(1, nextPage)
  try {
    const data = await adminFetch('/api/admin/users?page=' + usersPage.value + '&size=' + usersSize.value + '&search=' + encodeURIComponent(userSearch.value) + '&genre=' + encodeURIComponent(userGenreFilter.value) + '&sort_by=' + userSortBy.value + '&sort_order=' + userSortOrder.value)
    userList.value = data.items || []
    usersTotal.value = data.total || 0
  } finally { usersLoading.value = false }
}

async function loadTracks(nextPage = trackPage.value) {
  tracksLoading.value = true
  trackPage.value = Math.max(1, nextPage)
  try {
    const q = trackSearch.value ? '&search=' + encodeURIComponent(trackSearch.value) : ''
    const sort = '&sort_by=' + encodeURIComponent(trackSortBy.value) + '&sort_order=' + encodeURIComponent(trackSortOrder.value)
    const data = await adminFetch('/api/admin/tracks?page=' + trackPage.value + '&size=' + trackSize.value + q + sort)
    trackList.value = data.items || []
    trackTotal.value = data.total || 0
  } finally {
    tracksLoading.value = false
  }
}

function resetTrackPage() {
  trackPage.value = 1
  return loadTracks(1)
}

async function loadFeedback() {
  feedbackLoading.value = true
  try { Object.assign(fbData, await adminFetch('/api/admin/feedback')) } finally { feedbackLoading.value = false }
}

async function loadComments(nextPage = commentsPage.value) {
  commentsLoading.value = true
  if (typeof nextPage !== 'number') nextPage = 1
  commentsPage.value = Math.max(1, nextPage)
  try {
    const s = commentSearch.value || ''
    const p = new URLSearchParams({ page: commentsPage.value, size: commentsSize.value })
    if (s) p.set('search', s)
    const data = await adminFetch(`/api/admin/comments?${p}`)
    commentList.value = data.items || []
    commentsTotal.value = data.total || 0
  } finally {
    commentsLoading.value = false
  }
}

async function loadDataSources() {
  dataLoading.value = true
  try { Object.assign(dataSources, await adminFetch('/api/admin/data-sources')) } finally { dataLoading.value = false }
}

async function loadLogs(nextPage = 1) {
  logsLoading.value = true
  if (typeof nextPage !== 'number') nextPage = 1
  logsPage.value = Math.max(1, nextPage)
  try {
    const p = new URLSearchParams({ page: logsPage.value, size: logsSize.value })
    if (logSearch.value.trim()) p.set('search', logSearch.value.trim())
    if (logModel.value.trim()) p.set('model_name', logModel.value.trim())
    const data = await adminFetch('/api/admin/recommendation-logs?' + p)
    logList.value = data.items || []
    logsTotal.value = data.total || 0
  } finally {
    logsLoading.value = false
  }
}

async function loadActionLogs(nextPage = 1) {
  actionLogsLoading.value = true
  if (typeof nextPage !== 'number') nextPage = 1
  actionLogsPage.value = Math.max(1, nextPage)
  try {
    const p = new URLSearchParams({ page: actionLogsPage.value, size: actionLogsSize.value })
    if (actionFilter.value) p.set('action_type', actionFilter.value)
    if (actionStatus.value) p.set('status', actionStatus.value)
    if (actionSearch.value.trim()) p.set('search', actionSearch.value.trim())
    const data = await adminFetch('/api/admin/action-logs?' + p)
    actionLogList.value = data.items || []
    actionLogsTotal.value = data.total || 0
  } finally {
    actionLogsLoading.value = false
  }
}

function actionLabel(type) {
  const labels = {
    audio_play_request: '播放请求',
    audio_loadedmetadata: '音频加载',
    audio_playing: '开始播放',
    audio_paused: '暂停播放',
    audio_ended: '播放结束',
    audio_error: '播放错误',
    audio_play_error: '播放异常',
    audio_missing_source: '缺少音频',
    audio_pause_request: '暂停请求',
    audio_seek: '拖动进度',
    feedback: '用户反馈',
  }
  return labels[type] || type
}

async function loadMetrics() {
  if (metricsLoading.value) return
  clearMetricsPoll()
  metricsRefreshing.value = true
  metricsError.value = ''
  metricJob.value = null
  try {
    metrics.value = await adminFetch('/api/admin/model-metrics')
  } catch (e) {
    metricsError.value = e.message || '模型指标加载失败'
  } finally {
    metricsRefreshing.value = false
  }
}

async function startMetricsEvaluation() {
  if (metricsLoading.value) {
    metricsError.value = '评估正在进行中'
    return
  }
  clearMetricsPoll()
  metricsLoading.value = true
  metricsError.value = ''
  metricJob.value = null
  trainProgress.value = { percent: 0, stage: '离线评估', message: '正在创建评估任务', current_model: '', total_models: modelCards.value.length || 6, running: true }
  appendTrainingLog('info', `开始离线评估，样本数 ${metricSampleUsers.value}`)
  const models = trainConfig.scope !== 'all' ? [trainConfig.scope] : undefined
  try {
    const job = await adminFetch('/api/admin/model-metrics/jobs', {
      method: 'POST',
      body: JSON.stringify({ sample_users: metricSampleUsers.value, n: 100, models }),
    })
    metricJob.value = job
    appendTrainingLog('info', `评估任务已创建：${job.job_id || '-'}`)
    pollMetricsJob(job.job_id)
  } catch (e) {
    metricsError.value = e.message || '模型指标加载失败'
    appendTrainingLog('warn', metricsError.value)
    metricsLoading.value = false
  }
}

function clearMetricsPoll() {
  if (metricsPollTimer) {
    clearTimeout(metricsPollTimer)
    metricsPollTimer = null
  }
}

async function pollMetricsJob(jobId) {
  try {
    const job = await adminFetch('/api/admin/model-metrics/jobs/' + jobId)
    metricJob.value = job
    trainProgress.value = {
      percent: Number(job.progress || 0),
      stage: job.stage || '离线评估',
      message: job.message || '',
      current_model: job.current_model || '',
      total_models: modelCards.value.length || 6,
      running: job.status === 'running' || job.status === 'pending',
    }
    if (job.message && job.message !== lastRetrainMessage) {
      lastRetrainMessage = job.message
      appendTrainingLog('info', job.message)
    }
    if (job.status === 'completed') {
      metrics.value = job.result || {}
      metricsLoading.value = false
      trainProgress.value = { ...trainProgress.value, percent: 100, stage: '评估完成', message: '离线评估完成', running: false }
      trainDone.value = true
      trainSuccessMsg.value = '训练与评估全部完成！模型指标已更新。'
      appendTrainingLog('done', '离线评估完成 — 所有模型指标已更新')
      clearMetricsPoll()
      loadStats()
      return
    }
    if (job.status === 'error') {
      metricsError.value = job.error || job.message || '模型评估失败'
      metricsLoading.value = false
      appendTrainingLog('warn', metricsError.value)
      clearMetricsPoll()
      return
    }
    metricsPollTimer = setTimeout(() => pollMetricsJob(jobId), 800)
  } catch (e) {
    metricsError.value = e.message || '模型评估进度查询失败'
    metricsLoading.value = false
    appendTrainingLog('warn', metricsError.value)
    clearMetricsPoll()
  }
}

async function loadSystem() {
  sysLoading.value = true
  try { Object.assign(sysData, await adminFetch('/api/admin/system')) } finally { sysLoading.value = false }
}

async function deleteUser(id) {
  if (!confirm('确定删除用户 ' + id + ' 及其所有数据？')) return
  try {
    await adminFetch('/api/admin/users/delete', { method: 'POST', body: JSON.stringify({ user_id: id }) })
  } catch (e) {
    alert('删除用户失败：' + (e.message || '未知错误'))
  }
  await Promise.all([loadUsers(), loadStats()])
}

async function deleteTrack(id) {
  if (!confirm('确定删除歌曲 ' + id + '？')) return
  try {
    await adminFetch('/api/admin/tracks/delete', { method: 'POST', body: JSON.stringify({ track_id: id }) })
  } catch (e) {
    alert('删除歌曲失败：' + (e.message || '未知错误'))
  }
  await Promise.all([loadTracks(), loadStats()])
}

async function deleteComment(id) {
  if (!confirm('确定删除评论？')) return
  try {
    await adminFetch('/api/admin/comments/' + id, { method: 'DELETE' })
  } catch (e) {
    alert('删除评论失败：' + (e.message || '未知错误'))
  }
  await loadComments()
}

function openEdit(track) {
  editTrack.value = track
  Object.assign(editForm, {
    title: track.title || '',
    album: track.album || '',
    year: track.year || 0,
    genre: track.genre || '',
    popularity: track.popularity || 0,
    image_url: track.image_url || '',
    preview_url: track.preview_url || '',
  })
  editError.value = ''
}

function closeEdit() {
  editTrack.value = null
  editError.value = ''
}

async function saveTrack() {
  savingTrack.value = true
  editError.value = ''
  try {
    await adminFetch('/api/admin/tracks/' + editTrack.value.id, { method: 'PUT', body: JSON.stringify(editForm) })
    closeEdit()
    await loadTracks()
  } catch (e) {
    editError.value = e.message
  } finally {
    savingTrack.value = false
  }
}

async function retrainModel(force) {
  retraining.value = true
  retrainMsg.value = ''
  retrainOk.value = false
  trainDone.value = false
  trainSuccessMsg.value = ''
  trainProgress.value = { percent: 0, stage: '准备训练', message: '正在提交训练任务', current_model: '', total_models: 6, running: true }
  lastRetrainStage = ''
  lastRetrainMessage = ''
  appendTrainingLog('info', force ? '开始全量重建训练' : '开始增量训练')
  clearRetrainPoll()
  retrainPollTimer = setInterval(pollRetrainProgress, 500)
  try {
    const data = await adminFetch('/api/admin/retrain', {
      method: 'POST',
      body: JSON.stringify({ force, scope: trainConfig.scope, min_interactions: trainConfig.minInteractions, seed: trainConfig.seed }),
    })
    retrainMsg.value = data.message || '模型重新训练完成'
    retrainOk.value = true
    trainProgress.value = { ...trainProgress.value, percent: 100, stage: '训练完成', message: retrainMsg.value, running: false }
    appendTrainingLog('done', retrainMsg.value)
    clearRetrainPoll()
    await loadMetrics()
  } catch (e) {
    retrainMsg.value = e.message
    retrainOk.value = false
    trainProgress.value = { ...trainProgress.value, running: false, error: e.message }
    appendTrainingLog('warn', e.message || '模型训练失败')
    clearRetrainPoll()
  } finally {
    retraining.value = false
  }
}

function barWidth(count) {
  const rows = stats.value.genre_distribution || [{ cnt: 1 }]
  const max = Math.max(...rows.map(g => g.cnt), 1)
  return (count / max) * 100
}

function percent(value) {
  return ((Number(value) || 0) * 100).toFixed(1) + '%'
}

function formatUptime(seconds) {
  const s = Number(seconds) || 0
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  return h > 0 ? h + '小时 ' + m + '分钟' : m + '分钟'
}

function formatDurationSeconds(seconds) {
  const s = Math.floor(Number(seconds) || 0)
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  if (h > 0) return `${h}小时 ${m}分钟 ${sec}秒`
  if (m > 0) return `${m}分钟 ${sec}秒`
  return `${sec}秒`
}

onMounted(async () => {
  await loadModelWeights()
  if (adminToken) {
    loggedIn.value = true
    const savedTheme = localStorage.getItem('theme')
    if (savedTheme === 'light') { adminIsDark.value = false; document.documentElement.setAttribute('data-theme', 'light') }
    try {
      await loadStats()
    } catch {
      logout()
      return
    }
    try {
      await loadMetrics()
    } catch {
      // metrics load failure is not fatal, continue
    }
    // Auto-start training+evaluation if metrics are demo/quick or have no real evaluation data
    if (!metricsLoading.value && (metrics.value.type === '演示评估' || !metrics.value.type || !metrics.value.model_breakdown?.length)) {
      appendTrainingLog('info', '自动启动训练与评估...')
      startTraining()
    }
  }
  window.addEventListener('resize', syncGenrePanelHeight)
  nextTick(() => {
    ensureRankObserver()
    syncGenrePanelHeight()
  })
})

onUnmounted(() => {
  clearMetricsPoll()
  clearRetrainPoll()
  if (rankResizeObserver) {
    rankResizeObserver.disconnect()
    rankResizeObserver = null
  }
  if (rankResizeFrame) {
    cancelAnimationFrame(rankResizeFrame)
    rankResizeFrame = 0
  }
  window.removeEventListener('resize', syncGenrePanelHeight)
})
</script>

<style scoped>
.auth-card{max-width:380px;margin:60px auto;background:var(--color-surface);border-radius:var(--radius);padding:32px;text-align:center}
.auth-card h1{font-size:22px;margin-bottom:8px}.desc,.hint{color:var(--color-text-muted);font-size:13px}.hint{margin-top:12px}.switch{font-size:13px;margin-top:12px}.switch a,.user-link{color:var(--color-primary-light);text-decoration:none}
form{display:flex;flex-direction:column;gap:10px;margin-top:20px}.error{color:var(--color-dislike);font-size:13px}
.topbar{display:flex;justify-content:space-between;align-items:flex-start;margin:24px 0 16px}.topbar h1{font-size:22px}.topbar-sub{font-size:13px;color:var(--color-text-muted);margin-top:2px}.topbar-right{display:flex;align-items:center;gap:12px}
.tabs{display:flex;gap:4px;margin-bottom:24px;flex-wrap:wrap}.tabs button{padding:8px 16px;border:none;border-radius:var(--radius);font-size:13px;font-weight:600;background:var(--color-surface);color:var(--color-text-muted);cursor:pointer}.tabs button.active{background:var(--color-primary);color:#fff}
.stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-bottom:24px}.stat-grid-sm{grid-template-columns:repeat(auto-fit,minmax(120px,1fr))}
.stat-card{background:var(--color-surface);border-radius:var(--radius);padding:18px;display:flex;flex-direction:column;align-items:center}.sv{font-size:26px;font-weight:800;color:var(--color-primary-light)}.sl{font-size:12px;color:var(--color-text-muted);margin-top:4px}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:20px}.section{margin-bottom:28px}.section h2{font-size:16px;font-weight:600;margin-bottom:12px}
.rank-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:20px}.rank-box{background:transparent}
.admin-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:-8px 0 22px}.seed-msg{font-size:13px;color:var(--color-text-muted)}
.simple-list{display:flex;flex-direction:column;gap:2px}.simple-row{background:var(--color-surface);border-radius:var(--radius);padding:10px 14px;display:flex;align-items:center;gap:12px}.rank{font-weight:700;color:var(--color-primary-light);width:24px}.name{flex:1;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.artist{color:var(--color-text-muted);font-size:13px}.cnt{font-size:13px;font-weight:600}
.rank-bars{display:flex;flex-direction:column;gap:8px}.rank-bar-row{display:grid;grid-template-columns:28px minmax(120px,1.2fr) minmax(160px,2fr) 72px;align-items:center;gap:10px}.rank-title{min-width:0;display:flex;flex-direction:column}.rank-title b{font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.rank-title small{font-size:11px;color:var(--color-text-muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.rank-track{height:20px}.rank-bar-row .cnt{text-align:right;color:var(--color-text-muted)}
.rank-card-box{background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius);padding:16px}.rank-box-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:12px}.rank-box-head h2{margin:0}.rank-box-head span{font-size:12px;color:var(--color-text-muted);background:var(--color-bg);border-radius:999px;padding:3px 9px}.rank-card-list{display:flex;flex-direction:column;gap:10px}.rank-card-row{display:grid;grid-template-columns:30px 42px minmax(0,1fr) auto;grid-template-rows:auto 7px;align-items:center;gap:8px 10px;background:var(--color-bg);border:1px solid var(--color-border);border-radius:12px;padding:10px 12px}.rank-medal{width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:var(--color-surface);color:var(--color-text-muted);font-size:12px;font-weight:800}.rank-medal.top{background:linear-gradient(135deg,var(--color-primary),var(--color-accent));color:#fff}.rank-cover-mini{width:42px;height:42px;border-radius:10px;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,var(--color-primary),var(--color-accent));color:rgba(255,255,255,.72);font-weight:900;font-size:18px;overflow:hidden}.rank-main{min-width:0;display:flex;flex-direction:column}.rank-main b{font-size:13px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.rank-main small{font-size:11px;color:var(--color-text-muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:2px}.rank-metric{font-size:12px;font-weight:800;color:var(--color-primary-light);background:var(--color-surface);border-radius:999px;padding:5px 9px;white-space:nowrap}.rank-meter{grid-column:2 / -1;height:7px;background:var(--color-surface);border-radius:999px;overflow:hidden}.rank-meter-fill{display:block;height:100%;background:linear-gradient(90deg,var(--color-primary),var(--color-accent));border-radius:999px}
.empty-mini{color:var(--color-text-muted);background:var(--color-surface);border-radius:var(--radius);padding:16px;font-size:13px}
.genre-bars{display:flex;flex:1;flex-direction:column;justify-content:flex-start;gap:6px;min-height:0;overflow-y:auto;overflow-x:hidden;padding-right:4px;scrollbar-width:thin;scrollbar-color:var(--color-border) transparent}.genre-bars::-webkit-scrollbar{width:5px}.genre-bars::-webkit-scrollbar-thumb{background:var(--color-border);border-radius:999px}.genre-row{display:flex;align-items:center;gap:10px;min-height:22px;flex:0 0 auto}.genre-label{width:92px;font-size:13px;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.bar-track{flex:1;height:18px;background:var(--color-bg);border-radius:10px;overflow:hidden}.bar-fill{height:100%;background:var(--color-primary);border-radius:10px}.genre-cnt{font-size:12px;color:var(--color-text-muted);width:36px;text-align:right}
.toolbar{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}.search-input{flex:1;max-width:320px}.compact-input{max-width:180px}
.data-table{width:100%;border-collapse:collapse;font-size:13px}.data-table th,.data-table td{padding:8px 12px;text-align:left;border-bottom:1px solid var(--color-border)}.data-table th{color:var(--color-text-muted);font-weight:600;white-space:nowrap}.data-table tr:hover td{background:var(--color-surface-hover)}
.td-title{max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.td-album{max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.td-comment{max-width:360px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.row-actions{display:flex;gap:6px}.btn-xs{padding:3px 10px;font-size:11px}.badge-ok,.like{color:var(--color-like)}.badge-no{color:var(--color-text-muted)}.dislike{color:var(--color-dislike)}
.pagination-info,.note,.system-text{font-size:12px;color:var(--color-text-muted);margin-top:10px}.pagination-row{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}.pager-actions{display:flex;gap:6px}.model-list{display:flex;flex-wrap:wrap;gap:6px}.model-tag{padding:4px 10px;border-radius:6px;font-size:12px;font-weight:600;background:var(--color-bg);color:var(--color-text-muted)}.action-row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.inline-control{display:flex;align-items:center;gap:8px;font-size:12px;font-weight:600;color:var(--color-text-muted)}.inline-control input{width:88px;padding:7px 10px}.retrain-msg{margin-top:10px;font-size:13px}.retrain-msg.success{color:var(--color-like)}.retrain-msg.error{color:var(--color-dislike)}.loading-panel{text-align:left}.error-msg{color:var(--color-dislike);background:var(--color-surface);border-radius:var(--radius);padding:14px;font-size:13px}
.progress-card{background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius);padding:18px;max-width:820px}.progress-head{display:flex;align-items:flex-start;justify-content:space-between;gap:16px}.progress-head h2{font-size:17px;margin:0 0 4px}.progress-head p{font-size:13px;color:var(--color-text-muted);margin:0}.progress-num{font-size:24px;font-weight:800;color:var(--color-primary-light);font-variant-numeric:tabular-nums}.progress-track{height:12px;border-radius:999px;background:var(--color-bg);overflow:hidden;margin:16px 0 12px}.progress-fill{height:100%;background:linear-gradient(90deg,var(--color-primary),var(--color-accent));border-radius:999px;transition:width .3s ease}.progress-meta{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px;font-size:12px;color:var(--color-text-muted)}
.modal-mask{position:fixed;inset:0;background:rgba(0,0,0,.56);display:flex;align-items:center;justify-content:center;padding:20px;z-index:100}.edit-modal{width:min(560px,100%);background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius);padding:18px;box-shadow:0 24px 80px rgba(0,0,0,.45);display:flex;flex-direction:column;gap:10px}.modal-head{display:flex;justify-content:space-between;align-items:center}.modal-head h2{font-size:18px}.modal-close{background:none;border:none;color:var(--color-text-muted);font-size:24px;cursor:pointer;line-height:1}.edit-modal label{display:flex;flex-direction:column;gap:5px;font-size:12px;color:var(--color-text-muted);font-weight:600}.edit-modal input{width:100%}.form-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.modal-actions{display:flex;justify-content:flex-end;gap:8px;margin-top:4px}
.container{--gold:#f0c060;--silver:#bcc6d0;--bronze:#d4a574}.stat-card{border:1px solid var(--color-border);border-radius:14px}.stat-card .sv{background:linear-gradient(135deg,var(--color-primary),var(--color-accent));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}.stat-card .sv.like,.stat-card .sv.dislike{-webkit-text-fill-color:transparent}
.overview-rank-layout{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(280px,.75fr);gap:20px;margin-bottom:22px;align-items:start}.play-rank-panel,.genre-panel{background:var(--color-surface);border:1px solid var(--color-border);border-radius:16px;padding:20px;overflow:hidden}.genre-panel{display:flex;flex-direction:column;align-self:start;min-height:0}.rank-section-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:18px}.rank-section-head h2{font-size:17px;margin:0 0 4px}.rank-section-head p{font-size:12px;color:var(--color-text-muted);margin:0}.rank-section-head>span{font-size:11px;color:var(--color-text-muted);background:var(--color-bg);border-radius:20px;padding:4px 10px;white-space:nowrap}.rank-section-head.compact{margin-bottom:14px}
.podium{display:flex;justify-content:center;align-items:flex-end;gap:16px;min-height:210px;margin-bottom:30px}.podium-item{display:flex;flex-direction:column;align-items:center;text-decoration:none;color:inherit;transition:transform .25s}.podium-item:hover{transform:translateY(-6px)}.podium-cover{border-radius:16px;display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden;box-shadow:0 8px 32px rgba(0,0,0,.28)}.podium-cover img{width:100%;height:100%;object-fit:cover}.podium-item.gold .podium-cover{width:120px;height:120px;background:linear-gradient(145deg,#f0c060,#e8a830)}.podium-item.silver .podium-cover{width:100px;height:100px;background:linear-gradient(145deg,#bcc6d0,#8e99a4)}.podium-item.bronze .podium-cover{width:88px;height:88px;background:linear-gradient(145deg,#d4a574,#b8783c)}.podium-char{font-size:42px;font-weight:900;color:rgba(0,0,0,.26)}.podium-item.gold .podium-char{font-size:48px}.podium-medal{width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:900;margin-top:-17px;position:relative;z-index:1;box-shadow:0 2px 8px rgba(0,0,0,.28)}.podium-item.gold .podium-medal{background:var(--gold);color:#5c3800}.podium-item.silver .podium-medal{background:var(--silver);color:#3a4048}.podium-item.bronze .podium-medal{background:var(--bronze);color:#5c3000}.podium-info{text-align:center;margin-top:10px}.podium-title{font-size:14px;font-weight:800;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:140px}.podium-artist{font-size:11px;color:var(--color-text-muted);margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:140px}.podium-count{font-size:12px;font-weight:800;color:var(--color-primary-light);margin-top:4px}
.rank-list-section h3{font-size:15px;margin:0 0 12px}.rank-list{display:flex;flex-direction:column;gap:6px}.rank-row{display:grid;grid-template-columns:36px 48px minmax(0,1fr) auto;grid-template-rows:auto 6px;align-items:center;gap:8px 12px;background:var(--color-bg);border:1px solid var(--color-border);border-radius:12px;padding:10px 14px;text-decoration:none;color:inherit;transition:transform .15s,border-color .15s;animation:fadeUp .4s ease both}.rank-row:hover{transform:translateX(4px);border-color:var(--color-primary)}.rank-pos{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;color:var(--color-text-muted);background:var(--color-surface)}.rank-mini-cover{width:48px;height:48px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:20px;color:rgba(255,255,255,.46);overflow:hidden}.rank-mini-cover img{width:100%;height:100%;object-fit:cover}.rank-row .rank-main{display:flex;flex-direction:column;min-width:0}.rank-row .rank-main b{font-size:14px;font-weight:800;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.rank-row .rank-main small{font-size:11px;color:var(--color-text-muted);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.rank-value{font-size:13px;font-weight:800;color:var(--color-primary-light);background:var(--color-surface);border-radius:20px;padding:5px 12px;white-space:nowrap}.rank-bar{grid-column:2 / -1;height:6px;background:var(--color-surface);border-radius:10px;overflow:hidden}.rank-bar-fill{display:block;height:100%;border-radius:10px;background:linear-gradient(90deg,var(--color-primary),var(--color-accent));transition:width .5s ease}.rank-row:nth-child(1){animation-delay:0s}.rank-row:nth-child(2){animation-delay:.03s}.rank-row:nth-child(3){animation-delay:.06s}.rank-row:nth-child(4){animation-delay:.09s}.rank-row:nth-child(5){animation-delay:.12s}.rank-row:nth-child(6){animation-delay:.15s}.rank-row:nth-child(7){animation-delay:.18s}
.rank-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}.rank-card{background:var(--color-surface);border:1px solid var(--color-border);border-radius:16px;padding:20px;overflow:hidden}.rank-card-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px}.rank-card-head h3{font-size:15px;font-weight:700;margin:0}.rank-card-head span{font-size:11px;color:var(--color-text-muted);background:var(--color-bg);border-radius:20px;padding:3px 10px}.rank-card-list{display:flex;flex-direction:column;gap:8px}.rank-card-row{display:grid;grid-template-columns:28px 42px minmax(0,1fr) auto;grid-template-rows:none;align-items:center;gap:10px;background:var(--color-bg);border:0;border-radius:11px;padding:10px 12px;text-decoration:none;color:inherit;transition:transform .15s;animation:fadeUp .4s ease both}.rank-card-row:hover{transform:translateX(3px)}.rank-card-pos{width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;color:var(--color-text-muted);background:var(--color-surface)}.rank-card-pos.top{background:var(--color-primary);color:#fff}.rank-card-cov{width:42px;height:42px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:18px;color:rgba(255,255,255,.46);overflow:hidden}.rank-card-cov img{width:100%;height:100%;object-fit:cover}.rank-card-main{min-width:0;display:flex;flex-direction:column}.rank-card-main b{font-size:13px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.rank-card-main small{font-size:11px;color:var(--color-text-muted);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.rank-card-metric{font-size:13px;font-weight:800;color:var(--color-primary-light);background:var(--color-surface);border-radius:20px;padding:4px 10px;white-space:nowrap}
.model-dashboard{display:flex;flex-direction:column;gap:18px}.model-hero-panel{display:flex;justify-content:space-between;align-items:flex-start;gap:18px;background:linear-gradient(135deg,rgba(108,92,231,.18),rgba(0,206,201,.08));border:1px solid var(--color-border);border-radius:18px;padding:22px}.model-eyebrow{font-size:11px;font-weight:900;color:var(--color-accent);letter-spacing:0;text-transform:uppercase}.model-hero-panel h2{font-size:22px;margin:6px 0}.model-hero-panel p{font-size:13px;color:var(--color-text-muted);max-width:620px}.model-status-card{min-width:150px;background:var(--color-surface);border:1px solid var(--color-border);border-radius:14px;padding:14px;display:flex;flex-direction:column;gap:4px}.status-dot{width:10px;height:10px;border-radius:50%;background:var(--color-like);box-shadow:0 0 0 4px rgba(0,184,148,.12)}.status-dot.running{background:var(--color-primary);box-shadow:0 0 0 4px rgba(108,92,231,.16)}.status-dot.error{background:var(--color-dislike);box-shadow:0 0 0 4px rgba(225,112,85,.14)}.model-status-card strong{font-size:14px}.model-status-card small{font-size:12px;color:var(--color-text-muted)}.model-control-panel{display:flex;align-items:center;gap:10px;flex-wrap:wrap;background:var(--color-surface);border:1px solid var(--color-border);border-radius:16px;padding:14px}.sample-control{display:flex;align-items:center;gap:8px;font-size:12px;font-weight:800;color:var(--color-text-muted)}.sample-control input{width:90px;padding:7px 10px}.model-progress-panel{display:grid;grid-template-columns:112px minmax(0,1fr);gap:18px;align-items:center;background:var(--color-surface);border:1px solid var(--color-border);border-radius:16px;padding:18px}.progress-ring{--p:0%;width:96px;height:96px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:conic-gradient(var(--color-primary) var(--p),var(--color-bg) 0);position:relative}.progress-ring::after{content:"";position:absolute;inset:10px;border-radius:50%;background:var(--color-surface)}.progress-ring span{position:relative;z-index:1;font-size:20px;font-weight:900;color:var(--color-primary-light)}.progress-body h3{font-size:17px;margin:0 0 4px}.progress-body p{font-size:13px;color:var(--color-text-muted);margin:0}.model-kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}.model-kpi{background:var(--color-surface);border:1px solid var(--color-border);border-radius:14px;padding:16px;display:flex;flex-direction:column;gap:4px}.model-kpi span{font-size:24px;font-weight:900;background:linear-gradient(135deg,var(--color-primary),var(--color-accent));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}.model-kpi small{font-size:12px;color:var(--color-text-muted)}.model-info-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.model-info-card,.model-breakdown-panel{background:var(--color-surface);border:1px solid var(--color-border);border-radius:16px;padding:18px}.model-card-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:14px}.model-card-head h3{font-size:16px;margin:0}.model-card-head span{font-size:11px;color:var(--color-text-muted);background:var(--color-bg);border-radius:999px;padding:4px 10px}.model-chip-list{display:flex;gap:8px;flex-wrap:wrap}.model-chip{padding:7px 11px;border-radius:999px;background:var(--color-bg);border:1px solid var(--color-border);font-size:12px;font-weight:800;color:var(--color-primary-light)}.model-note{font-size:12px;color:var(--color-text-muted);line-height:1.6;margin-top:12px}.model-help-list{list-style:none;display:flex;flex-direction:column;gap:10px;margin:0;padding:0}.model-help-list li{display:flex;flex-direction:column;gap:3px;background:var(--color-bg);border-radius:10px;padding:10px 12px}.model-help-list b{font-size:13px}.model-help-list span{font-size:12px;color:var(--color-text-muted)}.model-breakdown-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}.model-break-card{background:var(--color-bg);border:1px solid var(--color-border);border-radius:14px;padding:14px}.model-break-title{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:12px}.model-break-title span{font-size:11px;color:var(--color-text-muted)}.model-mini-metrics{display:grid;grid-template-columns:1fr 1fr;gap:8px}.model-mini-metrics span{background:var(--color-surface);border-radius:10px;padding:9px;display:flex;flex-direction:column}.model-mini-metrics b{font-size:15px;color:var(--color-primary-light)}.model-mini-metrics small{font-size:11px;color:var(--color-text-muted);margin-top:2px}
.models-header{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:10px;flex-wrap:wrap}.models-header h2{font-size:26px;font-weight:800;margin:0}.models-header h2 span{background:linear-gradient(135deg,var(--color-primary),var(--color-accent));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}.models-header-actions{display:flex;gap:8px;flex-wrap:wrap}.models-status-bar{display:flex;align-items:center;justify-content:space-between;gap:18px;background:linear-gradient(135deg,rgba(108,92,231,.16),rgba(0,206,201,.08));border:1px solid var(--color-border);border-radius:18px;padding:20px}.models-status-main{display:flex;align-items:center;gap:14px;min-width:0}.models-status-main h2{font-size:18px;margin:0 0 4px}.models-status-main p{font-size:13px;color:var(--color-text-muted);margin:0}.models-status-pill{font-size:13px;font-weight:900;border-radius:999px;padding:8px 12px;background:var(--color-surface);border:1px solid var(--color-border);white-space:nowrap}.models-status-pill.ready{color:var(--color-like)}.models-status-pill.running{color:var(--color-primary-light)}.models-status-pill.error{color:var(--color-dislike)}.models-status-side{display:flex;align-items:center;gap:10px;flex-wrap:wrap;justify-content:flex-end}.models-status-side span{min-width:86px;background:var(--color-surface);border:1px solid var(--color-border);border-radius:13px;padding:9px 12px;display:flex;flex-direction:column}.models-status-side b{font-size:18px;background:linear-gradient(135deg,var(--color-primary),var(--color-accent));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}.models-status-side small{font-size:11px;color:var(--color-text-muted);margin-top:2px}.models-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.models-card{position:relative;overflow:hidden;background:var(--color-surface);border:1px solid var(--color-border);border-radius:16px;padding:24px;transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease;cursor:default}.models-card::before{content:"";position:absolute;inset:0 0 auto;height:4px;background:var(--model-tone,var(--color-primary))}.models-card::after{content:"";position:absolute;right:-44px;top:-44px;width:120px;height:120px;border-radius:50%;background:var(--model-tone,var(--color-primary));opacity:.08;pointer-events:none;transition:opacity .2s}.models-card:hover{transform:translateY(-4px);border-color:var(--color-primary);box-shadow:0 18px 48px rgba(0,0,0,.18)}.models-card:hover::after{opacity:.15}.models-card.tone-0{--model-tone:var(--color-primary)}.models-card.tone-1{--model-tone:#0984e3}.models-card.tone-2{--model-tone:#636e72}.models-card.tone-3{--model-tone:var(--color-like)}.models-card.tone-4{--model-tone:#e17055}.models-card.tone-5{--model-tone:#e84393}.models-card-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:14px}.models-card-icon{width:48px;height:48px;border-radius:14px;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,var(--model-tone,var(--color-primary)),var(--color-accent));color:#fff;font-size:13px;font-weight:900}.models-card-badge{font-size:11px;font-weight:800;border-radius:999px;padding:4px 10px;background:var(--color-bg);color:var(--color-text-muted)}.models-card-badge.active{background:rgba(0,184,148,.14);color:var(--color-like)}.models-card h3{font-size:17px;margin:0 0 6px}.models-card p{min-height:38px;font-size:12px;line-height:1.55;color:var(--color-text-muted);margin:0 0 16px}.models-card-stats{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:16px}.models-card-stats span{display:flex;flex-direction:column;gap:2px;min-width:0}.models-card-stats b{font-size:18px;font-weight:900;color:var(--color-primary-light);font-variant-numeric:tabular-nums}.models-card-stats small{font-size:10px;color:var(--color-text-muted);text-transform:uppercase;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.models-weight-line{display:flex;flex-direction:column;gap:8px;margin-bottom:14px}.models-weight-line>div:first-child{display:flex;justify-content:space-between;font-size:12px;color:var(--color-text-muted)}.models-weight-line b{color:var(--color-text);font-size:13px}.models-weight-track{height:8px;background:var(--color-bg);border-radius:999px;overflow:hidden}.models-weight-track span{display:block;height:100%;border-radius:999px;background:linear-gradient(90deg,var(--color-primary),var(--color-accent));transition:width .2s ease}.models-expand-btn{width:100%;border:1px solid var(--color-border);background:var(--color-bg);color:var(--color-text);border-radius:10px;padding:8px 10px;font-size:12px;font-weight:800;cursor:pointer;transition:border-color .15s,background .15s}.models-expand-btn:hover{border-color:var(--color-primary);background:var(--color-surface-hover)}.models-detail-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px;padding-top:12px;border-top:1px solid var(--color-border)}.models-detail-grid span{background:var(--color-bg);border-radius:10px;padding:10px;display:flex;flex-direction:column}.models-detail-grid b{font-size:15px;color:var(--color-primary-light)}.models-detail-grid small{font-size:11px;color:var(--color-text-muted);margin-top:2px}.models-progress-panel{display:grid;grid-template-columns:112px minmax(0,1fr);gap:18px;align-items:center;background:var(--color-surface);border:1px solid var(--color-border);border-radius:16px;padding:18px}.models-console-grid{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(320px,.75fr);gap:18px}.models-panel{background:var(--color-surface);border:1px solid var(--color-border);border-radius:16px;padding:20px}.models-panel-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:16px}.models-panel-head h3{font-size:16px;margin:0}.models-panel-head span{font-size:11px;color:var(--color-text-muted);background:var(--color-bg);border-radius:999px;padding:4px 10px}.models-control-row{display:grid;grid-template-columns:minmax(110px,.7fr) repeat(4,auto);gap:10px;align-items:end}.models-control-row label{display:flex;flex-direction:column;gap:5px}.models-control-row small{font-size:11px;font-weight:800;color:var(--color-text-muted)}.models-control-row input{width:100%;padding:8px 10px}.models-log-list{margin-top:16px;display:flex;flex-direction:column;gap:8px;max-height:168px;overflow:auto}.models-log-row{display:grid;grid-template-columns:150px 78px minmax(0,1fr);gap:10px;align-items:center;background:var(--color-bg);border-radius:10px;padding:9px 11px;font-size:12px}.models-log-row span{color:var(--color-text-muted)}.models-log-row b{color:var(--color-primary-light)}.models-log-row small{color:var(--color-text-muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.models-slider-list{display:flex;flex-direction:column;gap:14px}.models-slider-row{display:grid;grid-template-columns:96px minmax(0,1fr) 48px;align-items:center;gap:12px;font-size:13px;font-weight:700}.models-slider-row span{color:var(--color-text)}.models-slider-row b{text-align:right;color:var(--color-primary-light);font-variant-numeric:tabular-nums}.models-slider-row input[type=range]{accent-color:var(--color-primary);width:100%}.models-save-btn{width:100%;margin-top:18px;justify-content:center}.models-chart{height:260px;display:grid;grid-template-columns:repeat(6,minmax(70px,1fr));gap:14px;align-items:end;padding:14px 6px 0}.models-chart-cell{height:100%;display:grid;grid-template-rows:24px minmax(0,1fr) 24px;align-items:end;text-align:center;gap:8px}.models-chart-value{font-size:12px;font-weight:900;color:var(--color-primary-light);font-variant-numeric:tabular-nums}.models-chart-bar-wrap{height:100%;display:flex;align-items:flex-end;justify-content:center;background:linear-gradient(180deg,transparent,rgba(108,92,231,.06));border-radius:12px;padding:0 14px}.models-chart-bar{width:100%;min-height:0;border-radius:12px 12px 0 0;background:linear-gradient(180deg,var(--color-primary),var(--color-accent));box-shadow:0 10px 24px rgba(108,92,231,.24);transition:height .25s ease}.models-chart-cell small{font-size:11px;color:var(--color-text-muted);white-space:nowrap}.models-history-table td,.models-history-table th{padding:10px 12px}.models-status-text{font-weight:900}.models-status-text.success{color:var(--color-like)}.models-status-text.failed{color:var(--color-dislike)}.models-status-text.running{color:var(--color-primary-light)}
.models-card{cursor:pointer}.models-card.expanded{border-color:var(--color-primary)}.models-detail-wide{grid-column:1 / -1}.models-detail-wide b{font-size:12px;line-height:1.45}.train-config{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:14px}.train-config label{display:flex;flex-direction:column;gap:6px}.train-config span{font-size:11px;font-weight:800;color:var(--color-text-muted)}.train-config select,.train-config input{width:100%;padding:9px 12px;background:var(--color-bg);color:var(--color-text);border:1px solid var(--color-border);border-radius:10px;font-size:13px}.train-config select:focus,.train-config input:focus{border-color:var(--color-primary)}.train-actions{display:flex;flex-direction:column;gap:12px}.train-options{display:flex;align-items:center;gap:10px;flex-wrap:wrap}.train-buttons{display:flex;align-items:center;gap:10px}.switch-row{display:flex;align-items:center;gap:9px;font-size:13px;font-weight:800;color:var(--color-text-muted)}.switch{width:44px;height:26px;border:0;border-radius:999px;background:var(--color-border);position:relative;cursor:pointer;transition:background .2s}.switch::after{content:"";position:absolute;top:3px;left:3px;width:20px;height:20px;border-radius:50%;background:#fff;transition:transform .2s}.switch.on{background:var(--color-primary)}.switch.on::after{transform:translateX(18px)}.switch:disabled{opacity:.45;cursor:not-allowed}.btn-danger{border:1px solid rgba(224,85,72,.35);background:transparent;color:var(--color-dislike)}.btn-danger:hover:not(:disabled){background:rgba(224,85,72,.1)}.sample-control{display:flex;align-items:center;gap:8px;font-size:12px;font-weight:800;color:var(--color-text-muted)}.sample-control input{width:86px;padding:8px 10px}.progress-track.striped .progress-fill{background:repeating-linear-gradient(-45deg,var(--color-primary),var(--color-primary) 8px,var(--color-primary-light) 8px,var(--color-primary-light) 16px);animation:barber 1s linear infinite}.tp-log{margin-top:12px;max-height:140px;overflow-y:auto;font-family:"SF Mono",Consolas,monospace;font-size:11px;background:var(--color-bg);border:1px solid var(--color-border);border-radius:10px;padding:10px}.tp-log .line{padding:2px 0;color:var(--color-text-muted)}.tp-log .line.info{color:var(--color-accent)}.tp-log .line.warn{color:#f0c060}.tp-log .line.done{color:var(--color-like)}.eval-table{width:100%;border-collapse:collapse}.eval-table th,.eval-table td{padding:12px 14px;text-align:left;border-bottom:1px solid var(--color-border);font-size:13px}.eval-table th{font-size:11px;color:var(--color-text-muted);text-transform:uppercase;cursor:pointer;user-select:none}.eval-table tr:hover td{background:var(--color-surface-hover)}.eval-bar-wrap{display:flex;align-items:center;gap:8px;min-width:170px}.eval-bar{flex:1;height:6px;background:var(--color-bg);border-radius:999px;overflow:hidden}.eval-bar-fill{display:block;height:100%;border-radius:999px}.eval-bar-fill.precision{background:linear-gradient(90deg,var(--color-primary),var(--color-accent))}.eval-bar-fill.recall{background:linear-gradient(90deg,var(--color-like),var(--color-accent))}.eval-bar-fill.hitrate{background:linear-gradient(90deg,#f0c060,var(--color-dislike))}.eval-val{min-width:52px;text-align:right;color:var(--color-primary-light);font-variant-numeric:tabular-nums}.radar-section{display:grid;grid-template-columns:1fr 1fr;gap:18px}.radar-card{background:var(--color-surface);border:1px solid var(--color-border);border-radius:16px;padding:20px}.radar-card h3{font-size:16px;margin:0 0 16px}.radar-viz{display:flex;justify-content:center;align-items:center;min-height:230px}.radar-svg{width:100%;max-width:300px}.radar-grid{fill:none;stroke:var(--color-border);stroke-width:1}.radar-grid.inner{opacity:.7}.radar-axis{stroke:var(--color-border);stroke-width:1}.radar-label{font-size:9px;fill:var(--color-text-muted);text-anchor:middle;dominant-baseline:middle}.radar-area{fill:rgba(56,189,248,.18);stroke:var(--color-primary);stroke-width:2}.radar-area.second{fill:rgba(125,211,252,.08);stroke:var(--color-accent);stroke-width:2;stroke-dasharray:6 3}.radar-dot{fill:var(--color-primary)}.radar-legend{display:flex;gap:16px;justify-content:center;margin-top:12px}.radar-legend span{display:flex;align-items:center;gap:6px;font-size:11px;color:var(--color-text-muted)}.swatch{width:14px;height:3px;border-radius:4px;background:var(--color-primary)}.swatch.average{background:var(--color-accent)}.timeline{display:flex;flex-direction:column}.tl-item{display:grid;grid-template-columns:128px 1fr;gap:14px;padding:14px 0;border-bottom:1px solid var(--color-border)}.tl-item:last-child{border-bottom:0}.tl-time{font-size:12px;color:var(--color-text-muted)}.tl-title{font-size:14px;font-weight:800}.tl-desc{font-size:12px;color:var(--color-text-muted);margin-top:4px}.tl-tags{display:flex;gap:6px;margin-top:6px}.tl-tag{font-size:11px;border-radius:999px;background:var(--color-bg);color:var(--color-text-muted);padding:3px 8px}.tl-tag.good{background:rgba(20,184,166,.12);color:var(--color-like)}.tl-tag.bad{background:rgba(224,85,72,.12);color:var(--color-dislike)}
.progress-ring.done{background:conic-gradient(var(--color-like) var(--p),var(--color-bg) 0)}.progress-ring.done::after{background:var(--color-surface)}.progress-ring.done span{color:var(--color-like);font-size:28px}.progress-fill.done{background:var(--color-like)}.models-progress-panel.done{border-color:rgba(0,184,148,.35)}
@keyframes barber{0%{background-position:0 0}100%{background-position:32px 0}}
@keyframes fadeUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
@media(max-width:900px){.two-col{grid-template-columns:1fr}.topbar{flex-direction:column;gap:10px}.data-table{display:block;overflow-x:auto}.form-grid{grid-template-columns:1fr}}
@media(max-width:900px){.overview-rank-layout,.model-info-grid{grid-template-columns:1fr}.model-hero-panel{flex-direction:column}.rank-grid{grid-template-columns:1fr}.podium-item.gold .podium-cover{width:96px;height:96px}.podium-item.silver .podium-cover{width:82px;height:82px}.podium-item.bronze .podium-cover{width:72px;height:72px}.podium-char{font-size:32px}.podium-item.gold .podium-char{font-size:36px}}
@media(max-width:768px){.podium{gap:10px;min-height:170px}.rank-row{grid-template-columns:30px 40px minmax(0,1fr) auto;gap:6px 8px;padding:8px 10px}.rank-mini-cover{width:40px;height:40px;font-size:16px}.rank-value{font-size:12px;padding:4px 8px}.model-progress-panel{grid-template-columns:1fr}.progress-ring{margin:auto}.model-control-panel{align-items:stretch;flex-direction:column}.sample-control{justify-content:space-between}.sample-control input{width:120px}}
@media(max-width:900px){.models-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.models-status-bar,.models-status-main{align-items:flex-start;flex-direction:column}.models-status-side{justify-content:flex-start}.models-console-grid{grid-template-columns:1fr}.models-control-row{grid-template-columns:1fr 1fr}.models-chart{grid-template-columns:repeat(6,minmax(54px,1fr));gap:8px}.models-chart-bar-wrap{padding:0 8px}}
@media(max-width:1000px){.train-config{grid-template-columns:repeat(2,minmax(0,1fr))}.radar-section{grid-template-columns:1fr}.eval-table{display:block;overflow-x:auto}}
@media(max-width:600px){.models-grid{grid-template-columns:1fr}.models-status-side{width:100%;display:grid;grid-template-columns:1fr 1fr}.models-status-side .btn{grid-column:1 / -1;justify-content:center}.models-control-row{grid-template-columns:1fr}.models-log-row{grid-template-columns:1fr;gap:3px}.models-slider-row{grid-template-columns:82px minmax(0,1fr) 44px}.models-progress-panel{grid-template-columns:1fr}.models-chart{height:220px;overflow-x:auto;grid-template-columns:repeat(6,64px)}}
@media(max-width:640px){.train-config{grid-template-columns:1fr}.train-actions{align-items:stretch;flex-direction:column}.train-actions .btn{justify-content:center}.tl-item{grid-template-columns:1fr;gap:4px}}

.theme-btn{width:32px;height:32px;border-radius:50%;border:1px solid var(--color-border);background:var(--color-surface);color:var(--color-text);cursor:pointer;font-size:16px;display:flex;align-items:center;justify-content:center;transition:background .2s}.theme-btn:hover{background:var(--color-surface-hover)}
.import-progress{margin:12px 0}.import-progress p{font-size:13px;color:var(--color-text-muted)}.import-progress .progress-bar{height:6px;background:var(--color-border);border-radius:3px;margin-top:6px}.import-progress .progress-fill{height:100%;background:var(--color-primary);border-radius:3px;transition:width .3s}</style>
