import csv
import json
import re
import tempfile
import unittest
from pathlib import Path

from seeding import collect, config, dm_queue
from seeding.ig_api import GraphError, InstagramAPI, SampleTransport


def sample_api(**kwargs):
    return InstagramAPI("token", "0", transport=SampleTransport(config.SAMPLE_PROFILES), min_interval=0, **kwargs)


def read_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return {r["계정"]: r for r in csv.DictReader(f)}


class Usernames(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(collect.normalize_username("@Some.Name"), "some.name")
        self.assertEqual(collect.normalize_username("https://www.instagram.com/some_name/?hl=ko"), "some_name")
        self.assertIsNone(collect.normalize_username("https://www.instagram.com/p/ABC123/"))
        self.assertIsNone(collect.normalize_username("한글계정"))
        self.assertIsNone(collect.normalize_username(""))

    def test_read_sample_file(self):
        names, skipped = collect.read_usernames(config.SAMPLE_ACCOUNTS)
        self.assertEqual(len(names), 11)
        self.assertIn("sample_brunch_seoul", names)   # 주소로 적은 줄
        self.assertIn("sample_wine_and_rice", names)  # @를 붙여 적은 줄
        self.assertEqual(skipped, [])

    def test_read_cp949_file_without_header(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "list.csv"
            path.write_bytes("abc_one,메모\nabc_two,한글\nabc_one,중복\n".encode("cp949"))
            names, _ = collect.read_usernames(path)
        self.assertEqual(names, ["abc_one", "abc_two"])


class CollectRun(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.out = Path(self.dir.name) / "emails.csv"
        self.names, _ = collect.read_usernames(config.SAMPLE_ACCOUNTS)

    def tearDown(self):
        self.dir.cleanup()

    def test_full_run_on_sample_data(self):
        summary = collect.run(self.names, sample_api(), self.out, log=lambda *_: None)
        rows = read_rows(self.out)

        self.assertEqual(summary["전체"], 11)
        self.assertEqual(summary["메일 확보"], 6)
        self.assertEqual(summary["DM 대상"], 4)
        self.assertEqual(summary["수동 확인"], 1)

        self.assertEqual(rows["sample_homesool_diary"]["메일"], "homesool.diary@example.com")
        self.assertEqual(rows["sample_homesool_diary"]["다음 행동"], "메일 발송")
        self.assertEqual(rows["sample_makgeolli_note"]["메일"], "makgeolli.note@example.co.kr")
        self.assertEqual(rows["sample_table_for_two"]["메일"], "table.for.two@example.com")
        self.assertEqual(rows["sample_table_for_two"]["확인 필요"], "예")
        self.assertEqual(rows["sample_weekend_camper"]["메일"], "weekend.camper@example.com")
        self.assertEqual(rows["sample_foodie_jeju"]["메일"], "foodie.jeju@example.com")
        self.assertEqual(rows["sample_two_contacts"]["메일"], "ad.two@example.com; hello.two@example.com")

        self.assertEqual(rows["sample_cocktail_lab"]["다음 행동"], "DM")  # 멘션을 메일로 오인하지 않는다
        self.assertIn("링크 모음 페이지", rows["sample_wine_and_rice"]["비고"])
        self.assertIn("DM 문의", rows["sample_brunch_seoul"]["비고"])
        self.assertEqual(rows["sample_private_person"]["조회 결과"], "조회 불가")

        mail_rows = read_rows(collect.mail_targets_path(self.out))
        self.assertEqual(len(mail_rows), 6)

    def test_second_run_skips_finished_accounts(self):
        collect.run(self.names, sample_api(), self.out, log=lambda *_: None)
        calls = []

        def counting(url, timeout=20.0):
            calls.append(url)
            return SampleTransport(config.SAMPLE_PROFILES)(url)

        api = InstagramAPI("token", "0", transport=counting, min_interval=0)
        collect.run(self.names, api, self.out, log=lambda *_: None)
        self.assertEqual(calls, [])

    def test_expired_token_stops_and_keeps_partial_results(self):
        real = SampleTransport(config.SAMPLE_PROFILES)
        count = {"n": 0}

        def expiring(url, timeout=20.0):
            count["n"] += 1
            if count["n"] > 3:
                raise GraphError("Error validating access token", code=190, http_status=400)
            return real(url)

        api = InstagramAPI("token", "0", transport=expiring, min_interval=0)
        with self.assertRaises(collect.Stopped) as ctx:
            collect.run(self.names, api, self.out, log=lambda *_: None)
        self.assertIn("토큰", str(ctx.exception))
        self.assertEqual(len(read_rows(self.out)), 3)

    def test_rate_limit_waits_then_continues(self):
        real = SampleTransport(config.SAMPLE_PROFILES)
        state = {"failed": False}
        waits = []

        def limited(url, timeout=20.0):
            if not state["failed"]:
                state["failed"] = True
                raise GraphError("Application request limit reached", code=4, http_status=400)
            return real(url)

        api = InstagramAPI("token", "0", transport=limited, min_interval=0, sleep=waits.append)
        summary = collect.run(self.names[:2], api, self.out, log=lambda *_: None)
        self.assertEqual(waits, [60])
        self.assertEqual(summary["조회됨"], 2)

    def test_token_never_written_to_results(self):
        api = InstagramAPI("SECRET-TOKEN-VALUE", "0", transport=SampleTransport(config.SAMPLE_PROFILES), min_interval=0)
        collect.run(self.names, api, self.out, log=lambda *_: None)
        self.assertNotIn("SECRET-TOKEN-VALUE", self.out.read_text(encoding="utf-8-sig"))


class RequestShape(unittest.TestCase):
    def test_business_discovery_url(self):
        seen = []

        def capture(url, timeout=20.0):
            seen.append(url)
            return {"business_discovery": {"username": "abc"}, "id": "1"}

        api = InstagramAPI("tok", "17841400000000000", version="v27.0", transport=capture, min_interval=0)
        api.business_discovery("abc.def_1")
        self.assertTrue(seen[0].startswith("https://graph.facebook.com/v27.0/17841400000000000?"))
        self.assertIn("business_discovery.username%28abc.def_1%29", seen[0])
        self.assertIn("biography", seen[0])

    def test_rejects_malformed_username(self):
        api = sample_api()
        with self.assertRaises(ValueError):
            api.business_discovery("abc){media}")


class DmQueue(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        base = Path(self.dir.name)
        self.results = base / "emails.csv"
        self.log = base / "contact_log.csv"
        self.html = base / "dm_queue.html"
        self.template = config.ROOT / "templates" / "dm_template.txt"
        names, _ = collect.read_usernames(config.SAMPLE_ACCOUNTS)
        collect.run(names, sample_api(), self.results, log=lambda *_: None)

    def tearDown(self):
        self.dir.cleanup()

    def page_items(self):
        text = self.html.read_text(encoding="utf-8")
        return json.loads(re.search(r"const DATA = (\{.*?\});\n", text, re.S).group(1))["items"]

    def test_queue_has_only_accounts_without_email_sorted_by_followers(self):
        summary = dm_queue.build(self.results, self.template, self.log, self.html, limit=20)
        self.assertEqual(summary["오늘 보낼 대상"], 4)
        self.assertEqual(
            [it["u"] for it in self.page_items()],
            ["sample_big_creator", "sample_cocktail_lab", "sample_brunch_seoul", "sample_wine_and_rice"],
        )

    def test_message_is_filled_in(self):
        dm_queue.build(self.results, self.template, self.log, self.html)
        msg = self.page_items()[0]["msg"]
        self.assertIn("@sample_big_creator", msg)
        self.assertNotIn("{계정}", msg)

    def test_daily_limit(self):
        summary = dm_queue.build(self.results, self.template, self.log, self.html, limit=3)
        self.assertEqual((summary["오늘 보낼 대상"], summary["다음으로 미룬 계정"]), (3, 1))

    def test_contacted_accounts_are_excluded_after_import(self):
        sent = Path(self.dir.name) / "sent.csv"
        sent.write_text("﻿계정,채널,연락일\r\nsample_big_creator,DM,2026-11-18\r\n", encoding="utf-8")
        self.assertEqual(dm_queue.import_sent(sent, self.log), 1)
        self.assertEqual(dm_queue.import_sent(sent, self.log), 0)  # 두 번 넣어도 중복되지 않는다
        summary = dm_queue.build(self.results, self.template, self.log, self.html)
        self.assertEqual(summary["이미 연락해서 뺀 계정"], 1)
        self.assertNotIn("sample_big_creator", [it["u"] for it in self.page_items()])

    def test_bio_cannot_inject_page_code(self):
        rows = collect.load_results(self.results)
        rows["sample_big_creator"]["소개글"] = "</script><script>alert(1)</script>"
        collect.write_csv(self.results, collect.COLUMNS, list(rows.values()))
        dm_queue.build(self.results, self.template, self.log, self.html)
        text = self.html.read_text(encoding="utf-8")
        self.assertEqual(text.count("</script>"), 1)
        self.assertNotIn("<script>alert", text)


if __name__ == "__main__":
    unittest.main()
