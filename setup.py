from setuptools import setup
from setuptools.extension import Extension
from Cython.Distutils import build_ext
import os.path
import os
import pyblooming

# Get the long description by reading the README
try:
    readme_content = open("README.rst").read()
except:
    readme_content = ""

# Get the current dir
current_path = os.path.dirname(os.path.abspath(__file__))

ext_modules = [
        Extension("cbitmap",
            extra_compile_args=['-std=gnu99', '-O2'],
            sources = ["pyblooming/cbitmap.pyx","pyblooming/cbitmaputil.c"],
            include_dirs = [os.path.join(current_path, 'pyblooming')],
            library_dirs = [os.path.join(current_path, 'pyblooming')],
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
      cmdclass = {'build_ext':build_ext},
      ext_modules = ext_modules,
    )
