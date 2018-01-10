import sys
import os
from setuptools import findall
from modulefinder import ModuleFinder
from collections import namedtuple

module_meta = namedtuple('module', 'package pathname'.split())


def main(a_pathname, b_pathname):
    modules_a = findall(a_pathname)
    modules_b = findall(b_pathname)
    sys_path = [os.path.dirname(os.path.dirname(os.path.commonprefix([a_pathname, b_pathname])))] + sys.path
    out = {}
    traverse_dependencies(modules_a, a_pathname, b_pathname, out, sys_path)
    traverse_dependencies(modules_b, a_pathname, b_pathname, out, sys_path)
    return out


def traverse_dependencies(modules_a, a_pathname, b_pathanme, out, sys_path):
    for module_pathname in modules_a:
        mf = ModuleFinder(sys_path)
        mf.run_script(module_pathname)
        res = {}
        for mod_name, mod_obj in mf.modules.iteritems():
            pathname = mod_obj.__file__
            if pathname is not None and (a_pathname in pathname or b_pathanme in pathname):
                res[mod_obj.__file__] = mod_name
        if len(res) > 1:
            seek_module = module_meta(res[module_pathname], module_pathname)
            del res[module_pathname]
            out[seek_module] = set(module_meta(mod_name, pathname) for pathname, mod_name in res.iteritems())

if __name__ == '__main__':
    path = sys.argv[1]
