import os
import shutil
from unittest import TestCase
from decoupy import main
from tempfile import gettempdir
import mock


def make_file(pathname, content):
    with open(pathname, 'w') as f:
        f.write(content)

def norm_indent(code):
    if code == '':
        return code
    for i, char in enumerate(code.lstrip('\n')):
        if char != ' ':
            ws_to_strip = i
            break
    return '\n'.join([line[ws_to_strip:] for line in code.split('\n')]).strip()

def build_package_tree(tree, current_dir=''):
    for k, v in tree.iteritems():
        if isinstance(v, dict):
            cur_dir = os.path.join(current_dir, k)
            os.makedirs(cur_dir)
            build_package_tree(v, current_dir=cur_dir)
        elif isinstance(v, basestring):
            make_file(os.path.join(current_dir, k), norm_indent(v))


class TestTools(TestCase):

    def test_code_indentation_fix(self):
        code = """
                import os
                import sys
                from root_package.package_b import module_a
                def bar():
                    print 'ba
                if __name__ == '__main__':
                    if module_a.foo():
                        print 'ok'
        """
        formatted_code = norm_indent(code)

        etalon = """
import os
import sys
from root_package.package_b import module_a
def bar():
    print 'ba
if __name__ == '__main__':
    if module_a.foo():
        print 'ok'""".strip()

        self.assertMultiLineEqual(formatted_code, etalon)

    def test_package_tree_builder(self):
        tree = {
            "root": {
                'inner1': {
                    'file1': 'file_content'
                },
                'inner2': {
                    'file2': ''
                }

            }
        }
        with mock.patch('os.makedirs') as makedirs_stub,\
            mock.patch('unittests.make_file') as make_file_stub:
            build_package_tree(tree)
        makedirs_stub.assert_has_calls([mock.call("root"),
                                        mock.call('root/inner1'),
                                        mock.call('root/inner2')],
                                       any_order=True)
        make_file_stub.assert_has_calls([mock.call('root/inner1/file1', 'file_content'),
                                         mock.call('root/inner2/file2', '')],
                                        any_order=True)


ROOT = 'root_package'

ROOT_PACKAGE = ''
PACKAGE_A = 'package_a'
PACKAGE_B = 'package_b'
PACKAGE_C = 'package_c'
MODULE_A = 'module_a.py'
MODULE_B = 'module_b.py'
INIT_FILE = '__init__.py'

PACKAGE_A_PATHNAME = ''
PACKAGE_B_PATHNAME = ''
PACKAGE_C_PATHNAME = ''

PACKAGE_A_MODULE_A_PATHNAME = ''
PACKAGE_A_MODULE_B_PATHNAME = ''
PACKAGE_B_MODULE_A_PATHNAME = ''
PACKAGE_B_MODULE_B_PATHNAME = ''

class AcceptanceTests(TestCase):

    maxDiff = None

    def setUp(self):
        global ROOT_PACKAGE
        ROOT_PACKAGE = os.path.join(gettempdir(), ROOT)

        global PACKAGE_A_PATHNAME, PACKAGE_B_PATHNAME, PACKAGE_C_PATHNAME
        PACKAGE_A_PATHNAME = os.path.join(ROOT_PACKAGE, PACKAGE_A)
        PACKAGE_B_PATHNAME = os.path.join(ROOT_PACKAGE, PACKAGE_B)
        PACKAGE_C_PATHNAME = os.path.join(ROOT_PACKAGE, PACKAGE_C)

        global PACKAGE_A_MODULE_A_PATHNAME, PACKAGE_B_MODULE_A_PATHNAME,\
            PACKAGE_B_MODULE_B_PATHNAME, PACKAGE_A_MODULE_B_PATHNAME
        PACKAGE_A_MODULE_A_PATHNAME = os.path.join(PACKAGE_A_PATHNAME, MODULE_A)
        PACKAGE_A_MODULE_B_PATHNAME = os.path.join(PACKAGE_A_PATHNAME, MODULE_B)
        PACKAGE_B_MODULE_A_PATHNAME = os.path.join(PACKAGE_B_PATHNAME, MODULE_A)
        PACKAGE_B_MODULE_B_PATHNAME = os.path.join(PACKAGE_B_PATHNAME, MODULE_B)


    def tearDown(self):
        shutil.rmtree(ROOT_PACKAGE)

    def test_single_dependency(self):
        build_package_tree(
            {
                ROOT_PACKAGE: {
                    INIT_FILE: '',
                    PACKAGE_A: {
                        INIT_FILE: '',
                        MODULE_A: """
                                    import os
                                    import sys
                                    from root_package.package_b import module_a
                                    def bar():
                                        print 'bar'
                                    if __name__ == '__main__':
                                        module_a.foo()
                                  """
                    },
                    PACKAGE_B: {
                        INIT_FILE: '',
                        MODULE_A: """
                                    import socket
                                    def foo():
                                        print 'foo'
                                  """
                    }
                }
            }
        )

        result = main.main(PACKAGE_A_PATHNAME, PACKAGE_B_PATHNAME)

        etalon = {
            PACKAGE_A_MODULE_A_PATHNAME: set([PACKAGE_B_MODULE_A_PATHNAME])
        }
        self.assertDictEqual(result, etalon)

    def test_two_dependencies_and_custom_modules_straight(self):
        build_package_tree(
            {
                ROOT_PACKAGE: {
                    INIT_FILE: '',
                    PACKAGE_A: {
                        INIT_FILE: '',
                        MODULE_A: """
                                    import os
                                    import sys
                                    from root_package.package_b import module_a
                                    from root_package.package_c import module_a as c_module_a
                                    def bar():
                                        print 'bar'
                                    if __name__ == '__main__':
                                        module_a.foo()
                                        """,
                        MODULE_B: """
                                    import shutil
                                    def baz():
                                        print 'baz'
                                        """
                    },
                    PACKAGE_B: {
                        INIT_FILE: '',
                        MODULE_A: """
                                    import socket
                                    from root_package.package_c import module_a

                                    def foo():
                                        print 'foo'
                                        """,
                        MODULE_B: """
                                    from root_package.package_a import module_b
                                    import shutil
                                    def baz():
                                        print 'baz'
                                        """
                    },
                    PACKAGE_C: {
                        INIT_FILE: '',
                        MODULE_A: ''
                    }
                }
            }
        )

        result = main.main(PACKAGE_A_PATHNAME, PACKAGE_B_PATHNAME)

        etalon = {
            PACKAGE_A_MODULE_A_PATHNAME: set([PACKAGE_B_MODULE_A_PATHNAME]),
                  PACKAGE_B_MODULE_B_PATHNAME: set([PACKAGE_A_MODULE_B_PATHNAME])
        }
        self.assertDictEqual(result, etalon)

    def test_two_dependencies_and_custom_modules_transitive(self):
        build_package_tree(
            {
                ROOT_PACKAGE: {
                    INIT_FILE: '',
                    PACKAGE_A: {
                        INIT_FILE: '',
                        MODULE_A: """
                                    import os
                                    import sys
                                    from root_package.package_b import module_a
                                    from root_package.package_c import module_a as c_module_a
                                    def bar():
                                        print 'bar'
                                    if __name__ == '__main__':
                                        module_a.foo()
                                        """,
                        MODULE_B: """
                                    import shutil
                                    def baz():
                                        print 'baz'
                                        """
                    },
                    PACKAGE_B: {
                        INIT_FILE: '',
                        MODULE_A: """
                                    import socket
                                    from root_package.package_a import module_b

                                    def foo():
                                        print 'foo'
                                        """
                    },
                    PACKAGE_C: {
                        INIT_FILE: '',
                        MODULE_A: ''
                    }
                }
            }
        )

        result = main.main(PACKAGE_A_PATHNAME, PACKAGE_B_PATHNAME)

        etalon = {
            PACKAGE_A_MODULE_A_PATHNAME: set([PACKAGE_B_MODULE_A_PATHNAME, PACKAGE_A_MODULE_B_PATHNAME]),
        PACKAGE_B_MODULE_A_PATHNAME: set([PACKAGE_A_MODULE_B_PATHNAME])
        }
        self.assertDictEqual(result, etalon)
