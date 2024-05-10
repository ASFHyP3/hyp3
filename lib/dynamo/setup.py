from setuptools import find_packages, setup

setup(
    name='dynamo',
    license='BSD',
    include_package_data=True,

    install_requires=[
        'boto3',
        'python-dateutil',
        'requests',
    ],
    python_requires='~=3.9',

    packages=find_packages(),

    package_data={'dynamo': ['*.json']},
)
