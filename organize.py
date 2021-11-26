import glob
import sys
import re
from pathlib import Path
from shutil import SameFileError, copy2
import logging


# Configure path mapping
inputKeys = ["somePathPart", "name", "year", "fileName"]
outputKeys = ["year", "somePathPart", "name", "fileName"]


def validateInputKeysConfig():
    for key in inputKeys:
        assert re.match(
            r"^\w+$", key
        ), f"Error: invalid character in inputKeys (in key '{key}')"
        assert (
            inputKeys.count(key) == 1
        ), f"Error: duplicate key '{key}' in inputKeys"


def validateOutputKeysConfig():
    for key in outputKeys:
        assert re.match(
            r"^\w+$", key
        ), f"Error: invalid character in outputKeys (in key '{key}')"
        assert key in inputKeys, f"Error: '{key}' doesn't exist in inputKeys"


if __name__ == "__main__":
    try:
        validateInputKeysConfig()
        validateOutputKeysConfig()
    except AssertionError as e:
        print(e)
        print(
            "Configuration error: please check the path mapping and try again"
        )
        exit()


# Return [sourceDirectory, destinationDirectory]
def getRootsFromCommandLine():
    if len(sys.argv) != 3:
        print("Usage: python organize.py <source_folder> <destination_folder>")
        exit()
    return Path(sys.argv[1]).absolute(), Path(sys.argv[2]).absolute()


# Return a function to transform a path according to path mapping
def getTransformPathFunction(inputKeys, outputKeys):
    captureGroups = [rf"(?P<{key}>[^\\/]+)" for key in inputKeys]
    joinedCaptureGroups = r"\\".join(captureGroups)
    inputPathRegex = re.compile(rf"^\\?{joinedCaptureGroups}$")

    def transformFunction(relativePath):
        match = inputPathRegex.match(str(relativePath))
        parts = match.groupdict() if match else None
        if parts:
            return "/".join([parts[key] for key in outputKeys if key in parts])

    return transformFunction


# Copy a source file into destination
# Create the tree structure if needed
def copyFile(source, destination):
    if not isinstance(destination, Path):
        destination = Path(destination)
    if not destination.parent.exists():
        destination.parent.mkdir(parents=True)
    copy2(Path(source).absolute(), destination.absolute())


# Return absolute paths of all files in the root directory
def getAllFilesInDirectory(root):
    allItems = glob.glob(f"{root}/**", recursive=True)
    allItemsAsPath = [Path(item) for item in allItems]
    return [item.absolute() for item in allItemsAsPath if item.is_file()]


def main():
    logging.basicConfig(level=logging.INFO, filename="./log.txt", filemode="w")
    logger = logging.getLogger(__name__)

    transformPath = getTransformPathFunction(inputKeys, outputKeys)
    sourceDir, dstDir = getRootsFromCommandLine()
    files = getAllFilesInDirectory(sourceDir)

    fileCopiedCount = 0
    fileIgnoredCount = 0
    fileSkippedCount = 0
    copyErrorCount = 0

    for file in files:
        sourceRelativePath = file.relative_to(sourceDir)
        destinationRelativePath = transformPath(sourceRelativePath)

        if destinationRelativePath:
            sourceAbsolutePath = sourceDir.joinpath(sourceRelativePath)
            destinationAbsolutePath = dstDir.joinpath(destinationRelativePath)
            if not destinationAbsolutePath.exists():
                logger.info(
                    f"Copy {sourceAbsolutePath} to {destinationAbsolutePath}"
                )
                try:
                    copyFile(sourceAbsolutePath, destinationAbsolutePath)
                except (IOError, SameFileError) as e:
                    logger.error(f"Error copying {sourceAbsolutePath}: {e}")
                    print("E", end="")
                    copyErrorCount += 1
                else:
                    print("+", end="")
                    fileCopiedCount += 1
            else:
                logger.warning(
                    f"Skip file: {destinationAbsolutePath} already exists"
                )
                print("-", end="")
                fileSkippedCount += 1
        else:
            logger.warning(f"Ignore file: {file} doesn't match the pattern")
            print("!", end="")
            fileIgnoredCount += 1

    print(f"\n+ {fileCopiedCount} / {len(files)} copied")
    print(f"! {fileIgnoredCount} ignored (not matching)")
    print(f"- {fileSkippedCount} skipped (already exists)")
    print(f"E {copyErrorCount} failed (copy error)")
    print("\nSee log.txt for more information")
    print()


if __name__ == "__main__":
    main()
