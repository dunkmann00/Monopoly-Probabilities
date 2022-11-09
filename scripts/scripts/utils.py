from pathlib import Path
import sys, os, venv, argparse, subprocess

NO_VIRTUAL_ENV = os.getenv("NO_VIRTUAL_ENV")

class Env():
    def __init__(self, python):
        self._python = python

    @classmethod
    def get(cls):
        return cls(sys.executable)

    @staticmethod
    def run(*args, **kwargs):
        print(" ".join(args))
        completed_process = subprocess.run(args, **kwargs)
        completed_process.check_returncode()
        return completed_process

    def python(self, *args, **kwargs):
        return self.run(self._python, *args, **kwargs)

    def pip(self, *args, **kwargs):
        return self.python("-m", "pip", "--isolated", "--disable-pip-version-check", *args, **kwargs)

    def setup_py(self, *args, **kwargs):
        return self.python("setup.py", *args, **kwargs)


class VirtualEnv(Env):
    @classmethod
    def get(cls):
        return cls(sys.executable) if cls.is_venv_active() else None

    @classmethod
    def make(cls, venv_dir="venv"):
        if cls.is_venv_active():
            print("Virtual Environment already active at:")
            print(sys.prefix, end="\n\n")
            env = VirtualEnv(sys.executable)
        else:
            venv_path = Path(venv_dir).resolve()
            # For Python <3.10, resolve won't return an absolute path if the
            # file/directory does not exist on Windows
            # https://bugs.python.org/issue38671
            if not venv_path.is_absolute():
                venv_path = Path().resolve() / venv_path
            print("Creating new Virtual Environment at:")
            print(venv_path, end="\n\n")
            # https://github.com/python/cpython/blob/38f331d4656394ae0f425568e26790ace778e076/Lib/venv/__init__.py#L476-L479
            if os.name == 'nt':
                use_symlinks = False
            else:
                use_symlinks = True
            builder = venv.EnvBuilder(system_site_packages=False,
                                      clear=False,
                                      symlinks=use_symlinks,
                                      upgrade=False,
                                      with_pip=True,
                                      prompt=None,
                                      upgrade_deps=False
            )
            context = builder.ensure_directories(venv_path)
            builder.create(venv_path)
            env = VirtualEnv(context.env_exec_cmd)

        return env

    @classmethod
    def is_venv_active(self):
        return sys.prefix != sys.base_prefix

def use_virtual_env():
    return not NO_VIRTUAL_ENV

class DecoratedArgParse():
    def __init__(self, *args, **kwargs):
        self.arg_parser = argparse.ArgumentParser(*args, **kwargs)
        self.arg_parser.error = self.error #Provide our own error function
        self._subparsers = None

    @property
    def subparsers(self):
        if self._subparsers is None:
            self._subparsers = self.arg_parser.add_subparsers(
                title="Available Commands",
                required=True,
                metavar=""
            )
        return self._subparsers

    def make_subparsers(self, *args, **kwargs):
        self._subparsers = self.arg_parser.add_subparsers(*args, **kwargs)

    def parse_args(self, args=None):
        return self.arg_parser.parse_args(args)

    def parser(self, *args, **kwargs):
        def decorator(f):
            parser_args, parser_kwargs = self.check_params((args, kwargs))
            parser = self.subparsers.add_parser(f.__name__.lower().replace("_", "-"), *parser_args, **parser_kwargs)
            if hasattr(f, "__argparse_params__"):
                for params in f.__argparse_params__:
                    parser_args, parser_kwargs = params
                    parser.add_argument(*parser_args, **parser_kwargs)
                del f.__argparse_params__
            parser.set_defaults(func=f)
            return f
        return decorator

    def argument(self, *args, **kwargs):
        def decorator(f):
            params = (args, kwargs)
            if not hasattr(f, "__argparse_params__"):
                f.__argparse_params__ = []
            f.__argparse_params__.append(params)
            return f
        return decorator

    @staticmethod
    def check_params(params):
        args, kwargs = params
        help_desc = kwargs.pop("help_desc", None)
        if help_desc is not None:
            kwargs["help"] = help_desc
            kwargs["description"] = help_desc
        return (args, kwargs)

    def error(self, message):
        """error(message: string)
        Prints a usage message incorporating the message to stderr,
        followed by the help message, and then exits.
        If you override this in a subclass, it should not return -- it
        should either exit or raise an exception.
        """
        sys.stderr.write(f"error: {message}\n")
        self.arg_parser.print_help(sys.stderr)
        sys.exit(2)

def monopoly_probabilities_dir():
    return Path(__file__).parents[2].resolve()
