import React from "react";
import { Modal, Form, Select, message } from "antd";
import api from "../../utils/api";

const { Option } = Select;
const CreateAdminModal = ({
  users,
  buckets,
  isModalVisible,
  setIsModalVisible,
}) => {
  const [form] = Form.useForm();

  const handleCreateAdmin = (values) => {
    const adminRequestData = {
      bucket_name: values.bucket,
      username: values.user,
      role:"ADMIN"
    };
    console.log("ADMIN REQUEST DATA", adminRequestData)
    api
      .post("/buckets/change_bucket_permissions", adminRequestData)
      .then((response) => {
        message.success("Admin created successfully");
      })
      .catch((error) => {
        message.error("Failed to create admin");
      });
  };
  const handleOk = () => {
    form
      .validateFields()
      .then((values) => {
        console.log(values);
        form.resetFields();
        handleCreateAdmin(values);
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
        title="Create Admin"
        visible={isModalVisible}
        onOk={handleOk}
        onCancel={handleCancel}
      >
        <Form form={form} layout="vertical" name="form_in_modal">
          <Form.Item
            name="bucket"
            label="Bucket"
            rules={[
              {
                message: "Please select the bucket !",
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
              placeholder="Select a Bucket"
              optionFilterProp="children"
              filterOption={(input, option) =>
                option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
              }
            >
              {buckets.slice(0, 5).map((bucket) => (
                <Option key={bucket}>{bucket}</Option>
              ))}
            </Select>
          </Form.Item>
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

export default CreateAdminModal;
