import { describe, expect, it } from 'vitest'

import { coverStyle, coverText } from './cover.js'

describe('cover fallback', () => {
  it('uses a stable music symbol instead of title text', () => {
    expect(coverText('万里长城永不倒')).toBe('♫')
  })

  it('returns a genre-specific gradient for Chinese music', () => {
    expect(coverStyle(1, 'CN-Pop').background).toContain('linear-gradient')
  })
})
