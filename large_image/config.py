import json
import logging
import os
import pathlib
import re
from typing import Any, Optional, Union, cast

from . import exceptions

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Default logger
fallbackLogger = logging.getLogger('large_image')
fallbackLogger.setLevel(logging.INFO)
fallbackLogHandler = logging.NullHandler()
fallbackLogHandler.setLevel(logging.NOTSET)
fallbackLogger.addHandler(fallbackLogHandler)

ConfigValues = {
    'logger': fallbackLogger,
    'logprint': fallbackLogger,

    # For tiles
    'cache_backend': None,  # 'python' or 'memcached'
    # 'python' cache can use 1/(val) of the available memory
    'cache_python_memory_portion': 32,
    # cache_memcached_url may be a list
    'cache_memcached_url': '127.0.0.1',
    'cache_memcached_username': None,
    'cache_memcached_password': None,

    # If set to False, the default will be to not cache tile sources.  This has
    # substantial performance penalties if sources are used multiple times, so
    # should only be set in singular dynamic environments such as experimental
    # notebooks.
    'cache_sources': True,

    # Generally, these keys are the form of "cache_<cacheName>_<key>"

    # For tilesources.  These are also limited by available file handles.
    # 'python' cache can use 1/(val) of the available memory based on a very
    # rough estimate of the amount of memory used by a tilesource
    'cache_tilesource_memory_portion': 16,
    # If >0, this is the maximum number of tilesources that will be cached
    'cache_tilesource_maximum': 0,

    'max_small_image_size': 4096,

    # Should ICC color correction be applied by default
    'icc_correction': True,

    # The maximum size of an annotation file that will be ingested into girder
    # via direct load
    'max_annotation_input_file_length': 1 * 1024 ** 3 if not HAS_PSUTIL else max(
        1 * 1024 ** 3, psutil.virtual_memory().total // 16),
}


def getConfig(key: Optional[str] = None,
              default: Optional[Union[str, bool, int, logging.Logger]] = None) -> Any:
    """
    Get the config dictionary or a value from the cache config settings.

    :param key: if None, return the config dictionary.  Otherwise, return the
        value of the key if it is set or the default value if it is not.
    :param default: a value to return if a key is requested and not set.
    :returns: either the config dictionary or the value of a key.
    """
    if key is None:
        return ConfigValues
    envKey = f'LARGE_IMAGE_{key.replace(".", "_").upper()}'
    if envKey in os.environ:
        value = os.environ[envKey]
        if value == '__default__':
            return default
        try:
            value = json.loads(value)
        except ValueError:
            pass
        return value
    return ConfigValues.get(key, default)


def getLogger(key: Optional[str] = None,
              default: Optional[logging.Logger] = None) -> logging.Logger:
    """
    Get a logger from the config.  Ensure that it is a valid logger.

    :param key: if None, return the 'logger'.
    :param default: a value to return if a key is requested and not set.
    :returns: a logger.
    """
    logger = cast(logging.Logger, getConfig(key or 'logger', default))
    if not isinstance(logger, logging.Logger):
        logger = fallbackLogger
    return logger


def setConfig(key: str, value: Optional[Union[str, bool, int, logging.Logger]]) -> None:
    """
    Set a value in the config settings.

    :param key: the key to set.
    :param value: the value to store in the key.
    """
    curConfig = getConfig()
    if curConfig.get(key) is not value:
        curConfig[key] = value


def _ignoreSourceNames(
        configKey: str, path: Union[str, pathlib.Path], default: Optional[str] = None) -> None:
    """
    Given a path, if it is an actual file and there is a setting
    "source_<configKey>_ignored_names", raise a TileSourceError if the path
    matches the ignore names setting regex in a case-insensitive search.

    :param configKey: key to use to fetch value from settings.
    :param path: the file path to check.
    :param default: a default ignore regex, or None for no default.
    """
    ignored_names = getConfig('source_%s_ignored_names' % configKey) or default
    if not ignored_names or not os.path.isfile(path):
        return None
    if re.search(ignored_names, os.path.basename(path), flags=re.IGNORECASE):
        raise exceptions.TileSourceError('File will not be opened by %s reader' % configKey)
