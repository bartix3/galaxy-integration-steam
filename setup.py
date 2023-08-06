from distutils.core import setup

setup(
    name="SuperPackageA",
    author="BaumherA, don-de-marco, et al",
    version="2.0",
    package_dir={'': 'src'},
    package_data={"steam_client": ["py.typed"], "local": ["py.typed"], "caches": ["py.typed"]},
    packages=["steam_network", "local"]
)