import setuptools

VERSION = "0.4.0"

setuptools.setup(
	name="epubinfo",
	url="https://github.com/davidgfnet/epubinfo",
	author="davidgfnet",
	keywords="python epub metadata",
	description="A library to parse epub metadata",
	license="GPL",
	classifiers=[
		"Operating System :: OS Independent",
		"Topic :: Software Development",
		"Programming Language :: Python :: 3",
	],
    python_requires=">=3.0",
	version=VERSION,
	test_suite="tests",
	packages=setuptools.find_packages(),
)
