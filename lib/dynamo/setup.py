from setuptools import find_packages, setup

setup(
    name='dynamo',
    license='BSD',
    include_package_data=True,

    install_reqires=[
        'boto3',
        'dateutil',
    ],
    python_requires='~=3.8',

    packages=find_packages(),
)
