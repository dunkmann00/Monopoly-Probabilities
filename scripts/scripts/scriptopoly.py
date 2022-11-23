from .utils import (
    DecoratedArgParse,
    Env,
    VirtualEnv,
    use_virtual_env,
    monopoly_probabilities_dir
)
from contextlib import contextmanager
from pathlib import Path
from shlex import split
import sys, shutil, os, glob

PYINSTALLER_BUILD_DIR = os.getenv("PYINSTALLER_BUILD_DIR", "pyinstaller-build")
PYOXIDIZER_BUILD_DIR = os.getenv("PYOXIDIZER_BUILD_DIR", "pyoxidizer-build")
NUITKA_BUILD_DIR = os.getenv("NUITKA_BUILD_DIR", "nuitka-build")

PYINSTALLER = shutil.which("pyinstaller")
PYOXIDIZER = shutil.which("pyoxidizer")

BUILD_DISTPATH = os.getenv("BUILD_DISTPATH")

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
    "dist*",
    PYINSTALLER_BUILD_DIR,
    "monopoly.spec",
    PYOXIDIZER_BUILD_DIR,
    NUITKA_BUILD_DIR,
    "app/cython_ext/*.so",
    "app/cython_ext/*.pyd"
]

PYINSTALLER_BUILD_COMMAND = f"""
{PYINSTALLER} {PYINSTALLER_BUILD_DIR}/monopoly.py
    --add-data {PYINSTALLER_BUILD_DIR}/app/data/{os.pathsep}app/data
    --distpath {{}}
    --workpath {PYINSTALLER_BUILD_DIR}/build
    -F
"""

PYOXIDIZER_BUILD_COMMAND = f"""
{PYOXIDIZER} build --release --var PYOXIDIZER_BUILD_DIR {PYOXIDIZER_BUILD_DIR}
"""

NUITKA_BUILD_COMMAND = f"""
-m nuitka --onefile --assume-yes-for-downloads
    --include-data-file={NUITKA_BUILD_DIR}/app/data/*.txt=app/data/
    --output-dir={NUITKA_BUILD_DIR}/build
    {NUITKA_BUILD_DIR}/monopoly.py
"""

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
    mp_dir = monopoly_probabilities_dir()
    for artifact in BUILD_ARTIFACTS:
        artifact_paths = mp_dir.glob(artifact)
        for artifact_path in artifact_paths:
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
@script_parser.argument("--distpath", help="Where to put the binary build. (Default: dist)", default="dist")
@script_parser.argument("--no-extension", help="Build the binary without the C extension.", action="store_false")
@script_parser.argument("--macos-codesign-identity", help="Sign the binary build with the provided identity (macOS only).")
def pyinstaller(args, env):
    if PYINSTALLER is None:
        print("--- PyInstaller not installed. Run 'scriptopoly install' to install ---")
        return
    print("--- Building binary with PyInstaller. ---")
    distpath = BUILD_DISTPATH or args.distpath
    distpath = Path(distpath) / "pyinstaller"
    shutil.rmtree(distpath, ignore_errors=True)
    with extension_manager(build=args.no_extension):
        env.setup_py("build", "--build-lib", PYINSTALLER_BUILD_DIR)
    shutil.copy2(Path("monopoly.py"), Path(PYINSTALLER_BUILD_DIR))
    print("--- Done ---")
    print("--- Creating PyInstaller single file executable. ---")
    build_command = PYINSTALLER_BUILD_COMMAND
    if sys.platform == 'darwin' and args.macos_codesign_identity:
        build_command += f"--codesign-identity \"{args.macos_codesign_identity}\""
    env.run(*split(build_command.format(distpath.as_posix())))
    print(f"--- Done. File can be found in {distpath} ---")

@script_parser.parser(help_desc="Build a monopoly binary with PyOxidizer.")
@script_parser.argument("--distpath", help="Where to put the binary build. (Default: dist)", default="dist")
@script_parser.argument("--no-extension", help="Build the binary without the C extension.", action="store_false")
@script_parser.argument("--macos-codesign-identity", help="Sign the binary build with the provided identity (macOS only).")
def pyoxidizer(args, env):
    if PYOXIDIZER is None:
        print("--- PyOxidizer not installed. Run 'scriptopoly install' to install ---")
        return
    print("--- Building binary with PyOxidizer. ---")
    distpath = BUILD_DISTPATH or args.distpath
    distpath = Path(distpath) / "pyoxidizer"
    shutil.rmtree(distpath, ignore_errors=True)
    with extension_manager(build=args.no_extension):
        env.run(*split(PYOXIDIZER_BUILD_COMMAND))
    print("--- Signing Binaries ---")
    if sys.platform == 'darwin' and args.macos_codesign_identity:
        files = glob.glob(f"{PYOXIDIZER_BUILD_DIR}/**/monopoly*", recursive=True)
        env.run("/usr/bin/codesign", "--force", "-s", args.macos_codesign_identity, "--timestamp", "--options", "runtime", *files, "-v")
    print(f"--- Done. Copying package files into {distpath} ---")
    for platform_dir in Path(PYOXIDIZER_BUILD_DIR).iterdir():
        install_dir = platform_dir / "release/install"
        shutil.copytree(install_dir, distpath, dirs_exist_ok=True)
    print(f"--- Done. Files can be found in {distpath} ---")

@script_parser.parser(help_desc="Build a monopoly binary with Nuitka.")
@script_parser.argument("--distpath", help="Where to put the binary build. (Default: dist)", default="dist")
@script_parser.argument("--no-extension", help="Build the binary without the C extension.", action="store_false")
@script_parser.argument("--macos-codesign-identity", help="Sign the binary build with the provided identity (macOS only).")
def nuitka(args, env):
    try:
        import nuitka
    except:
        print("--- Nuitka not installed. Run 'scriptopoly install' to install ---")
        return
    print("--- Building binary with Nuitka. ---")
    distpath = BUILD_DISTPATH or args.distpath
    distpath = Path(distpath) / "nuitka"
    shutil.rmtree(distpath, ignore_errors=True)
    with extension_manager(build=args.no_extension):
        env.setup_py("build", "--build-lib", NUITKA_BUILD_DIR)
    shutil.copy2(Path("monopoly.py"), Path(NUITKA_BUILD_DIR))
    print("--- Done ---")
    print("--- Creating Nuitka single file executable. ---")
    build_command = NUITKA_BUILD_COMMAND
    if sys.platform == 'darwin' and args.macos_codesign_identity:
        build_command += f"--macos-sign-identity=\"{args.macos_codesign_identity}\" --macos-sign-notarization"
    env.python(*split(build_command))
    print(f"--- Done. Copying package file into {distpath} ---")
    distpath.mkdir(parents=True, exist_ok=True)
    monopoly_file_src = Path(NUITKA_BUILD_DIR) / "build" / f"monopoly{'.exe' if os.name == 'nt' else '.bin'}"
    monopoly_file_dest = distpath / f"monopoly{'.exe' if os.name == 'nt' else ''}"
    shutil.copy2(monopoly_file_src, monopoly_file_dest)
    print(f"--- Done. Files can be found in {distpath} ---")

@script_parser.parser(help_desc="Build a monopoly binary with all packaging tools.")
@script_parser.argument("--distpath", help="Where to put the binary build. (Default: dist)", default="dist")
@script_parser.argument("--no-extension", help="Build the binaries without the C extension.", action="store_false")
@script_parser.argument("--macos-codesign-identity", help="Sign the binary build with the provided identity (macOS only).")
def all_binaries(args, env):
    pyinstaller(args, env)
    pyoxidizer(args, env)
    nuitka(args, env)

@script_parser.parser(help_desc="Create an archive of the binariy builds.")
@script_parser.argument("--base-name", help="The name of the file to create, including the path, minus any format-specific extension.")
@script_parser.argument("--distpath", help="Where to find the binary builds. (Default: dist)", default="dist")
@script_parser.argument("--format", help="Force a specific archive format to be used. (Default: zip on Windows, gztar otherwise)")
def archive_binaries(args, env):
    print("--- Archiving Binary Builds. ---")
    distpath = BUILD_DISTPATH or args.distpath
    distpath = Path(distpath)
    base_name = args.base_name or str(distpath)
    format = args.format or ('zip' if os.name == 'nt' else 'gztar')
    archive_name = shutil.make_archive(base_name, format, base_dir=distpath)
    print(f"--- Done. Archive can be found at {archive_name} ---")

def main():
    env = VirtualEnv.get() if use_virtual_env() else Env.get()
    args = script_parser.parse_args()
    args.func(args, env)

if __name__ == '__main__':
    main()
