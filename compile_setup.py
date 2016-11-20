from cx_Freeze import setup, Executable, hooks

# NOTE: you can include any other necessary external imports here aswell

# If you delete the whole folder you need to copy all .dll files from C:\Python34\Lib\site-packages\numpy\core
# into the folder of the executable (build/exe.win32-3.4)

includefiles = []  # include any files here that you wish
includes = []
excludes = ['matplotlib','scipy','PySide']
packages = []

exe = Executable(
    # what to build
    script="brief_latex_parser.py",  # the name of your main python script goes here
    initScript=None,
    base='',  # if creating a GUI instead of a console app, type "Win32GUI"
    targetName="iScientist_letter_parser.exe",  # this is the name of the executable file
)

setup(
    # the actual setup & the definition of other misc. info
    name="iScientist letter parser",  # program name
    version="1.0",
    description='Software for parsing letters',
    author="Jannick Weisshaupt",
    options={"build_exe": {"excludes": excludes, "packages": packages,
                           "include_files": includefiles, "includes": includes}},
    executables=[exe]
)