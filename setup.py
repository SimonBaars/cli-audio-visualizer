from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cli-audio-visualizer",
    version="1.0.0",
    author="CLI Audio Visualizer",
    description="Platform independent audio visualizer for CLI written in Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "numpy>=1.20.0",
        "rich>=13.0.0",
        "colorama>=0.4.0",
        "sounddevice>=0.4.0",
    ],
    entry_points={
        "console_scripts": [
            "audio-visualizer=audio_visualizer.main:main",
        ],
    },
)