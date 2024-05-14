import React from "react";
import { Modal, Form, Select, message } from "antd";
import api from "../../utils/api";

const { Option } = Select;
const GiveBucketPermissionModal = ({
  users,
  bucket,
  isModalVisible,
  setIsModalVisible,
}) => {
  const [form] = Form.useForm();

  const handleGivePermission = (values) => {
    const requestData = {
      bucket_name: bucket,
      username: values.user,
      permission: values.permission,
      role:"USER"
    };
    console.log("USER Request Permission DATA", requestData)
    api
      .post("/buckets/change_bucket_permissions", requestData)
      .then((response) => {
        message.success("Permissions given successfully");
      })
      .catch((error) => {
        message.error("Failed to give permissions");
      });
  };
  const handleOk = () => {
    form
      .validateFields()
      .then((values) => {
        console.log(values);
        form.resetFields();
        handleGivePermission(values);
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
        title="Give Permissions to"
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
              {users.map((user) => (
                <Option key={user.username}>{user.username}</Option>
              ))}
            </Select>
          </Form.Item>
            <Form.Item
                name="permission"
                label="Permission"
                rules={[
                {
                    message: "Please select the permission",
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
                placeholder="Select a permission"
                optionFilterProp="children"
                filterOption={(input, option) =>
                    option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
                }
                >
                <Option key="READ">READ</Option>
                <Option key="WRITE">WRITE</Option>
                </Select>
            </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default GiveBucketPermissionModal;
