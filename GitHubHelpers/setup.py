from distutils.core import setup

setup(
    name='GitHubHelpers',
    version='0.1',
    packages=['github',],
    scripts=['bin/triage','bin/issues', 'bin/runreports'],
    license='Apache',
    long_description="Github issue api helpers",
)
