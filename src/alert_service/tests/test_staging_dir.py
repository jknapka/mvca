'''
Test the staging directory code.
'''
import os
import shutil
import logging
from pathlib import Path
from nose.tools import ok_, eq_

from ..service import scanDir

TEST_DIR='_alert_svc_staging'

class TestStagingDir:

    def setUp(self):
        try:
            shutil.rmtree(TEST_DIR)
        except:
            pass
        try:
            os.mkdir(TEST_DIR)
        except:
            pass

    def tearDown(self):
        try:
            shutil.rmtree(TEST_DIR)
        except:
            logging.getLogger('unter.alert_svc.test').error('Couls not delete {}'.\
                    format(TEST_DIR))

    def test_0_testDirExists(self):
        ''' The test staging directory exists (setUp() succeeded). '''
        p = Path(TEST_DIR)
        p.resolve(strict=False)
        ok_(p.exists(),'{} does not exist.'.format(str(p)))
        ok_(p.is_dir(),'{} is not a directory.'.format(str(p)))


    def test_1_scanEmptyDir(self):
        result = scanDir(TEST_DIR)
        ok_([] == result,'Found files in allegedly empty directory: {}'.format(result))

    def test_2_scanOneFile(self):
        p = Path(TEST_DIR,'1.json')
        p.touch()
        result = scanDir(TEST_DIR)
        expected = ['{}/1.json'.format(TEST_DIR)]
        eq_(expected,result,'Expected {}, found {}'.format(expected,result))

    def test_3_scan3Files(self):
        p = Path(TEST_DIR,'1.json')
        p.touch()
        p = Path(TEST_DIR,'2.json')
        p.touch()
        p = Path(TEST_DIR,'3.json')
        p.touch()
        result = scanDir(TEST_DIR)
        expected = []
        for x in (1,2,3):
            expected.append('{}/{}.json'.format(TEST_DIR,x))
        eq_(expected,result,'Expected {}, found {}'.format(expected,result))


