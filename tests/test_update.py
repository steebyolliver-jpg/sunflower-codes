import importlib.util
import unittest
from pathlib import Path

MODULE = Path(__file__).parents[1] / 'scripts' / 'update_codes.py'

class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(MODULE.exists(), '兑换码采集器尚未实现')
        spec = importlib.util.spec_from_file_location('update_codes', MODULE)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)

    def test_extract_only_article_codes_and_expiry(self):
        html = '<title>保卫向日葵</title><a href="/moment/123456"><p>教师节兑换码来啦<br>V4INKEJ<br>有效时间：2026年9月24日 23:59过期</p></a><script>FAKE123</script><a href="/user/44444">USER999</a>'
        rows = self.m.parse_page(html)
        self.assertEqual([r['code'] for r in rows], ['V4INKEJ'])
        self.assertEqual(rows[0]['expiresAt'], '2026-09-24T23:59:00+08:00')

    def test_explicit_code_and_midnight(self):
        html = '<title>保卫向日葵</title><a href="/moment/123456">联动福利礼包码：DECN5KD 兑换时间：2026年9月1日0点过期</a>'
        self.assertEqual(self.m.parse_page(html)[0]['expiresAt'], '2026-09-01T00:00:00+08:00')

    def test_layout_failure_is_not_success(self):
        with self.assertRaises(ValueError):
            self.m.parse_page('<html>Access denied</html>')

    def test_customer_contact_is_not_a_voucher_and_draw_deadline_is_not_expiry(self):
        html = '<title>保卫向日葵</title><a href="/moment/123456"><p>今日福利兑换码：ABC123</p><p>回复抽奖活动将在2026年9月1日0点截止，礼包码长期有效</p><p>客服微信</p><p>Service123</p></a>'
        rows = self.m.parse_page(html)
        self.assertEqual([r['code'] for r in rows], ['ABC123'])
        self.assertIsNone(rows[0]['expiresAt'])

    def test_unrelated_code_after_empty_voucher_heading_is_not_collected(self):
        html = '<title>保卫向日葵</title><a href="/moment/123456"><p>兑换码之后公布，请耐心等待</p><p>客服微信</p><p>Service123</p><p>联系客服了解后续活动详情</p></a>'
        self.assertEqual(self.m.parse_page(html), [])

    def test_contiguous_voucher_list_collects_all_codes(self):
        html = '<title>保卫向日葵</title><a href="/moment/123456">兑换码：<br>ABC123<br>DEF456<br>请在游戏兑换入口领取今日福利礼包<br>客服微信<br>Service123</a>'
        self.assertEqual([r['code'] for r in self.m.parse_page(html)], ['ABC123', 'DEF456'])

    def test_draw_validity_does_not_expire_permanent_voucher(self):
        html = '<title>保卫向日葵</title><a href="/moment/123456">兑换码：ABC123，长期有效<br>抽奖有效时间：2026年9月1日0点截止</a>'
        self.assertIsNone(self.m.parse_page(html)[0]['expiresAt'])

    def test_case_sensitive_merge_keeps_history(self):
        existing = {'codes': [{'code': 'AbC123', 'firstSeen': '2026-01-01', 'sourceType': 'screenshot', 'expiresAt': None}], 'lastSuccessfulCheck': 'old'}
        result = self.m.merge_catalog(existing, [{'code': 'ABC123', 'sourceType': 'official', 'expiresAt': None}], '2026-09-14T01:00:00Z')
        self.assertEqual([r['code'] for r in result['codes']], ['AbC123', 'ABC123'])
        self.assertEqual(result['codes'][0]['firstSeen'], '2026-01-01')
        self.assertEqual(len(self.m.merge_catalog(result, result['codes'], 'next')['codes']), 2)
        self.assertTrue(all('used' not in r for r in result['codes']))

    def test_official_update_preserves_existing_expiry_if_missing(self):
        old = {'codes': [{'code': 'ABC123', 'expiresAt': '2026-09-24T23:59:00+08:00', 'firstSeen': '2026-09-10'}]}
        result = self.m.merge_catalog(old, [{'code': 'ABC123', 'expiresAt': None, 'sourceType': 'official'}], 'now')
        self.assertEqual(result['codes'][0]['expiresAt'], old['codes'][0]['expiresAt'])

    def test_failure_preserves_success_timestamp_and_codes(self):
        old = {'codes': [{'code': 'VIP666'}], 'lastSuccessfulCheck': 'yesterday'}
        result = self.m.record_failure(old, 'today', ['连接超时'])
        self.assertEqual(result['lastSuccessfulCheck'], 'yesterday')
        self.assertEqual(result['codes'], old['codes'])
        self.assertEqual(result['checkStatus'], 'failed')

if __name__ == '__main__':
    unittest.main()
