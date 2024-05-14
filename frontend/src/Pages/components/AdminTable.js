import { Button, Table, Select, Row, Col, message } from "antd";
import { useEffect, useState, useRef } from "react";
import { InputNumber } from "antd";
import GiveBucketPermissionModal from "./GiveBucketPermissionModal";
import CreateGroupModal from "./CreateGroupModal";
import api from "../../utils/api";
const { Option } = Select;

/**
 * Renders an admin table component.
 *
 * @param {Object[]} data - The data to be displayed in the table.
 * @param {Function} onUpdate - The function to be called when an update button is clicked.
 * @returns {JSX.Element} The rendered admin table component.
 */
const AdminTable = ({ data, onUpdate, currentBucket }) => {
  const getGroupsData = () => {
    const groups_data = [];
    for (let i = 0; i < data.length; i++) {
      for (let j = 0; j < data[i].access_groups.length; j++) {
        let group_name = data[i].access_groups[j];
        let permission = data[i].access_groups_permissions[j];
        let username = data[i].username;
        groups_data.push({ group_name, username, permission });
      }
    }
    console.log("GROUPS DATA", groups_data);
    return groups_data;
  };

  data = data.map((item, index) => {
    return {
      key: index,
      admin: item.admin,
      username: item.username,
      email: item.email,
      permission: item.permission,
      storage_quota: item.storage_quota,
      storage_used: item.storage_used,
      access_groups: item.access_groups,
      access_groups_permissions: item.access_groups_permissions,
    };
  });
  const [dataSource, setDataSource] = useState([]);
  const [groupsDataSource, setGroupsDataSource] = useState();
  const [changedEntries, setChangedEntries] = useState({});
  const [denominations, setDenominations] = useState({});
  const [showGivePermissionModal, setShowGivePermissionModal] = useState(false);
  const [showAddUserModal, setShowAddUserModal] = useState(false);
  const [showCreateGroupModal, setShowCreateGroupModal] = useState(false);
  const [users, setUsers] = useState([]);

 
  useEffect(() => {
    api
      .get("/auth/users")
      .then((response) => {
        setUsers(response.data);
      })
      .catch((error) => {
        message.error("Failed to fetch users");
      });
  }, []);

  const denominatioChange = {
    MB: {
      GB: 1024,
      MB: 1,
      TB: 1024 * 1024,
    },
    GB: {
      MB: 1 / 1024,
      GB: 1,
      TB: 1024,
    },
    TB: {
      MB: 1 / (1024 * 1024),
      TB: 1,
      GB: 1 / 1024,
    },
  };

  const prevDataRef = useRef();

  useEffect(() => {
    const prevData = prevDataRef.current;

    // Only update dataSource if data has changed
    if (JSON.stringify(prevData) !== JSON.stringify(data)) {
      setDataSource(data);
      setGroupsDataSource(getGroupsData());
    }

    // Store current data in ref
    prevDataRef.current = data;
  }, [data]);

  const handleUpdate = (record) => {
    onUpdate(record);
  };

  const handlePermissionChange = (value, record) => {
    const newData = [...dataSource];
    const index = newData.findIndex((item) => record.key === item.key);
    newData[index].permission = value;
    setDataSource(newData);
  };

  const handleQuotaChange = (value, record) => {
    const newData = [...dataSource];
    const index = newData.findIndex((item) => record.key === item.key);
    newData[index].storage_quota = value;
    setDataSource(newData);
  };
  function formatBytes(bytes) {
    if (bytes < 1024) return bytes + " B";
    else if (bytes < 1048576) return (bytes / 1024).toFixed(2) + " KB";
    else if (bytes < 1073741824) return (bytes / 1048576).toFixed(2) + " MB";
    else if (bytes < 1099511627776)
      return (bytes / 1073741824).toFixed(2) + " GB";
    else return (bytes / 1099511627776).toFixed(2) + " TB";
  }
  function formatInput(bytes) {
    if (bytes < 1024) return bytes;
    else if (bytes < 1048576) return (bytes / 1024).toFixed(2);
    else if (bytes < 1073741824) return (bytes / 1048576).toFixed(2);
    else if (bytes < 1099511627776) return (bytes / 1073741824).toFixed(2);
    else return (bytes / 1099511627776).toFixed(2);
  }
  useEffect(() => {
    const denominationdict = data.map((item, index) => {
      return {
        key: index,
        denomination: denomination(item.storage_used),
      };
    });
    setDenominations(denominationdict);
  }, [data]);
  function denomination(bytes) {
    if (bytes < 1024) return "B";
    else if (bytes < 1048576) return "KB";
    else if (bytes < 1073741824) return "MB";
    else if (bytes < 1099511627776) return "GB";
    else return "TB";
  }

  const mapPermissionValue = (value) => {
    switch (value) {
      case 0:
        return "None";
      case 1:
        return "Read";
      case 2:
        return "Write";
      default:
        return "None";
    }
  };
  const factors = {
    B: 1,
    KB: 1024,
    MB: 1024 * 1024,
    GB: 1024 * 1024 * 1024,
    TB: 1024 * 1024 * 1024 * 1024,
  };
  const columns = [
    // {
    //   title: "ROLE",
    //   dataIndex: "admin",
    //   key: "admin",
    //   align: "center",
    //   // render: (text, record) => (
    //   //   <Select
    //   //     defaultValue={mapPermissionValue(text)}
    //   //     style={{ width: 120 }}
    //   //     onChange={(value) => handlePermissionChange(value, record)}
    //   //   >
    //   //     <Option value={"USER"}>USER</Option>
    //   //     <Option value={"ADMIN"}>ADMIN</Option>
    //   //   </Select>
    //   // ),
    //   width: "5%",
    // },
    {
      title: "Username",
      dataIndex: "username",
      align: "center",
      key: "username",
      width: "10%",
    },
    {
      title: "Email",
      dataIndex: "email",
      align: "center",
      key: "email",
      width: "20%",
    },
    {
      title: "Permission",
      dataIndex: "permission",
      key: "permission",
      align: "center",
      render: (text, record) => (
        <Select
          defaultValue={mapPermissionValue(text)}
          style={{ width: 120 }}
          onChange={(value) => handlePermissionChange(value, record)}
        >
          <Option value={0}>None</Option>
          <Option value={1}>Read</Option>
          <Option value={2}>Write</Option>
        </Select>
      ),
      width: "5%",
    },
    {
      title: "Storage Quota",
      dataIndex: "storage_quota",
      key: "storage_quota",
      align: "center",
      render: (text, record) => (
        <div
          style={{
            display: "flex",
            justifyContent: "flex-start",
            alignItems: "center",
            gap: "10px",
          }}
        >
          <p
            style={{
              color: changedEntries[record.key] ? "#f50" : "#1677ff",
              width: "100px",
            }}
          >
            {formatBytes(text)}
          </p>
          <InputNumber
            min={1}
            defaultValue={formatInput(text)}
            style={{ width: "100px" }}
            onChange={(value) => {
              console.log(
                "denominations",
                denominations[record.key].denomination
              );
              console.log("denomiation text", denomination(text));
              console.log("factor", denominatioChange["MB"]["MB"]);
              let newSizeInBytes =
                value * factors[denominations[record.key].denomination];
              handleQuotaChange(newSizeInBytes, record);
              setChangedEntries({ ...changedEntries, [record.key]: true });
            }}
          />
          <Select
            defaultValue={denomination(text)}
            style={{ width: "100px" }}
            onChange={(value) => {
              console.log("current size", text);
              console.log("current denomiation", denomination(text));
              let newSizeInBytes;
              newSizeInBytes =
                text * denominatioChange[denomination(text)][value];
              handleQuotaChange(newSizeInBytes, record);
              setDenominations({ ...denominations, [record.key]: value });
              setChangedEntries({ ...changedEntries, [record.key]: true });
            }}
          >
            <Select.Option value="MB">MB</Select.Option>
            <Select.Option value="GB">GB</Select.Option>
            <Select.Option value="TB">TB</Select.Option>
          </Select>
        </div>
      ),
      width: "15%",
    },
    {
      title: "Storage Used",
      dataIndex: "storage_used",
      key: "storage_used",
      align: "center",
      render: (text) => formatBytes(text),
      width: "20%",
    },
    {
      title: "Update",
      key: "update",
      align: "center",
      render: (text, record) => (
        <Button type="primary" onClick={() => handleUpdate(record)}>
          Update
        </Button>
      ),
      width: "10%",
    },
  ];

  const groupColumns = [
    {
      title: "Group Name",
      align: "center",
      dataIndex: "group_name",
      key: "group_name",
      width: "20%",
    },
    {
      title: "Username",
      dataIndex: "username",
      align: "center",
      key: "username",
      width: "30%",
    },
    {
      title: "Permission",
      align: "center",
      dataIndex: "permission",
      key: "permission",
      align: "center",
      render: (text, record) => (
        <Select
          defaultValue={mapPermissionValue(text)}
          style={{ width: 120 }}
          // onChange={(value) => handlePermissionChange(value, record)}
        >
          <Option value={0}>None</Option>
          <Option value={1}>Read</Option>
          <Option value={2}>Write</Option>
        </Select>
      ),
      width: "10%",
    },
    // {
    //   title: "Members",
    //   dataIndex: "members",
    //   key: "members",
    //   render: members => members.map(member => (
    //     <Select defaultValue={member.permission} style={{ width: 120 }}>
    //       {/* onChange={value => handlePermissionChange(value, member.username)} */}
    //       <Option value="None">None</Option>
    //       <Option value="Read">Read</Option>
    //       <Option value="Write">Write</Option>
    //     </Select>
    //   ))
    // },
    {
      title: "Actions",
      align: "center",
      dataIndex: "actions",
      key: "actions",
      render: () => (
        <Button onClick={() => setShowAddUserModal(true)} type="primary">
          Remove from group
        </Button>
      ),
      width: "20%",
    },
  ];

  return (
    <div style={{ margin: "10px" }}>
      <Row
        justify="end"
        gutter={16}
        style={{ marginBottom: "20px", padding: "10px" }}
      >
        <Col>
          <Button
            type="primary"
            onClick={() => setShowGivePermissionModal(true)}
          >
            Give Permission
          </Button>
        </Col>
          <Col>
            <Button
              type="primary"
              onClick={() => setShowCreateGroupModal(true)}
            >
              Create Group
            </Button>
          </Col>
        
      </Row>
      <Table columns={columns} dataSource={dataSource} />
        <Table columns={groupColumns} dataSource={groupsDataSource} />
      <GiveBucketPermissionModal
        isModalVisible={showGivePermissionModal}
        setIsModalVisible={setShowGivePermissionModal}
        bucket={currentBucket}
        users={users}
      />
        <CreateGroupModal
          isModalVisible={showCreateGroupModal}
          setIsModalVisible={setShowCreateGroupModal}
          users={users}
          bucket={currentBucket}
        />
   </div>
  );
};

export default AdminTable;
