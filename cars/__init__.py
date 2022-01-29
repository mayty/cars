from pkg_resources import get_distribution, DistributionNotFound

try:
    __version__ = get_distribution("cars").version
except DistributionNotFound:
    __version__ = "0.0"
