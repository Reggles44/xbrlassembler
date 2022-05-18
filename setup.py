from distutils.core import setup

setup(
    name="XBRLAssembler",
    version="0.13.1",
    author="Reggles",
    author_email="reginaldbeakes@gmail.com",
    description="An assembler for XBRL Documents into pandas",
    url="https://gitlab.com/Reggles44/xbrlassembler",
    include_package_data=True,
    packages=['xbrlassembler'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
