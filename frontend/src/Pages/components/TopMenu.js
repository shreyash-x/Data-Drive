import { Menu } from "antd";
import { DesktopOutlined, ShareAltOutlined } from "@ant-design/icons";
import axios from "axios";
import { useState, useEffect } from "react";
/**
 * Renders the top menu component.
 *
 * @param {Object} props - The component props.
 * @param {Function} props.handleMenuClick - The function to handle menu click events.
 * @param {string} props.activeTab - The currently active tab.
 * @returns {JSX.Element} The rendered top menu component.
 */
const TopMenu = ({
  handleMenuClick,
  bucket_list,
  activeTab,
  currentBucket,
  setPath,
  user,
}) => {
  const bucketKey =
    bucket_list.indexOf(currentBucket) !== -1
      ? bucket_list.indexOf(currentBucket) + 7
      : 4;

  return (
    <>
      <Menu
        style={{ marginBottom: "auto" }}
        onClick={handleMenuClick}
        selectedKeys={[activeTab, bucketKey.toString()]}
        mode="inline"
        className="custom-menu"
        items={[
          {
            label: "Home",
            key: "4",
            icon: <DesktopOutlined />,
            title: "Home",
            // onClick: () => {
            //   setPath(currentBucket);
            // },
          },
          ...bucket_list.map((bucket) => {
            return {
              label: bucket,
              key: 7 + bucket_list.indexOf(bucket),
              icon: <i className="icon icon-share"></i>,
              title: bucket,
              // onClick: () => {
              //   setPath(currentBucket);
              // },
            };
          }),
        ]}
      />
      ;
    </>
  );
};

export default TopMenu;
