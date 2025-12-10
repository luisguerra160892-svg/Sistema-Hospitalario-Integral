from setuptools import setup, find_packages

setup(
    name="sistema-hospitalario",
    version="1.0.0",
    author="Sistema Imtegral Hospitalario",
    author_email="soporte@hospital.cu",
    description="Sistema integral de gestión hospitalaria",
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/luisguerra160892-svg/sistema-hospitalario",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        "Flask>=2.3.0",
        "Flask-SQLAlchemy>=3.0.0",
        "Flask-Migrate>=4.0.0",
        "Flask-Login>=0.6.0",
        "pandas>=2.0.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "hospital-system=main:main",
        ],
    },
)