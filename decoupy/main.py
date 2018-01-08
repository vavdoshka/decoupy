import sys
import os
from setuptools import findall
from modulefinder import ModuleFinder
from collections import defaultdict


def main(a_pathname, b_pathname):
    modules_a = findall(a_pathname)
    modules_b = findall(b_pathname)
    sys_path = [os.path.dirname(os.path.dirname(os.path.commonprefix([a_pathname, b_pathname])))] + sys.path
    out = defaultdict(set)
    traverse_dependencies(modules_a, a_pathname, b_pathname, out, sys_path)
    traverse_dependencies(modules_b, a_pathname, b_pathname, out, sys_path)
    return out


def traverse_dependencies(modules_a, a_pathname, b_pathanme, out, sys_path):
    for module_pathname in modules_a:
        if module_pathname.endswith('__init__.py'):
            continue
        mf = ModuleFinder(sys_path)
        mf.run_script(module_pathname)
        for modname, mod in mf.modules.iteritems():
            if mod.__file__ is not None and (a_pathname in mod.__file__ or b_pathanme in mod.__file__):
                if module_pathname != mod.__file__ and not mod.__file__.endswith('__init__.py'):
                    out[module_pathname].add(mod.__file__)


if __name__ == '__main__':
    path = sys.argv[1]