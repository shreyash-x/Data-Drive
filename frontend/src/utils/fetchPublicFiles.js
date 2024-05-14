/**
 * Fetches user information and updates the path and folders state.
 * @param {function} setPath - The function to update the path state.
 * @param {function} setFolders - The function to update the folders state.
 * @returns {Promise<void>} - A promise that resolves when the user information is fetched and the state is updated.
 */
const fetchPublicFiles = async (setCurrentBucket, setSharedPath, setToken) => {
    // const url = new URL(window.location.href);
    // const pathname = url.pathname;
    // console.log("current location", pathname)
    // // remove the first character
    // console.log("pathname", pathname.slice(1))
    // setSharedPath(pathname.slice(1))

    // url is of form /path?token=token
    // extract the path and token from the url
    const url = new URL(window.location.href);
    const pathname = url.pathname;
    console.log("current location", pathname)
    // remove the first character
    const token = url.searchParams.get("token");
    const path = pathname.slice(8);

    // path is of format {bucket_name}/{path}
    const pathArray = path.split("/");
    const bucket = pathArray[0];
    const pathInBucket = pathArray.slice(1).join("/");
    console.log("bucket", bucket)
    console.log("path", pathInBucket)
    console.log("token", token)
    setSharedPath(pathInBucket);
    setToken(token);
    setCurrentBucket(bucket);
};

export default fetchPublicFiles;