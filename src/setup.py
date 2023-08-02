from distutils.core import setup

setup(
    name="SuperPackageA",
    author="BaumherA, don-de-marco, et al",
    version="2.0",
    package_data={"steam_network": ["py.typed"], "local": ["py.typed"]},
    packages=["steam_network", "local"]
)