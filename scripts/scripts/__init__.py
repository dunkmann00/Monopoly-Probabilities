# We purposely want a scripts module in a scripts module because that makes
# importing either the install or scriptopoly module the same from the top level
# of the project or from within the outer scripts directory.
#
# Scenarios for importing scripts:
#
# Top Level:
#   - Import in install_monopoly.py
#   - Poetry script command ('tool.poetry.scripts' in pyproject.toml)
#
# Within outer scripts directory:
#   - setup.py 'console_scripts' 'entry_point' command. This works because we
#     add the outer scripts directory into a '.pth' file which adds it to python
#     'sys.path'.
#
# While this isn't absolutely necessary, it makes the scriptopoly import from
# the entry point in setup.py the same as the import from the poetry script
# command.
