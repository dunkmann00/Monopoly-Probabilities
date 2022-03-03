from pathlib import Path
from shlex import split
from contextlib import contextmanager
import sys, shutil, os, venv, argparse, subprocess

PYINSTALLER_BUILD_DIR = os.getenv("PYINSTALLER_BUILD_DIR", "pyinstaller-build")
PYOXIDIZER_BUILD_DIR = os.getenv("PYOXIDIZER_BUILD_DIR", "pyoxidizer-build")
NUITKA_BUILD_DIR = os.getenv("NUITKA_BUILD_DIR", "nuitka-build")

PYINSTALLER = shutil.which("pyinstaller")
PYOXIDIZER = shutil.which("pyoxidizer")

# On Windows these need to be converted to Posix strings because shlex only
# works with unix shells. 'shutil.which' produces a path string with forward
# slashes, which shlex removes, leaving behind a path that is garbage
if os.name == 'nt':
    if PYINSTALLER:
        PYINSTALLER = Path(PYINSTALLER).as_posix()
    if PYOXIDIZER:
        PYOXIDIZER = Path(PYOXIDIZER).as_posix()

BUILD_ARTIFACTS = [
    "build",
    "dist",
    PYINSTALLER_BUILD_DIR,
    "monopoly.spec",
    PYOXIDIZER_BUILD_DIR,
    NUITKA_BUILD_DIR
]

PYINSTALLER_BUILD_COMMAND = f"""
{PYINSTALLER} {PYINSTALLER_BUILD_DIR}/monopoly.py
    --add-data {PYINSTALLER_BUILD_DIR}/app/data/{os.pathsep}app/data
    --distpath dist/pyinstaller
    --workpath {PYINSTALLER_BUILD_DIR}/build
    -F
"""

PYOXIDIZER_BUILD_COMMAND = f"""
{PYOXIDIZER} build --release --var PYOXIDIZER_BUILD_DIR {PYOXIDIZER_BUILD_DIR}
"""

NUITKA_BUILD_COMMAND = f"""
-m nuitka --onefile
    --include-data-file={NUITKA_BUILD_DIR}/app/data/*.txt=app/data/
    --output-dir={NUITKA_BUILD_DIR}/build
    -o dist/nuitka/monopoly{'.exe' if os.name == 'nt' else ''}
    {NUITKA_BUILD_DIR}/monopoly.py
"""


class VirtualEnv():
    def __init__(self, python):
        self._python = python

    @classmethod
    def get(cls):
        return VirtualEnv(sys.executable) if cls.is_venv_active() else None

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

@contextmanager
def extension_manager(build=True):
    if build:
        os.environ["BUILD_EXTENSION"] = "1"
    try:
        yield
    finally:
        if "BUILD_EXTENSION" in os.environ:
            del os.environ["BUILD_EXTENSION"]

script_parser = DecoratedArgParse(description="Helper script to perform various tasks for monopoly.")

@script_parser.parser(help_desc="Build the C extension version of the monopoly object.")
def build(args, env):
    print("--- Building monopoly object C extension ---")
    with extension_manager():
        env.setup_py("build_ext", "-i", "-f")
    print("--- Done ---")


@script_parser.parser(help_desc="Install dependencies necessary for building binaries.")
def install(args, env):
    print("--- Installing dependencies needed for building binaries ---")
    env.pip("install", "-r", "requirements-binaries.txt")
    print("--- Done ---")

@script_parser.parser(help_desc="Remove files & folders from building binaries, etc.")
def clean(args, env):
    print("--- Removing build artifacts ---")
    for artifact in BUILD_ARTIFACTS:
        artifact_path = Path(artifact)
        if artifact_path.is_dir():
            shutil.rmtree(artifact_path, ignore_errors=True)
        else:
            artifact_path.unlink(missing_ok=True)
    print("--- Done ---")

@script_parser.parser(help_desc="Run the cythonize command on monopoly.pyx.")
def monopolize(args, env):
    print("--- Running cythonize on monopoly.pyx ---")
    try:
        from Cython.Build import cythonize
    except:
        print("--- Cython not installed...installing now ---")
        env.pip("install", "-r", "requirements-cython.txt")
        from Cython.Build import cythonize
    cythonize("app/cython_ext/monopoly.pyx", annotate=True)
    print("--- Done ---")

@script_parser.parser(help_desc="Build a monopoly binary with PyInstaller.")
@script_parser.argument("--no-extension", help="Build the binary without the C extension.", action="store_false")
def pyinstaller(args, env):
    if PYINSTALLER is None:
        print("--- PyInstaller not installed. Run 'scriptopoly install' to install ---")
        return
    print("--- Building binary with PyInstaller. ---")
    shutil.rmtree(Path("dist/pyinstaller"), ignore_errors=True)
    with extension_manager(build=args.no_extension):
        env.setup_py("build", "--build-lib", PYINSTALLER_BUILD_DIR)
    shutil.copy2(Path("monopoly.py"), Path(PYINSTALLER_BUILD_DIR))
    print("--- Done ---")
    print("--- Creating PyInstaller single file executable. ---")
    env.run(*split(PYINSTALLER_BUILD_COMMAND))
    print("--- Done. File can be found in dist/ ---")

@script_parser.parser(help_desc="Build a monopoly binary with PyOxidizer.")
@script_parser.argument("--no-extension", help="Build the binary without the C extension.", action="store_false")
def pyoxidizer(args, env):
    if PYOXIDIZER is None:
        print("--- PyOxidizer not installed. Run 'scriptopoly install' to install ---")
        return
    print("--- Building binary with PyOxidizer. ---")
    dist_dir = Path("dist/pyoxidizer")
    shutil.rmtree(dist_dir, ignore_errors=True)
    with extension_manager(build=args.no_extension):
        env.run(*split(PYOXIDIZER_BUILD_COMMAND))
    print("--- Done. Copying package files into dist/ ---")
    dist_dir.mkdir(parents=True, exist_ok=True)
    for platform_dir in Path(PYOXIDIZER_BUILD_DIR).iterdir():
        install_dir = platform_dir / "release/install"
        shutil.copytree(install_dir, dist_dir, dirs_exist_ok=True)
    print("--- Done. Files can be found in dist/ ---")

@script_parser.parser(help_desc="Build a monopoly binary with Nuitka.")
@script_parser.argument("--no-extension", help="Build the binary without the C extension.", action="store_false")
def nuitka(args, env):
    try:
        import nuitka
    except:
        print("--- Nuitka not installed. Run 'scriptopoly install' to install ---")
        return
    print("--- Building binary with Nuitka. ---")
    dist_dir = Path("dist/nuitka")
    shutil.rmtree(dist_dir, ignore_errors=True)
    with extension_manager(build=args.no_extension):
        env.setup_py("build", "--build-lib", NUITKA_BUILD_DIR)
    shutil.copy2(Path("monopoly.py"), Path(NUITKA_BUILD_DIR))
    print("--- Done ---")
    print("--- Creating Nuitka single file executable. ---")
    # Making the directories ourselves is only needed for Windows
    # but is okay to do regardless of platform
    dist_dir.mkdir(parents=True, exist_ok=True)
    env.python(*split(NUITKA_BUILD_COMMAND))
    print("--- Done. Files can be found in dist/ ---")

@script_parser.parser(help_desc="Build a monopoly binary with all packaging tools.")
@script_parser.argument("--no-extension", help="Build the binaries without the C extension.", action="store_false")
def all_binaries(args, env):
    pyinstaller(args, env)
    pyoxidizer(args, env)
    nuitka(args, env)

@script_parser.parser(help_desc="Remove the virtual environment (along with the egg-info folder).")
def remove_venv(args, env):
    if env is None:
        venv_dir = args.venvdir
    else:
        venv_dir = sys.prefix
    print("--- Removing virtual environment ---")
    venv_path = Path(venv_dir).resolve()

    # See note above in VirtualEnv.make for why this is needed.
    # In this case, the only time venv_path will point to nothing is when
    # the virtual environment has already been removed.
    if not venv_path.is_absolute():
        venv_path = Path().resolve() / venv_path

    print("Virtual Environment Path:")
    print(venv_path)

    unremoved = []
    def rm_error(func, path, exc_info):
        if exc_info[0] != FileNotFoundError:
            unremoved.append(str(path))

    shutil.rmtree(Path("monopoly_probabilities.egg-info"), onerror=rm_error)
    shutil.rmtree(venv_path, onerror=rm_error)

    if len(unremoved) > 0:
        print("\nThe following items could not be removed:")
        print("\n".join(unremoved))
        print(
            "\nIf ran from inside the virtual environment, deactivate and try to\n"
            "uninstall again by running the install_monopoly script with the\n"
            "--uninstall flag.\n"
        )

    print("--- Done ---")
    if "VIRTUAL_ENV" in os.environ:
        print("The virtual environment is still active but will no longer work.")
        print("Enter 'deactivate' to leave the virtual environment.")

def install_venv(args):
    print("--- Installing Virtual Environment ---")
    env = VirtualEnv.make(venv_dir=args.venvdir)
    print("--- Installing Monopoly-Probabilites ---")
    env.pip("install", "-e", ".")
    print("--- Done ---")
    print("--- To uninstall, run this script again with --uninstall ---")

def run_python():
    # Still using 'DecoratedArgParse' here for the error text handling
    py_parser = DecoratedArgParse(
        description=("Install monopoly into a virtual environment. This exposes two commands, 'monopoly', "
                     "which runs the simulation, and 'scriptopoly', which is a helper script which can "
                     "perform various tasks for the monopoly project.")
    )
    py_parser.arg_parser.add_argument("--venvdir",
                                      help="The directory for the virtual environment. Default: venv",
                                      default="venv"
    )
    py_parser.arg_parser.add_argument("--uninstall",
                                      help=("Remove the virtual environment (along with the egg-info folder) "
                                            "that monopoly was installed in."),
                                      action="store_true"
    )
    args = py_parser.parse_args()
    if args.uninstall:
        remove_venv(args, VirtualEnv.get())
        return

    install_venv(args)

def run_script():
    env = VirtualEnv.get()
    args = script_parser.parse_args()
    args.func(args, env)

def main(setup_venv=False):
    if setup_venv:
        run_python()
    else:
        run_script()

if __name__ == '__main__':
    main(setup_venv=True)
