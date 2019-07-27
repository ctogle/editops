from setuptools import setup, find_packages
from setuptools.extension import Extension
from Cython.Build import cythonize
import numpy as np

extensions = cythonize(Extension(
    "editops.editops", ["editops/editops.pyx"], include_dirs=[np.get_include()]))
setup(name="editops", packages=find_packages(), ext_modules=extensions)
