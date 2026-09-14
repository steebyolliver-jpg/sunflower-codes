export const isExpired = (item, now = Date.now()) => Boolean(item.expiresAt && Date.parse(item.expiresAt) <= now);
export function setUsed(state, code, checked) {
  const next = { ...state };
  if (checked) next[code] = true;
  else delete next[code];
  return next;
}
export function isCatalog(value) {
  return Boolean(value && Array.isArray(value.codes) && value.codes.length > 0 && value.codes.length < 10000 &&
    value.codes.every(item => item && /^[A-Za-z0-9]{5,24}$/.test(item.code) &&
      ['official', 'screenshot'].includes(item.sourceType) &&
      (!item.expiresAt || Number.isFinite(Date.parse(item.expiresAt)))) &&
    new Set(value.codes.map(item => item.code)).size === value.codes.length);
}
export function visibleCodes(catalog, used, filter, showExpired, now = Date.now()) {
  return catalog.codes.filter(item => (showExpired || !isExpired(item, now)) &&
    (filter === 'all' || (filter === 'used' ? used[item.code] : !used[item.code])))
    .sort((a, b) => Number(isExpired(a, now)) - Number(isExpired(b, now)) ||
      Number(Boolean(used[a.code])) - Number(Boolean(used[b.code])) ||
      Number(b.sourceType === 'official') - Number(a.sourceType === 'official') ||
      (b.firstSeen || '').localeCompare(a.firstSeen || ''));
}
