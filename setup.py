from setuptools import setup

setup(
   name='bayao_finance',
   version='0.2',
   description='Creating stock indicators',
   author='Rafael Bayao',
   author_email='rgbayao@gmail.com',
   packages=['bayao_finance'],
   install_requires=['pandas, numpy, yfinance, datetime'],
)