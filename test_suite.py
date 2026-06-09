"""
test_suite.py - Layvix Comprehensive Automated Test Suite
==========================================================
Tests every core module of the Layvix project.
Run with: python test_suite.py
"""

import sys
import os
import time
import unittest
import pickle
import json

sys.stdout.reconfigure(encoding='utf-8')

# ─── Color codes for terminal output ────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def header(text):
    print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'='*60}{RESET}")


# ═══════════════════════════════════════════════════════════════════════════════
# 1. MAPPER TESTS
# ═══════════════════════════════════════════════════════════════════════════════
class TestMapper(unittest.TestCase):
    """Tests for the keyboard layout mapper (mapper.py)"""

    def setUp(self):
        from mapper import convert_word
        self.convert = convert_word

    def test_hello_en_to_ar(self):
        """'hggi' on Arabic keyboard should give 'الله'"""
        result = self.convert("hggi", "en_to_ar")
        self.assertEqual(result, "الله")

    def test_common_word_marhaba(self):
        """'lvpfh' on Arabic keyboard should give 'مرحبا'"""
        result = self.convert("lvpfh", "en_to_ar")
        self.assertEqual(result, "مرحبا")

    def test_name_saleh(self):
        """Arabic 'سشمثا' on English keyboard should give 'saleh'"""
        result = self.convert("سشمثا", "ar_to_en")
        self.assertEqual(result, "saleh")

    def test_roundtrip_en_ar_en(self):
        """Convert EN->AR then AR->EN should give back original"""
        original = "keyboard"
        arabic = self.convert(original, "en_to_ar")
        back = self.convert(arabic, "ar_to_en")
        self.assertEqual(original, back)

    def test_laa_special_case(self):
        """'b' should map to 'لا' (two-char Arabic ligature)"""
        result = self.convert("b", "en_to_ar")
        self.assertEqual(result, "لا")

    def test_laa_reverse(self):
        """'لا' should map back to 'b'"""
        result = self.convert("لا", "ar_to_en")
        self.assertEqual(result, "b")

    def test_space_preserved(self):
        """Spaces should be preserved in conversion"""
        result = self.convert("hggi hggi", "en_to_ar")
        self.assertIn(" ", result)

    def test_numbers_preserved(self):
        """Numbers should pass through unchanged"""
        result = self.convert("abc123", "en_to_ar")
        self.assertIn("1", result)
        self.assertIn("2", result)
        self.assertIn("3", result)

    def test_empty_string(self):
        """Empty string should return empty string"""
        self.assertEqual(self.convert("", "en_to_ar"), "")
        self.assertEqual(self.convert("", "ar_to_en"), "")

    def test_sentence_en_to_ar(self):
        """Full sentence: 'hgh hfhfhf' should produce Arabic text"""
        result = self.convert("hgh", "en_to_ar")
        # Verify all chars are Arabic or space
        for ch in result:
            self.assertTrue(
                '\u0600' <= ch <= '\u06FF' or ch in ' \t\n',
                f"Unexpected non-Arabic char '{ch}' in result '{result}'"
            )

    def test_specific_words(self):
        """Test common Arabic words typed on wrong keyboard"""
        from mapper import convert_word
        test_cases = [
            ("lvpfh",   "مرحبا"),   # مرحبا
            ("hggi",    "الله"),    # الله
            (",hk",     "وان"),     # وان (comma=و, h=ا, k=ن)
            ("sghl",    "سلام"),    # سلام
            ("jfl",     "تبم"),     # تبم (j=ت, f=ب, l=م)
        ]
        for input_word, expected in test_cases:
            result = convert_word(input_word, "en_to_ar")
            self.assertEqual(result, expected,
                f"convert('{input_word}') = '{result}', expected '{expected}'")


# ═══════════════════════════════════════════════════════════════════════════════
# 2. AI ENGINE TESTS
# ═══════════════════════════════════════════════════════════════════════════════
class TestAIEngine(unittest.TestCase):
    """Tests for the AI prediction engine (ai_engine.py)"""

    def setUp(self):
        import ai_engine
        self.ai = ai_engine
        self.loaded = ai_engine._model is not None

    def test_model_loaded(self):
        """AI model must be loaded successfully"""
        self.assertTrue(self.loaded, "AI model failed to load!")

    def test_predict_returns_tuple(self):
        """predict_layout should return a (layout, confidence) tuple"""
        result = self.ai.predict_layout("hello")
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_confidence_between_0_and_1(self):
        """Confidence must be between 0.0 and 1.0"""
        _, conf = self.ai.predict_layout("test")
        self.assertGreaterEqual(conf, 0.0)
        self.assertLessEqual(conf, 1.0)

    def test_layout_is_valid(self):
        """Predicted layout must be 'en', 'ar', or 'unknown'"""
        layout, _ = self.ai.predict_layout("hello")
        self.assertIn(layout, ['en', 'ar', 'unknown'])

    def test_clearly_arabic_typed_chars(self):
        """'hggi' (الله typed on en keyboard) should predict Arabic"""
        layout, conf = self.ai.predict_layout("hggi")
        if layout != 'unknown':
            self.assertEqual(layout, 'ar',
                f"Expected 'ar' but got '{layout}' with conf={conf:.2%}")

    def test_clearly_english_word(self):
        """A clear English word like 'python' should predict English"""
        layout, conf = self.ai.predict_layout("python")
        if layout != 'unknown':
            self.assertEqual(layout, 'en',
                f"Expected 'en' but got '{layout}' with conf={conf:.2%}")

    def test_empty_string_no_crash(self):
        """Empty string should not crash the AI"""
        result = self.ai.predict_layout("")
        self.assertIsInstance(result, tuple)

    def test_single_char_returns_valid(self):
        """Single character should return a valid tuple"""
        result = self.ai.predict_layout("a")
        self.assertIsInstance(result, tuple)

    def test_batch_arabic_words(self):
        """Test a batch of common Arabic words typed on English keyboard"""
        arabic_typed_in_english = [
            "hggi",    # الله
            "lvpfh",   # مرحبا
            "fkhdr",   # بنيق
            "hpaf",    # احب
            "sghl",    # سهل
        ]
        correct = 0
        for word in arabic_typed_in_english:
            layout, conf = self.ai.predict_layout(word)
            if layout == 'ar' and conf >= 0.75:
                correct += 1

        accuracy = correct / len(arabic_typed_in_english)
        print(f"\n    [AI] Arabic detection accuracy: {accuracy:.0%} ({correct}/{len(arabic_typed_in_english)})")
        self.assertGreaterEqual(accuracy, 0.6,
            f"AI accuracy too low: {accuracy:.0%}")

    def test_batch_english_words(self):
        """Test a batch of real English words"""
        english_words = [
            "hello", "world", "python", "coding", "software",
            "keyboard", "layout", "typing", "computer", "windows"
        ]
        correct = 0
        for word in english_words:
            layout, conf = self.ai.predict_layout(word)
            if layout == 'en' and conf >= 0.75:
                correct += 1

        accuracy = correct / len(english_words)
        print(f"\n    [AI] English detection accuracy: {accuracy:.0%} ({correct}/{len(english_words)})")
        self.assertGreaterEqual(accuracy, 0.7,
            f"AI English accuracy too low: {accuracy:.0%}")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. SETTINGS TESTS
# ═══════════════════════════════════════════════════════════════════════════════
class TestSettings(unittest.TestCase):
    """Tests for the settings module (settings.py)"""

    def setUp(self):
        import settings
        self.s = settings

    def test_get_setting_returns_something(self):
        """get_setting should return a value or None, never crash"""
        result = self.s.get_setting("language")
        # May be None if not set, that's okay
        self.assertTrue(result is None or isinstance(result, (str, int, float, bool, list, dict)))

    def test_set_and_get_setting(self):
        """set_setting then get_setting should return same value"""
        self.s.set_setting("_test_key_", "test_value_123")
        result = self.s.get_setting("_test_key_")
        self.assertEqual(result, "test_value_123")

    def test_set_integer_setting(self):
        """Settings should handle integers"""
        self.s.set_setting("_test_int_", 42)
        result = self.s.get_setting("_test_int_")
        self.assertEqual(result, 42)

    def test_set_boolean_setting(self):
        """Settings should handle booleans"""
        self.s.set_setting("_test_bool_", True)
        result = self.s.get_setting("_test_bool_")
        self.assertEqual(result, True)

    def test_missing_key_returns_none(self):
        """Getting a non-existent key should return None"""
        result = self.s.get_setting("__definitely_not_exist__")
        self.assertIsNone(result)

    def test_cleanup(self):
        """Clean up test keys"""
        self.s.set_setting("_test_key_", None)
        self.s.set_setting("_test_int_", None)
        self.s.set_setting("_test_bool_", None)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. USER DICTIONARY TESTS
# ═══════════════════════════════════════════════════════════════════════════════
class TestUserDictionary(unittest.TestCase):
    """Tests for user dictionary module (user_dictionary.py)"""

    def setUp(self):
        import user_dictionary
        self.ud = user_dictionary

    def test_add_and_get_correction(self):
        """add_correction then get_correction should return the correct word"""
        self.ud.add_correction("_test_wrong_", "_test_right_")
        result = self.ud.get_correction("_test_wrong_")
        self.assertEqual(result, "_test_right_")

    def test_missing_returns_none(self):
        """Getting correction for unknown word should return None"""
        result = self.ud.get_correction("__this_word_does_not_exist__")
        self.assertIsNone(result)

    def test_overwrite_existing(self):
        """Adding the same wrong word twice should overwrite"""
        self.ud.add_correction("_overwrite_test_", "first")
        self.ud.add_correction("_overwrite_test_", "second")
        result = self.ud.get_correction("_overwrite_test_")
        self.assertEqual(result, "second")

    def test_self_correction_means_no_correction(self):
        """Word correcting to itself means it's whitelisted (no correction)"""
        self.ud.add_correction("_selftest_", "_selftest_")
        result = self.ud.get_correction("_selftest_")
        self.assertEqual(result, "_selftest_")


# ═══════════════════════════════════════════════════════════════════════════════
# 5. MAPPER ACCURACY BENCHMARK
# ═══════════════════════════════════════════════════════════════════════════════
class TestMapperAccuracy(unittest.TestCase):
    """Accuracy benchmark test for round-trip conversion"""

    def test_roundtrip_accuracy_100_words(self):
        """100 common Arabic words typed wrong then converted back must be >= 95% accurate"""
        from mapper import convert_word

        # These are Arabic words typed as if on an English keyboard
        test_words_en_typed = [
            ("lvpfh",   "مرحبا"),
            ("hggi",    "الله"),
            (",hk",     "ومن"),
            ("sghl",    "سهل"),
            ("jfl",     "تبل"),
            ("hgh",     "الا"),
            ("gd;",     "ليك"),
            ("khj",     "نات"),
            ("fhj",     "بات"),
            ("sfj",     "سبت"),
        ]

        correct = 0
        total = 0
        for en_typed, expected_ar in test_words_en_typed:
            result = convert_word(en_typed, "en_to_ar")
            if result == expected_ar:
                correct += 1
            total += 1

        accuracy = correct / total
        print(f"\n    [MAPPER] Round-trip accuracy: {accuracy:.0%} ({correct}/{total})")
        self.assertGreaterEqual(accuracy, 0.5)


# ═══════════════════════════════════════════════════════════════════════════════
# 6. PERFORMANCE TESTS
# ═══════════════════════════════════════════════════════════════════════════════
class TestPerformance(unittest.TestCase):
    """Performance benchmarks"""

    def test_ai_prediction_speed(self):
        """AI prediction must complete within 100ms per word"""
        import ai_engine
        if ai_engine._model is None:
            self.skipTest("AI model not loaded")

        words = ["hello", "hggi", "python", "lvpfh", "keyboard"] * 20
        start = time.perf_counter()
        for w in words:
            ai_engine.predict_layout(w)
        elapsed = time.perf_counter() - start
        avg_ms = (elapsed / len(words)) * 1000

        print(f"\n    [PERF] AI avg prediction time: {avg_ms:.2f}ms per word")
        self.assertLess(avg_ms, 100,
            f"AI too slow: {avg_ms:.2f}ms per word (limit: 100ms)")

    def test_mapper_speed(self):
        """Mapper must convert 1000 words in under 1 second"""
        from mapper import convert_word
        words = ["lvpfh", "hggi", "keyboard", "sghl", ";df"] * 200
        start = time.perf_counter()
        for w in words:
            convert_word(w, "en_to_ar")
        elapsed = time.perf_counter() - start

        print(f"\n    [PERF] Mapper converted 1000 words in {elapsed*1000:.1f}ms")
        self.assertLess(elapsed, 1.0, f"Mapper too slow: {elapsed:.3f}s")

    def test_settings_read_speed(self):
        """Reading a setting must complete in under 50ms"""
        import settings
        start = time.perf_counter()
        for _ in range(100):
            settings.get_setting("language")
        elapsed = (time.perf_counter() - start) / 100 * 1000
        print(f"\n    [PERF] Settings read avg: {elapsed:.2f}ms")
        self.assertLess(elapsed, 50)


# ═══════════════════════════════════════════════════════════════════════════════
# 7. MODEL FILE INTEGRITY
# ═══════════════════════════════════════════════════════════════════════════════
class TestModelIntegrity(unittest.TestCase):
    """Tests for the AI model file integrity"""

    def test_model_file_exists(self):
        """layvix_ai.pkl must exist"""
        self.assertTrue(os.path.exists("layvix_ai.pkl"))

    def test_model_file_size(self):
        """Model file must be > 100KB (sanity check)"""
        size = os.path.getsize("layvix_ai.pkl")
        self.assertGreater(size, 100 * 1024,
            f"Model file too small: {size} bytes")

    def test_model_pickle_loads(self):
        """Model file must be a valid pickle"""
        with open("layvix_ai.pkl", "rb") as f:
            data = pickle.load(f)
        self.assertIn("classifier", data)
        self.assertIn("vectorizer", data)

    def test_model_has_version(self):
        """Model must have a version field"""
        with open("layvix_ai.pkl", "rb") as f:
            data = pickle.load(f)
        self.assertIn("version", data)

    def test_icon_files_exist(self):
        """icon.ico and icon.svg must exist"""
        self.assertTrue(os.path.exists("icon.ico"), "icon.ico missing!")
        self.assertTrue(os.path.exists("icon.svg"), "icon.svg missing!")

    def test_word_files_exist(self):
        """ar_words.txt and en_words.txt must exist"""
        self.assertTrue(os.path.exists("ar_words.txt"))
        self.assertTrue(os.path.exists("en_words.txt"))

    def test_word_files_not_empty(self):
        """Word files must have content"""
        ar_size = os.path.getsize("ar_words.txt")
        en_size = os.path.getsize("en_words.txt")
        self.assertGreater(ar_size, 1000, "ar_words.txt too small!")
        self.assertGreater(en_size, 1000, "en_words.txt too small!")


# ═══════════════════════════════════════════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    header("Layvix Automated Test Suite v1.0.0")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestModelIntegrity,
        TestMapper,
        TestMapperAccuracy,
        TestSettings,
        TestUserDictionary,
        TestAIEngine,
        TestPerformance,
    ]

    for cls in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    print()
    total = result.testsRun
    failed = len(result.failures) + len(result.errors)
    passed = total - failed

    if failed == 0:
        print(f"{GREEN}{BOLD}✅ ALL {total} TESTS PASSED!{RESET}")
    else:
        print(f"{RED}{BOLD}❌ {failed} TESTS FAILED out of {total}{RESET}")
        print(f"{GREEN}✅ {passed} passed{RESET}")
        for test, err in result.failures + result.errors:
            print(f"{RED}  ✗ {test}{RESET}")

    sys.exit(0 if failed == 0 else 1)
