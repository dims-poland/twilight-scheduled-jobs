from setuptools import setup, find_packages


setup(
    name='twilight_scheduled_jobs',
    version='0.1',
    description='Twilight time-based scheduled jobs based on schedule package and Skyfield package',
    url='https://github.com/dims-poland/twilight-scheduled-jobs',
    author='Michal Vrábel',
    author_email='michal.vrabel@ncbj.gov.pl',
    license='BSD 2-clause',
    packages=find_packages(),
    setup_requires=['wheel'],
    install_requires=[
        'python-dateutil==2.8.2',
        'pytimeparse==1.1.8',
        'pytz==2023.3',
        'PyYAML==6.0',
        'schedule==1.2.0',
        'skyfield==1.46',
        'tzlocal==5.0.1',
    ],
    data_files=[],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3.9',
    ],
    scripts=[]
)