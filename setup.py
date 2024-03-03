import setuptools

LONG_DESC = open("README.md").read()

setuptools.setup(
    name="cansync",
    version="1.0.0",
    author="James K.",
    author_email="jameskowal10@gmail.com",
    description="Sync files from Canvas courses",
    long_description_content_type="text/markdown",
    long_description=LONG_DESC,
    license="MIT",
    packages=["cansync"],
    entry_points={"console_scripts": ["cansync=cansync.main:main"]},
    python_requires=">=3.10.0",
    install_requires=[
        "requests>=2.31.0",
        "toml>=0.10.2",
        "canvasapi>=3.2.0",
        "PyTermGUI>=7.7.0",
    ],
    # test_suite="tests",
    # include_package_data=True,
    zip_safe=False,
)
