import React from "react";
import axios from "axios";

export const getBucketFileFromPath = (path) => {
  //  split the path by "/"
  const pathArray = path.split("/");
  const bucket = pathArray[0];
  const file = pathArray.slice(1).join("/");
  return { bucket, file };
}
export const getMenuBuckets = async () => {
  try {
    const response = await axios.get("/api/menu_buckets");
    return response.data;
  } catch (error) {
    console.error(error);
  }
};
