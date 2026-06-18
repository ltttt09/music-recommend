import { ref } from 'vue'
import api from '../api.js'
import { auth } from '../auth.js'

export function useRecommendations(defaultModel = 'hybrid') {
  const items = ref([])
  const loading = ref(false)
  const error = ref('')
  const toast = ref('')
  const model = ref(defaultModel)
  const CACHE_TTL = 6 * 60 * 60 * 1000

  function userId() {
    return auth.userId || Number(localStorage.getItem('user_id')) || 0
  }

  function cacheKey(uid, n) {
    return `recommend-cache:${uid}:${model.value}:${n}`
  }

  function readCache(uid, n) {
    const raw = localStorage.getItem(cacheKey(uid, n))
    if (!raw) return false
    try {
      const cached = JSON.parse(raw)
      if (Date.now() - Number(cached.created_at || 0) > CACHE_TTL) return false
      items.value = cached.items || []
      return items.value.length > 0
    } catch {
      return false
    }
  }

  function writeCache(uid, n) {
    localStorage.setItem(cacheKey(uid, n), JSON.stringify({
      created_at: Date.now(),
      items: items.value,
    }))
  }

  function showToast(message) {
    toast.value = message
    setTimeout(() => { toast.value = '' }, 2200)
  }

  async function fetchPersonalized({ refresh = false, n = 10 } = {}) {
    const uid = userId()
    if (!uid) {
      items.value = []
      error.value = '请先登录后再获取个性化推荐'
      return []
    }
    loading.value = true
    error.value = ''
    if (!refresh && readCache(uid, n)) {
      loading.value = false
      return items.value
    }
    const excludeIds = refresh ? items.value.map((item) => item.id) : []
    try {
      const data = await api.getRecommendations(uid, model.value, n, excludeIds, refresh)
      items.value = data.items || []
      if (!items.value.length) error.value = data.error || '暂无推荐结果'
      else writeCache(uid, n)
      return items.value
    } catch (e) {
      error.value = e.message || '推荐加载失败'
      items.value = []
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchColdStart(trackIds, n = 10) {
    loading.value = true
    error.value = ''
    try {
      const data = await api.coldStartRecommend(trackIds, n)
      items.value = data.items || []
      if (!items.value.length) error.value = '暂无推荐结果，请重新选择歌曲'
      return items.value
    } catch (e) {
      error.value = e.message || '推荐加载失败'
      items.value = []
      return []
    } finally {
      loading.value = false
    }
  }

  async function submitFeedback(track, rating) {
    const uid = userId()
    if (!uid) {
      showToast('请先登录')
      return null
    }
    const data = await api.submitFeedback(uid, track.id, rating, model.value)
    if (rating > 0) {
      track.user_liked = Boolean(data.liked)
      window.dispatchEvent(new CustomEvent('home-data-invalidated', { detail: { reason: 'likes' } }))
      showToast(data.liked ? '已标记喜欢' : '已取消喜欢')
    } else if (rating < 0) {
      track.user_skipped = true
      items.value = items.value.filter((item) => item.id !== track.id)
      window.dispatchEvent(new CustomEvent('home-data-invalidated', { detail: { reason: 'blacklist' } }))
      showToast('已移入黑名单，短期内不会再推荐')
    }
    return data
  }

  return {
    items,
    loading,
    error,
    toast,
    model,
    fetchPersonalized,
    fetchColdStart,
    submitFeedback,
  }
}
