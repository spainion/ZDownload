import unittest
from zdownloadmanager.core.organizer import Organizer


class OrganizerTests(unittest.TestCase):
    def test_normalize_filename(self) -> None:
        org = Organizer()
        self.assertEqual(org.normalize_filename("my-file_1.2.zip"), "my file v1.2.zip")


if __name__ == "__main__":
    unittest.main()
