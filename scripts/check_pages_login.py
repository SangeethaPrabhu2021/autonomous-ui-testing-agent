import importlib, traceback

try:
    import os, sys, traceback
    print('cwd=', os.getcwd())
    print('sys.path[0]=', sys.path[0])
    print('root listing=', os.listdir('.'))
    try:
        m = importlib.import_module('pages.login')
        print('module_file=', m.__file__)
        print('has LoginPage=', hasattr(m, 'LoginPage'))
        print('dir sample=', [n for n in dir(m) if n.lower().startswith('login') or n.endswith('Page')])
    except Exception:
        traceback.print_exc()
except Exception:
    traceback.print_exc()
