from setuptools import setup

setup(
    name='group_us',
    version="1.0.1",
    author="Anjay Goel",
    author_email="anjaygoel@gmail.com",
    description="GroupUs App Backend",
    packages=['group_us'],
    include_package_data=True,
    install_requires=[
        'flask',
    ],
)
 
