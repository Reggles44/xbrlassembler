import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="XBRLAssembler",
    version="0.4",
    author="Reggles",
    author_email="reginaldbeakes@gmail.com",
    description="An assembler for XBRL Documents into pandas",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/Reggles44/xbrlassembler",
    include_package_data=True,
    packages=['xbrlassembler'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    setup_requires=['flake8']
)
