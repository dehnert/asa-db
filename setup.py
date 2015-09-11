from distutils.core import setup

setup(
    name = "asa-db",
    version = "1.0.2015.09.11",
    packages = ["asadb"],
    install_requires = [
        # Server
        "django",
        "django-form-utils",
        "django-reversion",
        "django-filter",
        "pillow", # required for ImageField in FYSM
        # python-ldap is a C extension with various build dependencies
        # on Ubuntu, try apt-get build-dep python-ldap
        "python-ldap"
    ],
    extras_require = {
        'scriptsmitedu': ["flup", "MySQL-python"],
    }

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
