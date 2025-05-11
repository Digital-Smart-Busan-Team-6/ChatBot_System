def getNewPost(DataFrameBefore, DataFrameNew):
    newPost = DataFrameNew[~DataFrameNew.index.isin(DataFrameBefore.index)]

    return newPost

def getClosedPost(DataFrameBefore, DataFrameNew):
    closedPost = DataFrameBefore[~DataFrameBefore.index.isin(DataFrameNew.index)]

    return closedPost


