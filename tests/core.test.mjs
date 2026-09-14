import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';

test('兑换状态与码库逻辑已实现', () => assert.ok(existsSync(new URL('../dist/core.mjs', import.meta.url))));
const core = existsSync(new URL('../dist/core.mjs', import.meta.url)) ? await import('../dist/core.mjs') : {};
test('过期按公告的北京时间判定', () => {
  assert.equal(core.isExpired?.({ expiresAt: '2026-09-24T23:59:00+08:00' }, Date.parse('2026-09-24T16:00:00Z')), true);
});
test('已用状态序列化后保持大小写且支持取消', () => {
  const used = core.setUsed?.({}, 'AbC123', true);
  assert.deepEqual(JSON.parse(JSON.stringify(used ?? null)), { AbC123: true });
  assert.deepEqual(core.setUsed?.(used, 'AbC123', false), {});
});
test('异常码库不能覆盖本地缓存', () => {
  assert.equal(core.isCatalog?.({ codes: [{ code: '<script>' }] }), false);
  assert.equal(core.isCatalog?.({ codes: [{ code: 'AbC123', sourceType: 'screenshot' }] }), true);
});
