import React from "react";
import { Input, Modal, Form, Select, message } from "antd";
import api from "../../utils/api";

const { Option } = Select;
const CreateBucketModal = ({
  isModalVisible,
  setIsModalVisible,
  handleAddNewBucket
}) => {
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
        title="Create Bucket"
        visible={isModalVisible}
        onOk={handleOk}
        onCancel={handleCancel}
      >
        <Form form={form} layout="vertical" name="form_in_modal">
          <Form.Item
            name="bucket_name"
            rules={[
              {
                required: true,
                message: "Please input the name of the bucket!",
              },
            ]}
          >
            <Input placeholder="Bucket Name" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default CreateBucketModal;
