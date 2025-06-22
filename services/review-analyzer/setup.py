from setuptools import setup, find_packages

setup(
    name="review-analyzer",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "fastapi>=0.68.0,<0.69.0",
        "uvicorn>=0.15.0,<0.16.0",
        "pydantic>=1.8.0,<2.0.0",
        "numpy>=1.21.0,<2.0.0",
        "scikit-learn>=1.0.0,<2.0.0",
        "nltk>=3.6.0,<4.0.0",
        "confluent-kafka>=1.8.2,<2.0.0",
        "python-multipart>=0.0.5,<0.1.0",
        "python-dotenv>=0.19.0,<0.20.0",
    ],
    python_requires=">=3.9",
)
