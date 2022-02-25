# This file defines how PyOxidizer application building and packaging is
# performed. See PyOxidizer's documentation at
# https://pyoxidizer.readthedocs.io/en/stable/ for details of this
# configuration file format.

PYOXIDIZER_BUILD_DIR = VARS.get("PYOXIDIZER_BUILD_DIR", "build")


# Configuration files consist of functions which define build "targets."
# This function creates a Python executable and installs it in a destination
# directory.
def make_exe():
    dist = default_python_distribution()

    policy = dist.make_python_packaging_policy()

    policy.allow_files = True

    policy.extension_module_filter = "all"

    policy.include_distribution_sources = True

    policy.include_distribution_resources = False

    policy.include_test = False

    policy.resources_location = "in-memory"

    policy.resources_location_fallback = "filesystem-relative:lib"


    python_config = dist.make_python_interpreter_config()


    # Automatically calls `multiprocessing.set_start_method()` with an
    # appropriate value when OxidizedFinder imports the `multiprocessing`
    # module.
    python_config.multiprocessing_start_method = 'auto'


    # Evaluate a string as Python code when the interpreter starts.
    python_config.run_command = "from app import main; main()"

    # Produce a PythonExecutable from a Python distribution, embedded
    # resources, and other options. The returned object represents the
    # standalone executable that will be built.
    exe = dist.to_python_executable(
        name="monopoly",
        packaging_policy=policy,
        config=python_config,
    )

    exe.add_python_resources(exe.pip_install([CWD]))

    return exe

def make_embedded_resources(exe):
    return exe.to_embedded_resources()

def make_install(exe):
    # Create an object that represents our installed application file layout.
    files = FileManifest()

    # Add the generated executable to our install layout in the root directory.
    files.add_python_resource(".", exe)

    return files


# Tell PyOxidizer about the build targets defined above.
register_target("exe", make_exe)
register_target("resources", make_embedded_resources, depends=["exe"], default_build_script=True)
register_target("install", make_install, depends=["exe"], default=True)

set_build_path(CWD + "/" + PYOXIDIZER_BUILD_DIR)

# Resolve whatever targets the invoker of this configuration file is requesting
# be resolved.
resolve_targets()
