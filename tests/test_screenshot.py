import pytest

try:
    from scripts.screenshot import images_are_same
    from PIL import Image
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

pytestmark = pytest.mark.skipif(not HAS_NUMPY, reason="numpy not available in this environment")


class TestImagesAreSame:
    def _make_image(self, color=(255, 0, 0), size=(10, 10)):
        return Image.new("RGB", size, color)

    def test_identical(self):
        img = self._make_image()
        assert images_are_same(img, img) is True

    def test_different(self):
        img1 = self._make_image(color=(255, 0, 0))
        img2 = self._make_image(color=(0, 0, 255))
        assert images_are_same(img1, img2) is False

    def test_none_first(self):
        assert images_are_same(None, self._make_image()) is False

    def test_none_second(self):
        assert images_are_same(self._make_image(), None) is False

    def test_both_none(self):
        assert images_are_same(None, None) is False

    def test_different_size(self):
        img1 = self._make_image(size=(10, 10))
        img2 = self._make_image(size=(20, 20))
        assert images_are_same(img1, img2) is False

    def test_nearly_same_above_threshold(self):
        img1 = self._make_image(size=(100, 100))
        img2 = img1.copy()
        img2.putpixel((0, 0), (0, 0, 0))
        assert images_are_same(img1, img2, threshold=0.99) is True

    def test_nearly_same_below_threshold(self):
        img1 = self._make_image(color=(255, 0, 0), size=(10, 10))
        img2 = self._make_image(color=(0, 0, 0), size=(10, 10))
        assert images_are_same(img1, img2, threshold=0.99) is False
