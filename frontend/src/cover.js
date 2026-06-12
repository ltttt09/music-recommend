const GENRE_GRADIENTS = [
  { test: /CN|华语|中文|C-Pop|Mandopop|Cantopop/i, value: 'linear-gradient(145deg,#d94848 0%,#f59f00 54%,#ffe066 100%)' },
  { test: /Rock|摇滚|Metal|Punk/i, value: 'linear-gradient(145deg,#212529 0%,#c92a2a 58%,#f08c00 100%)' },
  { test: /Electronic|电子|Dance|EDM|House|Techno/i, value: 'linear-gradient(145deg,#0b7285 0%,#15aabf 52%,#99e9f2 100%)' },
  { test: /Hip.?Hop|Rap|说唱/i, value: 'linear-gradient(145deg,#343a40 0%,#7048e8 56%,#da77f2 100%)' },
  { test: /Jazz|爵士|Blues|蓝调/i, value: 'linear-gradient(145deg,#364fc7 0%,#748ffc 54%,#ffd43b 100%)' },
  { test: /Classical|古典|Opera/i, value: 'linear-gradient(145deg,#5f3dc4 0%,#b197fc 55%,#f8f0fc 100%)' },
  { test: /Folk|民谣|Country/i, value: 'linear-gradient(145deg,#2b8a3e 0%,#82c91e 52%,#ffd43b 100%)' },
  { test: /Pop|流行/i, value: 'linear-gradient(145deg,#e64980 0%,#f783ac 52%,#fcc2d7 100%)' },
]

const FALLBACK_GRADIENTS = [
  'linear-gradient(145deg,#1864ab 0%,#4dabf7 54%,#a5d8ff 100%)',
  'linear-gradient(145deg,#087f5b 0%,#38d9a9 54%,#c3fae8 100%)',
  'linear-gradient(145deg,#862e9c 0%,#cc5de8 54%,#eebefa 100%)',
  'linear-gradient(145deg,#9c36b5 0%,#f06595 54%,#ffc9c9 100%)',
  'linear-gradient(145deg,#495057 0%,#868e96 54%,#dee2e6 100%)',
]

export function coverText(title = '') {
  return '\u266B'
}

export function coverStyle(id = 0, genre = '') {
  const matched = GENRE_GRADIENTS.find(item => item.test.test(genre || ''))
  if (matched) return { background: matched.value }
  return { background: FALLBACK_GRADIENTS[Math.abs(Number(id) || 0) % FALLBACK_GRADIENTS.length] }
}
