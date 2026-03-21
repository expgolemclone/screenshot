import pytest

from scripts.upload import human_bytes, parse_selection, remote_join


class TestHumanBytes:
    def test_bytes(self):
        assert human_bytes(0) == "0B"
        assert human_bytes(512) == "512B"

    def test_kilobytes(self):
        assert human_bytes(1024) == "1.0KB"
        assert human_bytes(1536) == "1.5KB"

    def test_megabytes(self):
        assert human_bytes(1024 * 1024) == "1.0MB"

    def test_gigabytes(self):
        assert human_bytes(1024 ** 3) == "1.0GB"

    def test_terabytes(self):
        assert human_bytes(1024 ** 4) == "1.0TB"


class TestParseSelection:
    def test_single(self):
        assert parse_selection("1", 5) == [1]

    def test_multiple_comma(self):
        assert parse_selection("1,3", 5) == [1, 3]

    def test_range(self):
        assert parse_selection("2-4", 5) == [2, 3, 4]

    def test_reversed_range(self):
        assert parse_selection("4-2", 5) == [2, 3, 4]

    def test_mixed(self):
        assert parse_selection("1, 3-5", 5) == [1, 3, 4, 5]

    def test_quit(self):
        assert parse_selection("q", 5) == []
        assert parse_selection("quit", 5) == []
        assert parse_selection("exit", 5) == []

    def test_out_of_range(self):
        with pytest.raises(ValueError, match="範囲外"):
            parse_selection("6", 5)

    def test_invalid_input(self):
        with pytest.raises(ValueError, match="無効な入力"):
            parse_selection("abc", 5)

    def test_dedup(self):
        assert parse_selection("1,1,2", 5) == [1, 2]


class TestRemoteJoin:
    def test_with_dest(self):
        assert remote_join("/book", "test") == "/book/test"

    def test_root_dest(self):
        assert remote_join("/", "test") == "/test"

    def test_trailing_slash(self):
        assert remote_join("/book/", "test") == "/book/test"

    def test_empty_dest(self):
        assert remote_join("", "test") == "test"

    def test_whitespace_dest(self):
        assert remote_join("  ", "test") == "test"
