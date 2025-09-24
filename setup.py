"""
Setup script for Civic Eye - AI-powered Smart Civic Reporting Platform
"""

from setuptools import setup, find_packages
import os

# Read README file
readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
try:
    with open(readme_path, 'r', encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "AI-powered Smart Civic Reporting Platform"

# Read requirements
requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
try:
    with open(requirements_path, 'r', encoding='utf-8') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
except FileNotFoundError:
    requirements = [
        'flask>=3.0.0',
        'flask-cors>=4.0.0',
        'python-dotenv>=1.0.0',
        'pymongo[srv]>=4.8.0',
        'flask-jwt-extended>=4.6.0',
        'passlib[bcrypt]>=1.7.4',
        'pillow>=10.0.0',
        'transformers>=4.40.0',
        'torch>=2.0.0',
        'torchvision>=0.15.0',
        'scikit-learn>=1.3.0',
        'numpy>=1.24.0',
    ]

setup(
    name="civic-eye",
    version="1.0.0",
    author="Civic Eye Team",
    author_email="support@civiceye.com",
    description="AI-powered Smart Civic Reporting Platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/civiceye/civic-eye",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Framework :: Flask",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
        ],
        'production': [
            'gunicorn>=21.0.0',
            'redis>=4.5.0',
            'celery>=5.3.0',
        ],
        'monitoring': [
            'prometheus-client>=0.17.0',
            'sentry-sdk[flask]>=1.32.0',
        ]
    },
    entry_points={
        'console_scripts': [
            'civic-eye=main:main',
        ],
    },
    include_package_data=True,
    package_data={
        'civic_eye': [
            'templates/*.html',
            'static/css/*.css',
            'static/js/*.js',
            'static/images/*',
        ],
    },
    data_files=[
        ('config', ['.env.example']),
    ],
    project_urls={
        "Bug Reports": "https://github.com/civiceye/civic-eye/issues",
        "Documentation": "https://civiceye.readthedocs.io/",
        "Source": "https://github.com/civiceye/civic-eye",
    },
    keywords="civic reporting smart city ai machine learning flask mongodb",
    license="MIT",
    zip_safe=False,
)
