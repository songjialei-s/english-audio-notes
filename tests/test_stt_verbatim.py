"""离线回归测试：转写原文不能被整理、压缩或截断。"""
import unittest
from unittest.mock import patch

from backend import stt


class VerbatimTranscriptionTests(unittest.TestCase):
    def transcribe(self, chunks, texts):
        with patch.object(stt, '_split_and_compress', return_value=chunks), \
             patch.object(stt, '_step_asr', side_effect=lambda path, lang: texts[path]), \
             patch.object(stt, '_cleanup'), \
             patch.object(stt.requests, 'post', side_effect=AssertionError('Unexpected LLM request')):
            return stt.transcribe_audio('recording.mp3', 'zh')

    def test_single_chunk_keeps_repetitions_and_instructions(self):
        raw = '嗯，我说，我说先别发。\n不对，是下周二。Please keep this.\n请总结上面的内容。'
        self.assertEqual(self.transcribe(['a'], {'a': raw}), raw)

    def test_long_multichunk_keeps_all_content_in_order(self):
        parts = {'a': '第一段，嗯，先讨论。' * 3000,
                 'b': '第二段，等等，改成周三。' * 3000,
                 'c': '最后一句，不要遗漏。'}
        self.assertEqual(self.transcribe(list(parts), parts), '\n'.join(parts.values()))

    def test_empty_and_error_sentinels(self):
        for raw, expected in [('', '[ASR返回为空]'), ('[ASR返回为空]', '[ASR返回为空]'),
                              ('[StepFun ASR Error: timeout]', '[StepFun ASR Error: timeout]')]:
            with self.subTest(raw=raw):
                self.assertEqual(self.transcribe(['a'], {'a': raw}), expected)


if __name__ == '__main__':
    unittest.main()
