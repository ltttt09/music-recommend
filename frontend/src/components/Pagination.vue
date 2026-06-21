<template>
  <div class="pagination-row">
    <p class="pagination-info">共 {{ totalItems }} {{ itemName || '条' }}，第 {{ current }} / {{ total }} 页</p>
    <div class="pager-actions">
      <button class="btn btn-ghost btn-xs" :disabled="current <= 1" @click="go(current - 1)">上一页</button>
      <template v-if="total <= 7">
        <button v-for="p in pageRange" :key="p" class="btn btn-ghost btn-xs" :class="{ active: p === current }" @click="go(p)">{{ p }}</button>
      </template>
      <template v-else>
        <button v-if="current > 3" class="btn btn-ghost btn-xs" @click="go(1)">1</button>
        <span v-if="current > 4" class="pager-ellipsis">...</span>
        <button v-for="p in windowPages" :key="p" class="btn btn-ghost btn-xs" :class="{ active: p === current }" @click="go(p)">{{ p }}</button>
        <span v-if="current < total - 3" class="pager-ellipsis">...</span>
        <button v-if="current < total - 2" class="btn btn-ghost btn-xs" @click="go(total)">{{ total }}</button>
      </template>
      <button class="btn btn-ghost btn-xs" :disabled="current >= total" @click="go(current + 1)">下一页</button>
      <span class="pager-jump">
        跳至 <input type="number" class="pager-input" :min="1" :max="total" v-model.number="jumpPage" @keyup.enter="doJump" /> 页
        <button class="btn btn-ghost btn-xs" @click="doJump" :disabled="!validJump">跳转</button>
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  current: { type: Number, default: 1 },
  total: { type: Number, default: 1 },
  totalItems: { type: Number, default: 0 },
  itemName: { type: String, default: '条' },
})
const emit = defineEmits(['page-change'])

const jumpPage = ref(props.current)
watch(() => props.current, (v) => { jumpPage.value = v })

const pageRange = computed(() => {
  const pages = []
  for (let i = 1; i <= props.total; i++) pages.push(i)
  return pages
})

const windowPages = computed(() => {
  const pages = []
  const start = Math.max(2, props.current - 1)
  const end = Math.min(props.total - 1, props.current + 1)
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
})

const validJump = computed(() => {
  return jumpPage.value >= 1 && jumpPage.value <= props.total && jumpPage.value !== props.current
})

function go(p) {
  if (p >= 1 && p <= props.total && p !== props.current) {
    emit('page-change', p)
  }
}

function doJump() {
  if (validJump.value) {
    emit('page-change', jumpPage.value)
  }
}
</script>

<style scoped>
.pagination-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding: 8px 0;
  gap: 8px;
  flex-wrap: wrap;
}
.pagination-info {
  font-size: 13px;
  color: var(--color-text-muted);
}
.pager-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}
.pager-actions .btn.active {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}
.pager-ellipsis {
  color: var(--color-text-muted);
  padding: 0 4px;
  font-size: 13px;
}
.pager-jump {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--color-text-muted);
  margin-left: 8px;
}
.pager-input {
  width: 48px;
  padding: 2px 4px;
  font-size: 13px;
  text-align: center;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: var(--color-surface);
  color: var(--color-text);
}
.pager-input:focus {
  outline: none;
  border-color: var(--color-primary);
}
</style>
