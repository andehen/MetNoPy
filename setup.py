from setuptools import setup

setup(name='metnopy',
      version='0.1',
      description='Get weather observations from stations operated by the Norwegian Meteorological Institute',
      url='http://github.com/hennumjr/metnopy',
      author='Anders Asheim Hennum',
      author_email='hennumjr@gmail.com',
      license='MIT',
      packages=['metnopy'],
      install_requires=[
          'pandas',
          'requests'
      ],
      zip_safe=False)
