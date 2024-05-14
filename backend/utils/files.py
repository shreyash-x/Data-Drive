
def getFilePath(filePath:str):
    pathParts = filePath.split('/')
    bucketName = pathParts[0]
    restOfThePath = "/".join(pathParts[1:])
    return bucketName, restOfThePath

class FileUtils():
    def __init__(self) -> None:
        pass 
    