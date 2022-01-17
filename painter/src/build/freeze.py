import glob
import os
import site
import shutil
import subprocess
from settings import Settings


def run_pyinstaller(settings, extra_args=[]):
    app_name = settings.get("app_name")
    target_dir = os.path.abspath("target")
    # Use abspath to convert from unix path for windows.
    main_module = os.path.abspath(settings.get("main_module"))

    cmd = []
    cmd.extend(["pyinstaller"])
    cmd.extend(["--debug", "all"])
    cmd.extend(["--log-level", "DEBUG"])
    cmd.extend(["--noupx"])
    cmd.extend(extra_args)
    for hidden_import in settings.get_with_default("hidden_imports", []):
        cmd.extend(["--hidden-import", hidden_import])
    cmd.extend(["--distpath", target_dir])
    cmd.extend(["--specpath", os.path.join(target_dir, "PyInstaller")])
    cmd.extend(["--workpath", os.path.join(target_dir, "PyInstaller")])
    cmd.extend(["--noconfirm"])
    cmd.extend(["--name", app_name])
    cmd.extend([main_module])

    print(" ".join(cmd))

    subprocess.check_call(cmd)


def freeze(settings):
    if settings.is_mac():
        return freeze_mac(settings)
    if settings.is_linux():
        return freeze_linux(settings)
    if settings.is_windows():
        return freeze_windows(settings)


### Linux ###


def freeze_linux(settings):
    run_pyinstaller(settings, [])

    build_dir = "./target/RootPainter"
    fix_broken_packages(build_dir=build_dir)


### Windows ###


CPP_DLL_LIST = [
    # "msvcr100.dll",
    "msvcr110.dll",
    "msvcp110.dll",
    "vcruntime140.dll",
    "msvcp140.dll",
    "concrt140.dll",
    "vccorlib140.dll",
]
UCRT_DLL_LIST = ["api-ms-win-crt-multibyte-l1-1-0.dll"]


def freeze_windows(settings):
    # Check existence of required DLLs before running other commands
    check_has_cpp_dlls()
    check_has_ucrt_dlls()

    target_dir = os.path.abspath("target")
    app_name = settings.get("app_name")
    freeze_dir = os.path.join(target_dir, app_name)

    icon_file = os.path.join(os.path.abspath("src"), "main", "icons", "Icon.ico")

    extra_args = []
    extra_args.extend(["--icon", icon_file])

    run_pyinstaller(settings, extra_args)

    build_dir = os.path.join(target_dir, app_name)
    fix_broken_packages(build_dir=build_dir)

    shutil.copyfile(icon_file, os.path.join(freeze_dir, "Icon.ico"))

    for dll_name in CPP_DLL_LIST:
        copy_dll(dll_name, freeze_dir)

    for dll_name in UCRT_DLL_LIST:
        copy_dll(dll_name, freeze_dir)


def copy_dll(dll_name, freeze_dir):
    expected_dll_location = os.path.join(freeze_dir, dll_name)
    if not os.path.exists(expected_dll_location):
        shutil.copyfile(find_in_path(dll_name), expected_dll_location)


def check_has_cpp_dlls():
    for dll_name in CPP_DLL_LIST:
        try:
            find_in_path(dll_name)
        except LookupError:
            raise FileNotFoundError(
                f"Could not find {dll_name}. Please install C++ Redistributable for Visual Studio 2012 from: https://www.microsoft.com/en-us/download/details.aspx?id=30679",
            )


def check_has_ucrt_dlls():
    for dll_name in UCRT_DLL_LIST:
        try:
            find_in_path(dll_name)
        except LookupError:
            raise FileNotFoundError(
                f"Could not find {dll_name}. You may need to install Windows 10 SDK from https://developer.microsoft.com/en-us/windows/downloads/windows-10-sdk. Otherwise, try installing KB2999226 from https://support.microsoft.com/en-us/kb/2999226. ",
            )


def find_in_path(dll_name):
    for path in os.environ["PATH"].split(os.pathsep):
        dll_file = os.path.join(path, dll_name)
        if os.path.isfile(dll_file):
            return dll_file
    raise LookupError(f"Could not find {dll_name}")


### Mac ###


def freeze_mac(settings):
    target_dir = os.path.abspath("target")

    create_iconset(settings)

    extra_args = []
    extra_args.extend(["--icon", os.path.join(target_dir, "Icon.icns")])
    extra_args.extend(["-w"])

    run_pyinstaller(settings, extra_args)

    remove_pyinstaller_packages(settings)

    build_dir = "./target/RootPainter.app/Contents/MacOS/"
    fix_broken_packages(build_dir=build_dir)


def remove_pyinstaller_packages(settings):
    """
    Removes packages required by pyinstaller
    """
    target_dir = os.path.abspath("target")
    app_name = settings.get("app_name")
    freeze_dir = os.path.join(target_dir, f"{app_name}.app")

    remove_if_exists(os.path.join(freeze_dir, "Contents", "MacOS", "lib"))
    remove_if_exists(os.path.join(freeze_dir, "Contents", "Resources", "lib"))

    remove_if_exists(os.path.join(freeze_dir, "Contents", "MacOS", "include"))
    remove_if_exists(os.path.join(freeze_dir, "Contents", "Resources", "include"))

    remove_if_exists(os.path.join(freeze_dir, "Contents", "MacOS", "2to3"))
    remove_if_exists(os.path.join(freeze_dir, "Contents", "Resources", "2to3"))


def fix_broken_packages(build_dir):
    """
    If you try to run RootPainter on the command line like so:
    ./target/RootPainter.app/Contents/MacOS/RootPainter
    Then you may receive the following error:
    File "skimage/feature/orb_cy.pyx", line 12, in init skimage.feature.orb_cy
    ModuleNotFoundError: No module named 'skimage.feature._orb_descriptor_positions'

    It seems the built application is missing some crucial files from skimage.
    To copy these accross we will assume you have an environment created with venv (virtual env)
    in the current working directory call 'env'
    """

    # Copy missing orb files
    copy_lib_file(
        os.path.join("skimage", "feature", "_orb_descriptor_positions.py"), build_dir
    )
    # copy missing orb plugin file
    copy_lib_file(
        os.path.join("skimage", "feature", "orb_descriptor_positions.txt"), build_dir
    )
    # Copy missing tiffile plugin
    copy_lib_file(
        os.path.join("skimage", "io", "_plugins", "tifffile_plugin.py"), build_dir
    )


def copy_lib_file(libname, build_dir):
    src = find_lib_file(libname)
    dest = os.path.join(build_dir, libname)
    shutil.copyfile(src, dest)


def find_lib_file(libname):
    for site_packages_dir in site.getsitepackages():
        possible = os.path.join(site_packages_dir, libname)

        if os.path.exists(possible):
            return possible

    raise FileNotFoundError(f"Could not find {libname}")


def create_iconset(settings):
    target_dir = os.path.abspath("target")
    if not os.path.exists(os.path.join(target_dir, "Icon.icns")):
        iconset_path = os.path.join(target_dir, "Icon.iconset")
        os.makedirs(iconset_path, exist_ok=True)

        for size, icon_path in get_icons(settings):
            dest_name = create_icon_filename(size)
            shutil.copy(icon_path, os.path.join(target_dir, "Icon.iconset", dest_name))

        subprocess.check_call(
            ["iconutil", "-c", "icns", os.path.join(target_dir, "Icon.iconset")]
        )


def get_icons(settings):
    result = []
    for profile in settings.get_profiles():
        icons_dir = os.path.join("src", "main", "icons", profile)
        for icon_path in glob.glob(f"{icons_dir}/*.png"):
            name = os.path.basename(icon_path)
            size = extract_size(name)
            result.append((size, icon_path))
    return result


def extract_size(icon_filename):
    size = icon_filename.replace(".png", "")
    return int(size)


def create_icon_filename(size):
    return f"icon_{size}x{size}.png"


def remove_if_exists(filename):
    if not os.path.exists(filename):
        return
    if os.path.isfile(filename) or os.path.islink(filename):
        return os.unlink(filename)
    if os.path.isdir(filename):
        return shutil.rmtree(filename)


if __name__ == "__main__":
    freeze(settings=Settings())
