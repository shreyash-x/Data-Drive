import { Button, Table, Select, Row, Col, message } from "antd";
import { useEffect, useState, useRef } from "react";
import CreateAdminModal from "./CreateAdminModal";
import CreateBucketModal from "./CreateBucketModal";
import api from "../../utils/api";

const { Option } = Select;

/**
 * Renders an admin table component.
 *
 * @param {Object[]} data - The data to be displayed in the table.
 * @param {Function} onUpdate - The function to be called when an update button is clicked.
 * @returns {JSX.Element} The rendered admin table component.
 */

const SuperAdminTable = () => {
  console.log("HEYYY HEYYY 222");
  const [data, setData] = useState([{}]);
  const [dataSource, setDataSource] = useState([]);
  const [users, setUsers] = useState([]);
  const [buckets, setBuckets] = useState([]);
  const [showCreateAdminModal, setShowCreateAdminModal] = useState(false);
  const [showCreateNewBucketModal, setShowCreateNewBucketModal] =
    useState(false);
  const prevDataRef = useRef();

  const fetchBucketAdmins = () => {
    api
      .get("/buckets/get_admin_buckets")
      .then((response) => {
        console.log(response.data);
        const newData = response.data.data.map((item) => {
          return {
            key: item.bucket_name,
            bucket_name: item.bucket_name,
            admin: item.admin,
          };
        });
        console.log("HEYYY HEYYY 111");
        setData(newData);
      })
      .catch((error) => {
        message.error("Failed to fetch buckets");
      });
  }

  useEffect(() => {
    console.log("Heyyy 333");
    fetchBucketAdmins();
  }, []);

  useEffect(() => {
    const prevData = prevDataRef.current;
    // Only update dataSource if data has changed
    if (JSON.stringify(prevData) !== JSON.stringify(data)) {
      setDataSource(data);
    }
    // Store current data in ref
    prevDataRef.current = data;
  }, [data]);

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

  const fetchBuckets = () => {
    api
      .get("/buckets/list_buckets")
      .then((response) => {
        console.log(response.data);
        setBuckets(response.data.data);
      })
      .catch((error) => {
        message.error("Failed to fetch buckets");
      });
  }

  useEffect(() => {
    fetchBuckets();
  }, []);

  const handleAddNewBucket = () => {
    setShowCreateNewBucketModal(true, () => fetchBuckets());
  };
  const handleAddNewAdmin = () => {
    setShowCreateAdminModal(true, () => fetchBucketAdmins());
  };
  const handleDeleteAccess = (record) => {
    console.log("handle delete");
  };

  const columns = [
    {
      title: "Bucket Name",
      dataIndex: "bucket_name",
      key: "bucket_name",
      align: "center",
      width: "20%",
    },
    {
      title: "Admin",
      dataIndex: "admin",
      key: "admin",
      align: "center",
      width: "20%",
    },
    {
      title: "Revoke Access",
      align: "center",
      key: "delete",
      render: (text, record) => (
        <Button
          type="primary"
          danger
          onClick={() => {
            handleDeleteAccess(record);
          }}
        >
          Remove Access
        </Button>
      ),
      width: "10%",
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
          <Button type="primary" onClick={handleAddNewBucket}>
            Add New Bucket
          </Button>
        </Col>
        <Col>
          <Button type="primary" onClick={handleAddNewAdmin}>
            Create Admin
          </Button>
        </Col>
      </Row>
      <Table dataSource={dataSource} columns={columns} />
      <CreateAdminModal
        users={users}
        buckets={buckets}
        isModalVisible={showCreateAdminModal}
        setIsModalVisible={setShowCreateAdminModal}
      />
      <CreateBucketModal
        isModalVisible={showCreateNewBucketModal}
        setIsModalVisible={setShowCreateNewBucketModal}
      />
    </div>
  );
};

export default SuperAdminTable;
