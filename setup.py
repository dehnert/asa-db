from distutils.core import setup

setup(
    name = "asa-db",
    version = "1.0.2014-10-18",
    packages = ["asadb"],
    install_requires = [
        # Server
        "django",
        "south",
        "django-form-utils",
        "django-reversion",
        "django-filter",
        # python-ldap is a C extension with various build dependencies
        # on Ubuntu, try apt-get build-dep python-ldap
        "python-ldap"
    ],

    author = "ASA DB team",
    author_email = "asa-db@mit.edu",
    url = "https://asa.scripts.mit.edu/trac/",
    description = 'MIT ASA student group database',
    license = "LICENSE.txt",

    keywords = ["mit", ],
    classifiers = [
        "Programming Language :: Python",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
    ],
)
