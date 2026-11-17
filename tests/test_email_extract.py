import unittest

from seeding.email_extract import extract_emails, is_link_hub, prefers_dm

# 실제로 존재할 수 없는 주소를 쓴다. (gmail·naver 아이디 길이 제한보다 길다)
LONG = "fictional.sample.address.used.only.in.tests"


def emails(text):
    return [f.email for f in extract_emails(text)]


class StandardForm(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(emails("협업 문의 hello@example.com"), ["hello@example.com"])

    def test_korean_text_right_after(self):
        self.assertEqual(emails("메일은 hello@example.co.kr입니다"), ["hello@example.co.kr"])

    def test_korean_text_right_before(self):
        self.assertEqual(emails("문의hello@example.com"), ["hello@example.com"])

    def test_uppercase_is_lowered(self):
        self.assertEqual(emails("HELLO@EXAMPLE.COM"), ["hello@example.com"])

    def test_latin_text_glued_after_tld(self):
        self.assertEqual(emails("hello@example.comDM주세요"), ["hello@example.com"])

    def test_two_addresses_keep_order(self):
        self.assertEqual(emails("ad@example.com / hi@example.com"), ["ad@example.com", "hi@example.com"])

    def test_duplicates_removed(self):
        self.assertEqual(emails("a@example.com A@example.com"), ["a@example.com"])

    def test_fullwidth_at_sign(self):
        self.assertEqual(emails("hello＠example.com"), ["hello@example.com"])

    def test_standard_form_is_marked_sure(self):
        found = extract_emails("hello@example.com")[0]
        self.assertEqual((found.how, found.sure), ("표준", True))

    def test_unusual_ending_needs_review(self):
        self.assertFalse(extract_emails("hello@example.zzzz")[0].sure)


class ObfuscatedForm(unittest.TestCase):
    def test_korean_at_and_dot_words(self):
        self.assertEqual(emails("biz: hello 골뱅이 example 닷컴"), ["hello@example.com"])

    def test_bracketed_at_dot(self):
        self.assertEqual(emails("hello (at) example (dot) com"), ["hello@example.com"])
        self.assertEqual(emails("hello[at]example[dot]com"), ["hello@example.com"])

    def test_spaces_around_at_and_dot(self):
        self.assertEqual(emails("메일 hello @ example . com"), ["hello@example.com"])

    def test_space_after_at_only(self):
        self.assertEqual(emails("hello@ example.com"), ["hello@example.com"])

    def test_plain_at_word_before_mail_domain(self):
        self.assertEqual(emails(f"{LONG} at gmail.com"), [f"{LONG}@gmail.com"])

    def test_plain_dot_word(self):
        self.assertEqual(emails("hello (at) example dot com"), ["hello@example.com"])

    def test_space_before_at_with_mail_domain(self):
        self.assertEqual(emails(f"{LONG} @naver.com"), [f"{LONG}@naver.com"])

    def test_obfuscated_form_needs_review(self):
        found = extract_emails("hello 골뱅이 example 닷컴")[0]
        self.assertEqual((found.how, found.sure), ("변형 표기", False))

    def test_standard_and_obfuscated_together(self):
        self.assertEqual(
            emails("a@example.com 또는 b 골뱅이 example 닷컴"),
            ["a@example.com", "b@example.com"],
        )


class NotAnEmail(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(emails(""), [])
        self.assertEqual(emails(None), [])

    def test_account_mention(self):
        self.assertEqual(emails("collab with @sample.brand.kr"), [])
        self.assertEqual(emails("문의는 DM @sample.official"), [])

    def test_english_sentence_with_at(self):
        self.assertEqual(emails("I work at example.com every day"), [])

    def test_image_file_name(self):
        self.assertEqual(emails("logo@2x.png"), [])

    def test_whelk_dish_is_not_an_at_sign(self):
        self.assertEqual(emails("을지로 골뱅이 맛집 탐방"), [])

    def test_domain_containing_dot_word_is_untouched(self):
        self.assertEqual(emails("hello@kidotcom.example.com"), ["hello@kidotcom.example.com"])


class Hints(unittest.TestCase):
    def test_prefers_dm(self):
        self.assertTrue(prefers_dm("협찬 문의는 DM 주세요"))
        self.assertTrue(prefers_dm("문의는 디엠으로"))
        self.assertFalse(prefers_dm("메일로 연락 주세요"))

    def test_link_hub(self):
        self.assertTrue(is_link_hub("https://linktr.ee/someone"))
        self.assertTrue(is_link_hub("link.inpock.co.kr/someone"))
        self.assertFalse(is_link_hub("https://blog.example.com"))
        self.assertFalse(is_link_hub(""))


if __name__ == "__main__":
    unittest.main()
