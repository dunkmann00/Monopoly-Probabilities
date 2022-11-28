from .utils import (
    DecoratedArgParse,
    Env,
    VirtualEnv,
    use_virtual_env,
    monopoly_probabilities_dir
)
from pathlib import Path
import shutil, subprocess

def remove_venv(args, env):
    if env is None:
        venv_dir = args.venvdir
    else:
        print("Virtual Environment must not be active when uninstalling.")
        print("Enter 'deactivate' to leave the virtual environment.")
        return

    print("--- Removing virtual environment ---")
    venv_path = Path(venv_dir).resolve()

    # See note above in VirtualEnv.make for why this is needed.
    # In this case, the only time venv_path will point to nothing is when
    # the virtual environment has already been removed.
    if not venv_path.is_absolute():
        venv_path = Path().resolve() / venv_path

    print("Virtual Environment Path:")
    print(venv_path)

    if not venv_path.exists():
        print("Virtual Environment directory not found.")
        print("--- Aborting ---")
        return
    elif not venv_path.is_dir():
        print("Virtual Environment path is not a directory.")
        print("--- Aborting ---")
        return

    unremoved = []
    def rm_error(func, path, exc_info):
        if exc_info[0] != FileNotFoundError:
            unremoved.append(str(path))

    shutil.rmtree(Path("monopoly_probabilities.egg-info"), onerror=rm_error)
    shutil.rmtree(venv_path, onerror=rm_error)

    if len(unremoved) > 0:
        print("\nThe following items could not be removed:")
        print("\n".join(unremoved))

    print("--- Done ---")

def uninstall_monopoly(args):
    print("--- Uninstalling Monopoly-Probabilities ---")
    remove_venv(args, VirtualEnv.get())

def add_script_pth(env):
    site_packages = env.python("-c", "import site; print(site.getsitepackages()[0])", stdout=subprocess.PIPE, text=True).stdout.strip()
    site_packages_dir = Path(site_packages)
    script_pth = site_packages_dir / "script.pth"
    script_pth.write_text(str(Path("scripts").resolve()))

def install_venv(args):
    print("--- Installing Virtual Environment ---")
    env = VirtualEnv.make(venv_dir=args.venvdir)
    print("--- Done ---")
    return env

def install_monopoly(env):
    print("--- Installing Monopoly-Probabilities ---")
    env.pip("install", "--use-pep517", "-e", ".")
    env.pip("install", "--use-pep517", "-r", "requirements-runtime.txt")
    add_script_pth(env)
    print("--- Done ---")
    print("--- To uninstall, run this script again with --uninstall ---")

def main():
    if Path.cwd() != monopoly_probabilities_dir():
        print("Current working directory must be 'Monopoly-Probabilities' to "
              "install.")
        return

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
        uninstall_monopoly(args)
        return

    env = install_venv(args) if use_virtual_env() else Env.get()
    install_monopoly(env)

if __name__ == '__main__':
    main()
