from setuptools import setup
from setuptools.extension import Extension
import os.path
import os
import pyblooming

# Get the long description by reading the README
try:
    readme_content = open("README.rst").read()
except:
    readme_content = ""

ext_modules = [
        Extension("pyblooming.cbitmap",
            extra_compile_args=['-std=gnu99', '-O2'],
            sources = ["pyblooming/cbitmap.pyx", "pyblooming/cbitmaputil.c","pyblooming/cbitmaputil.h"],
            include_dirs = ["pyblooming"],
            library_dirs = ["pyblooming"]
            ),
        Extension("pyblooming.cbloom",
            extra_compile_args=['-std=gnu99', '-O2'],
            sources = ["pyblooming/cbloom.pyx"],
            include_dirs = ["pyblooming"],
            library_dirs = ["pyblooming"]
            ),
      ]

# Create the actual setup method
setup(name='pyblooming',
      version=pyblooming.__version__,
      description='Classic bloom filter using memory mapped files',
      long_description=readme_content,
      author='Armon Dadgar',
      author_email='armon@kiip.me',
      maintainer='Armon Dadgar',
      maintainer_email='armon@kiip.me',
      url="https://github.com/kiip/pyblooming/",
      license="MIT License",
      keywords=["bloom", "filter", "mmap"],
      packages=['pyblooming'],
      classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries"
      ],
      ext_modules = ext_modules,
    )
