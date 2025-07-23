import os
import unittest
from unittest import mock

from argo_poem_tools.repos import YUMRepos

from test_poem import mock_data


class YUMReposTests(unittest.TestCase):
    def setUp(self):
        self.repos1 = YUMRepos(
            data=mock_data["data"],
            repos_path=os.getcwd()
        )
        self.repos2 = YUMRepos(
            data=mock_data["data"],
            repos_path=os.getcwd(),
            override=False
        )

    def tearDown(self):
        if os.path.exists('argo-devel.repo'):
            os.remove('argo-devel.repo')

        if os.path.exists('nordugrid-updates.repo'):
            os.remove('nordugrid-updates.repo')

    def test_create_file(self):
        files = self.repos1.create_file()
        self.assertEqual(
            files,
            [os.path.join(os.getcwd(), 'argo-devel.repo'),
             os.path.join(os.getcwd(), 'nordugrid-updates.repo')]
        )
        self.assertTrue(os.path.exists('argo-devel.repo'))
        self.assertTrue(os.path.exists('nordugrid-updates.repo'))

        with open('argo-devel.repo', 'r') as f:
            content1 = f.read()

        with open('nordugrid-updates.repo', 'r') as f:
            content2 = f.read()

        self.assertEqual(
            content1, mock_data['data']['argo-devel']['content']
        )
        self.assertEqual(
            content2, mock_data['data']['nordugrid-updates']['content']
        )

    @mock.patch('argo_poem_tools.repos.shutil.copyfile')
    @mock.patch('argo_poem_tools.repos.os.path.isfile')
    @mock.patch('argo_poem_tools.repos.os.makedirs')
    def test_do_override_file_which_already_exists(
            self, mock_mkdir, mock_isfile, mock_cp
    ):
        with open('argo-devel.repo', 'w') as f:
            f.write('test')

        files = self.repos1.create_file()
        self.assertFalse(mock_mkdir.called)
        self.assertFalse(mock_isfile.called)
        self.assertFalse(mock_cp.called)
        self.assertEqual(
            files,
            [os.path.join(os.getcwd(), 'argo-devel.repo'),
             os.path.join(os.getcwd(), 'nordugrid-updates.repo')]
        )
        self.assertTrue(os.path.exists('argo-devel.repo'))
        self.assertTrue(os.path.exists('nordugrid-updates.repo'))

        with open('argo-devel.repo', 'r') as f:
            content1 = f.read()

        with open('nordugrid-updates.repo', 'r') as f:
            content2 = f.read()

        self.assertEqual(
            content1, mock_data['data']['argo-devel']['content']
        )
        self.assertEqual(
            content2, mock_data['data']['nordugrid-updates']['content']
        )

    @mock.patch('argo_poem_tools.repos.shutil.copyfile')
    @mock.patch('argo_poem_tools.repos.os.path.isfile')
    @mock.patch('argo_poem_tools.repos.os.makedirs')
    def test_do_not_override_file_which_already_exists(
            self, mock_mkdir, mock_isfile, mock_copy
    ):
        mock_isfile.return_value = True
        with open('argo-devel.repo', 'w') as f:
            f.write('test')

        files = self.repos2.create_file()
        self.assertEqual(mock_mkdir.call_count, 2)
        mock_mkdir.assert_called_with('/tmp' + os.getcwd(), exist_ok=True)
        file1 = os.path.join(os.getcwd(), 'argo-devel.repo')
        file2 = os.path.join(os.getcwd(), 'nordugrid-updates.repo')
        self.assertEqual(mock_isfile.call_count, 2)
        mock_isfile.assert_has_calls(
            [mock.call(file1), mock.call(file2)], any_order=True
        )
        self.assertEqual(mock_copy.call_count, 2)
        mock_copy.assert_has_calls([
            mock.call(file1, '/tmp' + file1),
            mock.call(file2, '/tmp' + file2)
        ], any_order=True)
        self.assertEqual(files, [file1, file2])
        self.assertTrue(os.path.exists('argo-devel.repo'))
        self.assertTrue(os.path.exists('nordugrid-updates.repo'))

        with open('argo-devel.repo', 'r') as f:
            content1 = f.read()

        with open('nordugrid-updates.repo', 'r') as f:
            content2 = f.read()

        self.assertEqual(
            content1, mock_data['data']['argo-devel']['content']
        )
        self.assertEqual(
            content2, mock_data['data']['nordugrid-updates']['content']
        )

    @mock.patch('argo_poem_tools.repos.subprocess.call')
    @mock.patch('argo_poem_tools.repos.shutil.rmtree')
    @mock.patch('argo_poem_tools.repos.shutil.copy')
    @mock.patch('argo_poem_tools.repos.os.path.isfile')
    @mock.patch('argo_poem_tools.repos.os.listdir')
    @mock.patch('argo_poem_tools.repos.os.path.isdir')
    def test_clean(
            self, mock_isdir, mock_ls, mock_isfile, mock_cp, mock_rm, mock_call
    ):
        mock_isdir.return_value = True
        mock_ls.return_value = [
            'argo-devel.repo', 'nordugrid-updates.repo'
        ]
        mock_isfile.return_value = True
        file1 = os.path.join(os.getcwd(), 'argo-devel.repo')
        file2 = os.path.join(os.getcwd(), 'nordugrid-updates.repo')
        self.repos2.clean()
        self.assertEqual(mock_isdir.call_count, 1)
        mock_isdir.assert_called_with('/tmp' + os.getcwd())
        self.assertEqual(mock_ls.call_count, 1)
        mock_ls.assert_called_with('/tmp' + os.getcwd())
        self.assertEqual(mock_isfile.call_count, 2)
        mock_isfile.assert_has_calls([
            mock.call('/tmp' + file1),
            mock.call('/tmp' + file2)
        ], any_order=True)
        self.assertEqual(mock_cp.call_count, 2)
        mock_cp.assert_has_calls([
            mock.call('/tmp' + file1, os.getcwd()),
            mock.call('/tmp' + file2, os.getcwd())
        ], any_order=True)
        self.assertEqual(mock_rm.call_count, 1)
        mock_rm.assert_called_with('/tmp' + os.getcwd())
        self.assertEqual(mock_call.call_count, 1)
        mock_call.assert_called_with(['yum', 'clean', 'all'])

    @mock.patch('argo_poem_tools.repos.subprocess.call')
    @mock.patch('argo_poem_tools.repos.shutil.copy')
    @mock.patch('argo_poem_tools.repos.shutil.rmtree')
    def test_clean_if_override(self, mock_rmdir, mock_copy, mock_call):
        self.repos1.clean()
        self.assertEqual(mock_rmdir.call_count, 0)
        self.assertEqual(mock_copy.call_count, 0)
        self.assertEqual(mock_call.call_count, 1)
        mock_call.assert_called_with(['yum', 'clean', 'all'])
