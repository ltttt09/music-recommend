export const PREFERENCE_GENRES = [
  '流行',
  '摇滚',
  '民谣',
  '电子',
  '说唱',
  '古典',
  '爵士',
  '华语',
  '欧美',
  '日语',
  '韩语',
  'R&B',
  '乡村',
  '舞曲',
]

export function parsePreferences(value = '') {
  return new Set(String(value).split(/[,，]/).map((item) => item.trim()).filter(Boolean))
}

export function stringifyPreferences(values) {
  return [...values].join(', ')
}
