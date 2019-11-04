import os
import pathlib
import subprocess

import scandir

import regex


def getPaths(paths=[], includes=[], excludes=[], required=[], prefixes=[],
             extensions=[], unified_excludes=False, subfolders=True,
             case_sensitive=False, find_files=True, find_dirs=True, files=[],
             signal=None):
    """Find file/directory path under the root path that matching the terms given

    :param paths: 'list' directories to search for files
    :param includes: 'list' item will be valid if they contain any terms
        from this list
    :param excludes: 'list' item will not be valid if they contain any terms
        from this list
    :param required: 'list' item will only be valid if they all terms from
        this list
    :param prefixes: 'list' item will be valid if they start with any terms
        from this list
    :param extensions: 'list' item will be valid if they end with any terms
        from this list
    :param unified_excludes: 'bool' combines all exclude terms so that all
        must be valid for a match to be detected
    :param subfolders: 'bool' search will include all child directories
    :param case_sensitive: 'bool' Case sensitvity will be respected in
        determining if item is valid
    :param find_files: 'bool' gathers all valid file paths
    :param find_dirs: 'bool' gather all valid directory paths
    :param files: 'list' Use this given list, instead of searching them
        from the given paths
    :param signal: 'Signal' Emits all valid file paths as they are evaluated
    :return: 'list' matching file list
    """
    if isinstance(paths, str):
        paths = [paths]
    message = ''
    if not paths and not files:
        message = 'No valid paths or files given for file collection'
    elif paths:
        for path in paths:
            if not os.path.exists(path):
                if not message:
                    message = 'The given path does not exist:'
                message = '{}\n\t{}'.format(message, path)
    if message:
        return []
    paths = [os.path.normpath(p) for p in paths]

    fileList = []
    pathList = []
    if files:
        fileList = files

    # find all the files
    if not fileList:
        for path in paths:
            for root, dirs, files in scandir.walk(path):
                fileList.extend([pathlib.WindowsPath(os.path.join(root, f)) for f in files])
                pathList.extend([pathlib.WindowsPath(os.path.join(root, d)) for d in dirs])
                if not subfolders:
                    break

    # collect search list
    searchList = []
    if find_dirs:
        searchList.extend(pathList)
    if find_files:
        searchList.extend(fileList)
    searchList.sort()

    # precompile reg expressions to speed up operations
    regs = regex.precompile(includes=includes, excludes=excludes,
                            required=required, starts=prefixes, ends=extensions,
                            unified_excludes=unified_excludes,
                            case_sensitive=case_sensitive)
    includesREGs, excludesREGs, requiredREGs, prefixREGs, extensionREGs = regs

    # filter the search, exclusion, required and extension terms from the list
    results = []
    for f in searchList:
        valid = True
        # required
        for r in requiredREGs:
            if not r.search(f):
                valid = False
                break
        if not valid:
            continue
        # extensions
        for r in extensionREGs:
            if not r.search(f):
                valid = False
                break
        if not valid:
            continue
        # excludes
        for r in excludesREGs:
            if r.search(f):
                valid = False
                break
        if not valid:
            continue
        # prefix
        for r in prefixREGs:
            if not r.search(f.name):
                valid = False
                break
        if not valid:
            continue
        # includes
        for r in includesREGs:
            if not r.search(f):
                valid = False
                break
        if valid:
            if signal:
                signal.emit(f)
            results.append(f)
    return results


# ------------------------------------------------------------------------------
def delete_emptyDirs(paths=[]):
    if isinstance(paths, str):
        paths = [paths]
    # remove empty directories
    for path in paths:
        for folder in paths.getPaths(path, collectDirs=True, collectFiles=False):
            if not os.path.exists(folder) or paths.getPaths(folder, collectDirs=False):
                continue
            os.removedirs(folder)


# ------------------------------------------------------------------------------
def duplicate(source='', target='', force=False):
    '''
        duplicate a file/directory to the given destination
        Parameters:
            source : the files to copy
            target : the path to duplate the files
            force : overwrites existing files
        Return:
           the duplicated filePaths
    '''
    if not os.path.exists(source):
        print('Source path does not exist:\t'+source)
        return False

    results = []
    if os.path.isdir(source):
        sourceFiles = getPaths(source)
        targetFiles = [f.replace(source, target) for f in sourceFiles]
    else:
        sourceFiles = [source]
        targetFiles = [target]

    for i, source in enumerate(sourceFiles):
        target = targetFiles[i]
        # create the output path
        if not force and os.path.exists(target):
            print('file not copied, already exists: ' + target)
            continue
        if os.path.exists(target):
            subprocess.call(["attrib", "-R", target], creationflags = 0x08000000)
        try:
            shutil.copy2(source, target)
            results.append(target)
        except:
            print('failed to copy: {0}'.format(target))
    return results


# ------------------------------------------------------------------------------
def move(source='', target='', force=False):
    if not os.path.exists(source):
        print('Source path does not exist:\t' + source)
        return False

    results = []
    if os.path.isdir(source):
        sourceFiles = paths.getPaths(source)
        targetFiles = [f.replace(source, target) for f in sourceFiles]
    else:
        sourceFiles = [source]
        targetFiles = [target]

    for src, trg in zip(sourceFiles, targetFiles):
        if not duplicate(src, trg, force):
            results.append(False)
        os.remove(src)
        results.append(True)
    if False in results:
        return False
    return True