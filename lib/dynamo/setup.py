from setuptools import find_packages, setup


setup(
    name='dynamo',
    license='BSD',
    include_package_data=True,
    install_requires=[
        # TODO: unpin these here and pin them in requirements files?
        'asf_enumeration==0.2.0',
        'asf_search==9.0.8',
        'boto3',
        'python-dateutil',
        'requests',
    ],
    python_requires='~=3.13',
    packages=find_packages(),
    package_data={'dynamo': ['*.json']},
)
