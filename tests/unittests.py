import os
import shutil
from unittest import TestCase
from decoupy.main import main, module_meta, find_common_base_path
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
MAIN = '__main__'

PACKAGE_A_PATHNAME = ''
PACKAGE_B_PATHNAME = ''
PACKAGE_C_PATHNAME = ''

PACKAGE_A_MODULE_INIT_PATHNAME = ''
PACKAGE_A_MODULE_A_PATHNAME = ''
PACKAGE_A_MODULE_B_PATHNAME = ''
PACKAGE_B_MODULE_INIT_PATHNAME = ''
PACKAGE_B_MODULE_A_PATHNAME = ''
PACKAGE_B_MODULE_B_PATHNAME = ''


class UnitTests(TestCase):

    def setUp(self):
        global ROOT_PACKAGE
        ROOT_PACKAGE = os.path.join(gettempdir(), ROOT)

    def tearDown(self):
        shutil.rmtree(ROOT_PACKAGE, ignore_errors=True)

    def test_common_path_founder(self):
        path1 = os.path.join(ROOT_PACKAGE, "common_folder1", "common_folder2", "uncommon_folder1", "dummy")
        path2 = os.path.join(ROOT_PACKAGE, "common_folder1", "common_folder2", "uncommon_folder2", "dummy")
        common_path = find_common_base_path(path1, path2)
        self.assertEqual(common_path, os.path.join(ROOT_PACKAGE, "common_folder1", "common_folder2"))



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
            PACKAGE_B_MODULE_B_PATHNAME, PACKAGE_A_MODULE_B_PATHNAME, PACKAGE_A_MODULE_INIT_PATHNAME,\
            PACKAGE_B_MODULE_INIT_PATHNAME
        PACKAGE_A_MODULE_INIT_PATHNAME = os.path.join(PACKAGE_A_PATHNAME, INIT_FILE)
        PACKAGE_A_MODULE_A_PATHNAME = os.path.join(PACKAGE_A_PATHNAME, MODULE_A)
        PACKAGE_A_MODULE_B_PATHNAME = os.path.join(PACKAGE_A_PATHNAME, MODULE_B)
        PACKAGE_B_MODULE_INIT_PATHNAME = os.path.join(PACKAGE_B_PATHNAME, INIT_FILE)
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

        result = main(PACKAGE_A_PATHNAME, PACKAGE_B_PATHNAME)

        etalon = {
            module_meta(MAIN, PACKAGE_A_MODULE_A_PATHNAME): set(
                [module_meta('.'.join([ROOT, PACKAGE_B]), PACKAGE_B_MODULE_INIT_PATHNAME),
                 module_meta('.'.join([ROOT, PACKAGE_B, "module_a"]), PACKAGE_B_MODULE_A_PATHNAME)]
            ),
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

        result = main(PACKAGE_A_PATHNAME, PACKAGE_B_PATHNAME)

        etalon = {
            module_meta(MAIN, PACKAGE_A_MODULE_A_PATHNAME):
                set(
                    [module_meta('.'.join([ROOT, PACKAGE_B]), PACKAGE_B_MODULE_INIT_PATHNAME),
                     module_meta('.'.join([ROOT, PACKAGE_B, "module_a"]), PACKAGE_B_MODULE_A_PATHNAME)]
                ),
            module_meta(MAIN, PACKAGE_B_MODULE_B_PATHNAME):
                set(
                [module_meta('.'.join([ROOT, PACKAGE_A]), PACKAGE_A_MODULE_INIT_PATHNAME),
                 module_meta('.'.join([ROOT, PACKAGE_A, 'module_b']), PACKAGE_A_MODULE_B_PATHNAME)]
            )
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

        result = main(PACKAGE_A_PATHNAME, PACKAGE_B_PATHNAME)

        etalon = {
            module_meta(MAIN, PACKAGE_A_MODULE_A_PATHNAME):
                set(
                    [module_meta('.'.join([ROOT, PACKAGE_B]), PACKAGE_B_MODULE_INIT_PATHNAME),
                     module_meta('.'.join([ROOT, PACKAGE_B, "module_a"]), PACKAGE_B_MODULE_A_PATHNAME),
                     module_meta('.'.join([ROOT, PACKAGE_A]), PACKAGE_A_MODULE_INIT_PATHNAME),
                     module_meta('.'.join([ROOT, PACKAGE_A, 'module_b']), PACKAGE_A_MODULE_B_PATHNAME)]
                ),
            module_meta(MAIN, PACKAGE_B_MODULE_A_PATHNAME):
                set(
                [module_meta('.'.join([ROOT, PACKAGE_A]), PACKAGE_A_MODULE_INIT_PATHNAME),
                 module_meta('.'.join([ROOT, PACKAGE_A, 'module_b']), PACKAGE_A_MODULE_B_PATHNAME)]
            )
        }

        self.assertDictEqual(result, etalon)

    def test_dependency_from_init_module(self):
        build_package_tree(
            {
                ROOT_PACKAGE: {
                    INIT_FILE: '',
                    PACKAGE_A: {
                        INIT_FILE: """
                                    import os
                                    import sys
                                    from root_package.package_b import module_a

                                    def baz():
                                        print 'baz'

                                    if __name__ == '__main__':
                                        module_a.foo()
                        """,
                        MODULE_A: """
                                    import os
                                    import sys
                                    from root_package.package_c import module_a as c_module_a
                                    if __name__ == '__main__':
                                        c_module_a.foo()
                                        """
                    },
                    PACKAGE_B: {
                        INIT_FILE: 'import sys',
                        MODULE_A: """
                                    import socket
                                    def foo():
                                        print 'foo'
                                        """,
                        MODULE_B: """
                                    from root_package.package_a import baz
                                    if __name__ == '__main__':
                                        baz()

                        """
                    },
                    PACKAGE_C: {
                        INIT_FILE: '',
                        MODULE_A: """
                                    def foo():
                                        print 'foo'
                        """
                    }
                }
            }
        )

        result = main(PACKAGE_A_PATHNAME, PACKAGE_B_PATHNAME)


        etalon = {
            module_meta(MAIN, PACKAGE_A_MODULE_INIT_PATHNAME):
                set(
                    [module_meta('.'.join([ROOT, PACKAGE_B]), PACKAGE_B_MODULE_INIT_PATHNAME),
                     module_meta('.'.join([ROOT, PACKAGE_B, "module_a"]), PACKAGE_B_MODULE_A_PATHNAME)]
                ),
            module_meta(MAIN, PACKAGE_B_MODULE_B_PATHNAME):
                set(
                    [module_meta('.'.join([ROOT, PACKAGE_A]), PACKAGE_A_MODULE_INIT_PATHNAME),
                     module_meta('.'.join([ROOT, PACKAGE_B]), PACKAGE_B_MODULE_INIT_PATHNAME),
                     module_meta('.'.join([ROOT, PACKAGE_B, 'module_a']), PACKAGE_B_MODULE_A_PATHNAME)]
                )
        }

        self.assertDictEqual(result, etalon)

    def test_import_inside_function(self):
        build_package_tree(
            {
                ROOT_PACKAGE: {
                    INIT_FILE: '',
                    PACKAGE_A: {
                        INIT_FILE: """
                                    import os
                                    import sys

                                    def baz():
                                        from root_package.package_b import module_a
                                        print 'baz'

                                    if __name__ == '__main__':
                                        module_a.foo()
                        """,
                        MODULE_A: """
                                    import os
                                    import sys
                                  """
                    },
                    PACKAGE_B: {
                        INIT_FILE: 'import sys',
                        MODULE_A: """
                                    import socket
                                    def foo():
                                        print 'foo'
                                        """,
                        MODULE_B: """
                                    from root_package.package_a import baz
                                    if __name__ == '__main__':
                                        baz()

                        """
                    },
                }
            }
        )

        result = main(PACKAGE_A_PATHNAME, PACKAGE_B_PATHNAME)


        etalon = {
            module_meta(MAIN, PACKAGE_A_MODULE_INIT_PATHNAME):
                set(
                    [module_meta('.'.join([ROOT, PACKAGE_B]), PACKAGE_B_MODULE_INIT_PATHNAME),
                     module_meta('.'.join([ROOT, PACKAGE_B, "module_a"]), PACKAGE_B_MODULE_A_PATHNAME)]
                ),
            module_meta(MAIN, PACKAGE_B_MODULE_B_PATHNAME):
                set(
                    [module_meta('.'.join([ROOT, PACKAGE_A]), PACKAGE_A_MODULE_INIT_PATHNAME),
                     module_meta('.'.join([ROOT, PACKAGE_B]), PACKAGE_B_MODULE_INIT_PATHNAME),
                     module_meta('.'.join([ROOT, PACKAGE_B, 'module_a']), PACKAGE_B_MODULE_A_PATHNAME)]
                )
        }

        self.assertDictEqual(result, etalon)

    def test_dependency_of_sub_package(self):
        build_package_tree(
            {
                ROOT_PACKAGE: {
                    INIT_FILE: '',
                    PACKAGE_A: {
                        INIT_FILE: '',
                        MODULE_A: """
                                    import os
                                    import sys
                                    from root_package.package_a.package_b import module_a
                                    def bar():
                                        print 'bar'
                                    if __name__ == '__main__':
                                        module_a.foo()
                                  """,
                        MODULE_B: '',
                        PACKAGE_B: {
                            INIT_FILE: '',
                            MODULE_A: """
                                    import socket
                                    def foo():
                                        print 'foo'
                                    """,
                            MODULE_B: """
                                    from root_package.package_a import module_b
                            """
                        }
                    }
                }
            }
        )

        result = main(os.path.join(ROOT_PACKAGE, PACKAGE_A), os.path.join(ROOT_PACKAGE, PACKAGE_A, PACKAGE_B))

        etalon = {
            module_meta(MAIN, PACKAGE_A_MODULE_A_PATHNAME): set(
                [module_meta('.'.join([ROOT, PACKAGE_A]), os.path.join(ROOT_PACKAGE, PACKAGE_A, INIT_FILE)),
                 module_meta('.'.join([ROOT, PACKAGE_A, PACKAGE_B]), os.path.join(ROOT_PACKAGE, PACKAGE_A, PACKAGE_B, INIT_FILE)),
                 module_meta('.'.join([ROOT, PACKAGE_A, PACKAGE_B, "module_a"]), os.path.join(ROOT_PACKAGE, PACKAGE_A, PACKAGE_B, MODULE_A))]
            ),
            module_meta(MAIN, os.path.join(ROOT_PACKAGE, PACKAGE_A, PACKAGE_B, MODULE_B)): set(
                [module_meta('.'.join([ROOT, PACKAGE_A]), os.path.join(ROOT_PACKAGE, PACKAGE_A, INIT_FILE)),
                 module_meta('.'.join([ROOT, PACKAGE_A, "module_b"]),
                             os.path.join(ROOT_PACKAGE, PACKAGE_A, MODULE_B))]

            )
        }

        self.assertDictEqual(result, etalon)
