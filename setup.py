from setuptools import setup, Command
import pyblooming

# Get the long description by reading the README
try:
    readme_content = open("README.rst").read()
except:
    readme_content = ""

# Create the actual setup method
setup(name='pyblooming',
      version=pyblooming.__version__,
      description='Classic bloom filter using memory mapped files',
      long_description=readme_content,
      author='Armon Dadgar',
      author_email='armon@kiip.me',
      maintainer='Armon Dadgar',
      maintainer_email='armon@kiip.me',
      url="https://kiip.github.com/pyblooming/",
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
    ]
      )
