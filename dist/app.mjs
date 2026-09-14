import { isCatalog, isExpired, setUsed, visibleCodes } from './core.mjs';

const USED_KEY = 'sunflower.used.v1';
const CACHE_KEY = 'sunflower.catalog.v1';
const $ = selector => document.querySelector(selector);
let used = {}, catalog = null, filter = 'unused', showExpired = false, loading = false, toastTimer;

function warn(message) { $('#storage-warning').textContent = message; $('#storage-warning').hidden = false; }
function toast(message) {
  clearTimeout(toastTimer);
  $('#toast').textContent = message;
  $('#toast').hidden = false;
  toastTimer = setTimeout(() => { $('#toast').hidden = true; }, 2600);
}
try {
  const saved = JSON.parse(localStorage.getItem(USED_KEY) || '{}');
  if (!saved || typeof saved !== 'object' || Array.isArray(saved)) throw new Error('invalid state');
  used = Object.fromEntries(Object.entries(saved).filter(([key, value]) => /^[A-Za-z0-9]{5,24}$/.test(key) && value === true));
} catch { warn('无法读取已用记录。请使用普通 Safari 窗口，并允许保存网站数据。'); }
try {
  const cached = JSON.parse(localStorage.getItem(CACHE_KEY) || 'null');
  if (isCatalog(cached)) catalog = cached;
} catch { /* Network loading remains available when a cache is unavailable. */ }

function element(tag, className, text) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (text !== undefined) el.textContent = text;
  return el;
}
function dateText(value, withTime = false) {
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) return '尚未检查';
  return new Intl.DateTimeFormat('zh-CN', { timeZone: 'Asia/Shanghai', month: '2-digit', day: '2-digit', ...(withTime ? { hour: '2-digit', minute: '2-digit', hour12: false } : {}) }).format(date);
}
function updateMeta() {
  if (!catalog) return;
  const checked = catalog.lastSuccessfulCheck;
  const stale = checked && Date.now() - Date.parse(checked) > 36 * 60 * 60 * 1000;
  $('#sync-status').textContent = checked ? `来源检查 ${dateText(checked, true)}${stale ? ' · 待更新' : ''}` : '尚未完成来源检查';
  if (catalog.checkStatus === 'failed') $('#sync-status').textContent += ' · 最近检查失败';
  $('#automation-status').textContent = catalog.automationStatus === 'enabled' ? '每天检查公开来源 · 北京时间' : '每日自动检查尚未启用';
}
function render() {
  const list = $('#code-list');
  list.setAttribute('aria-busy', String(loading));
  if (!catalog) { list.replaceChildren(element('p', 'empty', loading ? '正在收集阳光…' : '暂时无法读取码库，请联网后点击刷新。')); return; }
  const active = catalog.codes.filter(item => !isExpired(item));
  $('#remaining').textContent = active.filter(item => !used[item.code]).length;
  $('#used-count').textContent = `已用 ${catalog.codes.filter(item => used[item.code]).length} / 共收录 ${catalog.codes.length}`;
  const visible = visibleCodes(catalog, used, filter, showExpired);
  $('#list-count').textContent = `${visible.length} 个兑换码 · 官方新码优先`;
  const fragment = document.createDocumentFragment();
  for (const item of visible) {
    const expired = isExpired(item), checked = Boolean(used[item.code]);
    const card = element('article', `code-card ${item.sourceType === 'official' ? 'official' : ''} ${checked ? 'used' : ''} ${expired ? 'expired-card' : ''}`);
    card.dataset.code = item.code;
    const top = element('div', 'card-top');
    const code = element('span', 'code', item.code);
    const copy = element('button', 'copy', '复制');
    copy.type = 'button';
    copy.setAttribute('aria-label', `复制 ${item.code}`);
    copy.addEventListener('click', () => copyCode(item.code, copy));
    top.append(code, copy);
    const badges = element('div', 'badges');
    badges.append(element('span', `badge ${expired ? 'expired' : item.sourceType === 'official' ? '' : 'unknown'}`, expired ? '已过期' : item.sourceType === 'official' ? '官方发布' : '历史码 · 待验证'));
    if (item.expiresAt) badges.append(element('span', 'expiry', `${dateText(item.expiresAt, true)} 到期`));
    else badges.append(element('span', '', '有效期待核实'));
    const bottom = element('div', 'card-bottom');
    const validSource = typeof item.sourceUrl === 'string' && /^https:\/\/www\.taptap\.cn\/moment\/\d+$/.test(item.sourceUrl);
    const source = element(validSource ? 'a' : 'span', 'source', validSource ? '官方出处 ↗ · 微信待验证' : '截图收录 · 微信待验证');
    if (validSource) { source.href = item.sourceUrl; source.target = '_blank'; source.rel = 'noopener noreferrer'; }
    const label = element('label', 'used-label');
    const checkbox = element('input'); checkbox.type = 'checkbox'; checkbox.checked = checked;
    checkbox.setAttribute('aria-label', `${item.code} 已使用`);
    checkbox.addEventListener('change', () => {
      const next = setUsed(used, item.code, checkbox.checked);
      try { localStorage.setItem(USED_KEY, JSON.stringify(next)); used = next; }
      catch { checkbox.checked = checked; warn('保存失败，本次勾选没有保存。请检查 Safari 的网站数据设置或设备存储空间。'); return; }
      toast(checkbox.checked ? '已记下，下次不会忘 🌱' : '已恢复为未使用');
      render();
    });
    label.append(checkbox, document.createTextNode('已使用'));
    bottom.append(source, label);
    card.append(top, badges, bottom); fragment.append(card);
  }
  if (!visible.length) fragment.append(element('p', 'empty', filter === 'used' ? '还没有已用记录。兑换后打个勾吧 🌱' : '这里都收好啦 🌻\n可以切换筛选查看其他兑换码。'));
  list.replaceChildren(fragment);
}
async function copyCode(code, button) {
  try {
    if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
    await navigator.clipboard.writeText(code);
    button.textContent = '已复制'; button.classList.add('done');
    toast('已复制，去微信兑换吧');
    setTimeout(() => { button.textContent = '复制'; button.classList.remove('done'); }, 1800);
  } catch {
    $('#manual-code').value = code;
    $('#manual-copy').showModal();
    $('#manual-code').focus(); $('#manual-code').select();
  }
}
async function refresh(manual = false) {
  if (loading) return;
  loading = true; $('#refresh').disabled = true; render();
  const controller = new AbortController(), timeout = setTimeout(() => controller.abort(), 12000);
  try {
    const response = await fetch(`./data/codes.json?t=${Date.now()}`, { cache: 'no-store', signal: controller.signal });
    if (!response.ok) throw new Error('HTTP error');
    const latest = await response.json();
    if (!isCatalog(latest)) throw new Error('Invalid catalog');
    const previous = new Set(catalog?.codes.map(item => item.code) || []);
    const added = latest.codes.filter(item => !previous.has(item.code)).length;
    catalog = latest;
    try { localStorage.setItem(CACHE_KEY, JSON.stringify(catalog)); }
    catch { warn('码库已读取，但无法保存离线副本。'); }
    updateMeta();
    if (manual) toast(latest.checkStatus === 'failed' ? '已读取现有码库，最近的来源检查失败' : added ? `发现 ${added} 个新收录兑换码` : '已读取最新码库，暂无新增');
  } catch {
    updateMeta();
    $('#sync-status').textContent = catalog ? `当前离线或连接失败 · 保留 ${catalog.codes.length} 个码` : '连接失败，尚无本地码库';
    if (manual) toast('连接失败，已有兑换码和勾选仍保留');
  } finally { clearTimeout(timeout); loading = false; $('#refresh').disabled = false; render(); }
}
document.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click', () => {
  filter = button.dataset.filter;
  document.querySelectorAll('[data-filter]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
  render();
}));
$('#show-expired').addEventListener('change', event => { showExpired = event.target.checked; render(); });
$('#refresh').addEventListener('click', () => refresh(true));
$('#close-dialog').addEventListener('click', () => $('#manual-copy').close());
window.addEventListener('storage', event => {
  if (event.key !== USED_KEY) return;
  try { const value = JSON.parse(event.newValue || '{}'); if (value && typeof value === 'object' && !Array.isArray(value)) { used = value; render(); } } catch { /* Preserve current state. */ }
});
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible' && catalog && Date.now() - Date.parse(catalog.lastSuccessfulCheck || 0) > 24 * 60 * 60 * 1000) refresh();
});
if ('serviceWorker' in navigator && window.isSecureContext) navigator.serviceWorker.register('./sw.js').catch(() => {});
updateMeta(); refresh();
