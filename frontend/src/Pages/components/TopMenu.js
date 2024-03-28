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
  setPath,
  user,
}) => {

  return (
    <>
      <Menu
        style={{ marginBottom: "auto" }}
        onClick={handleMenuClick}
        selectedKeys={[activeTab]}
        mode="inline"
        className="custom-menu"
        items={[
          {
            label: "Home",
            key: "4",
            icon: <DesktopOutlined />,
            title: "Home",
            onClick: () => {
              setPath(user.username);
            },
          },
          {
            label: "Shared",
            key: "Shared",
            icon: <ShareAltOutlined />,
            title: "Shared",
            children: [
              {
                label: "Shared with me",
                key: "5",
                icon: <i className="icon icon-share"></i>,
                title: "Shared with me",
              },
              {
                label: "Shared by me",
                key: "6",
                icon: <i className="icon icon-share"></i>,
                title: "Shared by me",
              },
            ],
          },
          ...bucket_list.map((bucket) => {
            return {
              label: bucket,
              key: 7 + bucket_list.indexOf(bucket),
              icon: <i className="icon icon-share"></i>,
              title: bucket,
              onClick: () => {
                setPath(user.username);
              },
            };
          }),
        ]}
      />
      ;
    </>
  );
};

export default TopMenu;
