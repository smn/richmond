from setuptools import setup, find_packages

setup(
    name = "smn-richmond",
    version = "0.1",
    url = 'http://github.com/smn/richmond',
    license = 'BSD',
    description = "Mobile messaging infrastructure.",
    author = 'Simon de Haan',
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    install_requires = ['setuptools',],
)

