import { React, useState, useEffect } from "react";
import { Input, Modal, Form, Select, message } from "antd";
import api from "../../utils/api";

const { Option } = Select;
const PermissionsModal = ({
  currentBucket,
  isModalVisible,
  setIsModalVisible,
  handleAddNewBucket,
}) => {
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
  const [form] = Form.useForm();
  const handleCreateBucket = (values) => {
    const bucketRequestData = {
      bucket_name: values.bucket_name,
    };
    console.log("bucket REQUEST DATA", bucketRequestData);
    api
      .post("/buckets/create_bucket", bucketRequestData)
      .then((response) => {
        message.success("bucket created successfully");
      })
      .catch((error) => {
        message.error("Failed to create bucket");
      });
  };

  const handleOk = () => {
    form
      .validateFields()
      .then((values) => {
        console.log(values);
        form.resetFields();
        handleCreateBucket(values);
      })
      .catch((info) => {
        console.log("Validate Failed:", info);
      });
    setIsModalVisible(false);
  };

  const handleCancel = () => {
    setIsModalVisible(false);
  };

  return (
    <div style={{ margin: "10px" }}>
      <Modal
        title="Grant Permissions"
        visible={isModalVisible}
        onOk={handleOk}
        onCancel={handleCancel}
      >
        <Form form={form} layout="vertical" name="form_in_modal">
          <Form.Item
            name="user"
            label="User"
            rules={[
              {
                message: "Please select the user",
                validator: (_, value) => {
                  if (value) {
                    return Promise.resolve();
                  }
                  return Promise.reject();
                },
              },
            ]}
          >
            <Select
              showSearch
              placeholder="Select a user"
              optionFilterProp="children"
              filterOption={(input, option) =>
                option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
              }
            >
              {users.slice(0, 5).map((user) => (
                <Option key={user.username}>{user.username}</Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default PermissionsModal;
