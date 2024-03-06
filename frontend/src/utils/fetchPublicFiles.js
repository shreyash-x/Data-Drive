/**
 * Fetches user information and updates the path and folders state.
 * @param {function} setPath - The function to update the path state.
 * @param {function} setFolders - The function to update the folders state.
 * @returns {Promise<void>} - A promise that resolves when the user information is fetched and the state is updated.
 */
const fetchPublicFiles = async (setSharedPath, setToken) => {
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
    const path = pathname.slice(1);
    console.log("path", path)
    console.log("token", token)
    setSharedPath(path);
    setToken(token);
};

export default fetchPublicFiles;