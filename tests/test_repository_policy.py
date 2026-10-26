"""Exercise publication checks against isolated indexes, including staged secrets."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CHECKER = Path(__file__).resolve().parents[1] / 'scripts' / 'check_repository.py'


class RepositoryPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q')

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, check=True,
                              capture_output=True)

    def stage(self, name, content):
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        self.git('add', '--', name)
        return target

    def check(self):
        return subprocess.run([sys.executable, str(CHECKER), '--staged-only'],
                              cwd=self.root, capture_output=True, text=True)

    def test_shared_source_and_codeowners_are_allowed(self):
        self.stage('controller/example.py', b'print(1)\n')
        self.stage('.github/CODEOWNERS', b'* @maintainer\n')
        self.assertEqual(self.check().returncode, 0)

    def test_force_added_data_is_blocked(self):
        self.stage('output/private.txt', b'local data\n')
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('outside publication policy', result.stderr)

    def test_staged_secret_is_detected_even_when_worktree_is_clean(self):
        secret = b'gh' + b'p_' + b'X' * 36
        target = self.stage('controller/example.py', b'token = "' + secret + b'"\n')
        target.write_bytes(b'print(1)\n')
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('possible GitHub token', result.stderr)
        self.assertNotIn(secret.decode(), result.stdout + result.stderr)

    def test_unstaged_secret_is_not_misreported_as_published(self):
        target = self.stage('controller/example.py', b'print(1)\n')
        target.write_bytes(b'gh' + b'p_' + b'X' * 36)
        self.assertEqual(self.check().returncode, 0)

    def test_binary_masquerading_as_source_is_blocked(self):
        self.stage('controller/example.py', b'print(1)\0\n')
        self.assertNotEqual(self.check().returncode, 0)

    def test_oversized_source_is_blocked(self):
        self.stage('controller/example.py', b'#' * (1024 * 1024 + 1))
        self.assertNotEqual(self.check().returncode, 0)
