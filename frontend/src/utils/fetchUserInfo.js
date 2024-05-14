import api from "./api";
import { getBucketFileFromPath } from "./getMenuBuckets";
/**
 * Fetches user information and updates the path and folders state.
 * @param {function} setPath - The function to update the path state.
 * @param {function} setFolders - The function to update the folders state.
 * @returns {Promise<void>} - A promise that resolves when the user information is fetched and the state is updated.
 */
/** 
 * useEffect(() => {
    const postData = {
      username: user.username,
    };
    api
      .post("/buckets/get_user_roles", postData)
      .then((response) => {
        const newData = {};
        const adminRole = response.data.data.find(
          (role) => role.role === "admin"
        );
        const superAdminRole = response.data.data.find(
          (role) => role.role === "superadmin"
        );
        response.data.data.forEach((role) => {
          newData[role.bucket_name] = role.role;
        });
        setRoles(newData);
        if (adminRole) {
          setShowAdminTab(true);
        }
        if (superAdminRole) {
          setShowSuperAdminTab(true);
        }
      })
      .catch((error) => {
        message.error("Failed to fetch user roles");
      });
  }, []);
*/
const fetchUserInfo = async (
  setCurrentBucket,
  setBucketAccessible,
  setPath,
  setSharedPath,
  setFolders,
  setUser,
  setIsSuperAdmin,
  setLogin,
  setRoles
) => {
  const url = new URL(window.location.href);
  const pathname = url.pathname;
  console.log("current location", pathname);
  api
    .get("/auth/user")
    .then((res) => {
      console.log("user details 111", res);
      setBucketAccessible(res.data.bucket_list);
      setRoles(res.data.roles);
      let bucket_name = res.data.bucket_name;
      if (pathname === "/home") {
        setPath(bucket_name);
        setCurrentBucket(bucket_name);
      } else {
        // remove the first character
        console.log("pathname", pathname.slice(1));
        const { bucketName, filePath } = getBucketFileFromPath(
          pathname.slice(1)
        );
        setPath(filePath);
        bucket_name = bucketName;
        setCurrentBucket(bucketName);
      }
      setSharedPath(bucket_name);
      setUser(res.data);
      setIsSuperAdmin(res.data.super_admin);
      const firstFolder = {
        id: bucket_name,
        name: bucket_name,
        isDir: true,
        isOpenable: true,
      };
      setFolders([firstFolder]);
      setLogin(true);
    })
    .catch((err) => {
      setPath(pathname.slice(1));
    });
};

export default fetchUserInfo;
