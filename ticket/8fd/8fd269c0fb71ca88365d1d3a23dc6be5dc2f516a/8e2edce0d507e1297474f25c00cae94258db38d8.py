# -*- coding: utf-8 -*-
from setuptools import setup
import py2exe, glob, os
from py2exe.build_exe import py2exe as BuildExe
from twisted.plugin import getCache


class PluginCacheCollector(BuildExe):
    """
    This class pre-generates the plugin cache and includes it in the 
    library.zip file
    """
    def copy_extensions(self, extensions):
        BuildExe.copy_extensions(self, extensions)
        
        # Import the plugin packages, change this to your plugin packages
        from mypackage.plugins.io import io
        from mypackage.plugins.misc import misc
        mods = [ io, misc ]
        
        for m in mods:
            # Pre-gen the plugin cache
            getCache(m)
           
            # Build the cache file's path in the build collect dir and copy the cache files there
            f = os.path.join(*(m.__name__.split('.') + ["dropin.cache"]))
            full = os.path.join(self.collect_dir, f)
            self.copy_file(f, full)
            
            # Add the cache file path to the list of files to be added to the py2exe zip file
            self.compiled_files.append(f)


opts = {
    "py2exe": {
        "packages": [ "mypackage" ],
        "includes": [],
        "excludes": [],
        "dll_excludes": [],
        "dist_dir": "dist",
        "optimize": 2, # Use -OO when building (e.g. python -OO setup.py py2exe)
        "bundle_files": 1,
        "compressed": True,
    }
}

setup(
    console=[ "mymain.py" ],
    zipfile="library.zip",
    options=opts,
    data_files=[],
    cmdclass={"py2exe": PluginCacheCollector}, # <--------- add this
)


