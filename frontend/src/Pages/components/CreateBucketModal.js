import React, { useState, useEffect } from "react";
import { Input, Modal, Space, Button, Form, Select, message } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import api from "../../utils/api";

const { Option } = Select;
const CreateBucketModal = ({
  isModalVisible,
  setIsModalVisible,
  handleAddNewBucket,
}) => {
  const [form] = Form.useForm();
  const [bucketTypes, setBucketTypes] = useState([]);

  useEffect(() => {
    api
      .get("/buckets/get_task_types")
      .then((response) => {
        console.log("Bucket Types", response.data);
        setBucketTypes(response.data.data);
      })
      .catch((error) => {
        message.error("Failed to get bucket types");
      });
  }, []);
  const handleCreateBucket = (values) => {
    console.log("Check Box Values", values);
    let tasksArray = [];
    values.tasks.forEach((task) => {
      tasksArray.push([task.taskName, task.bucketType]);
    });
    const bucketRequestData = {
      bucket_name: values.bucket_name,
      tasks: tasksArray,
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
          <Form.List name="tasks">
            {(fields, { add, remove }) => (
              <>
                {fields.map((field) => (
                  <Space
                    key={field.key}
                    style={{ display: "flex", marginBottom: 8 }}
                    align="baseline"
                  >
                    <Form.Item
                      {...field}
                      name={[field.name, "taskName"]}
                      fieldKey={[field.fieldKey, "taskName"]}
                      rules={[{ required: true, message: "Missing task name" }]}
                    >
                      <Input placeholder="Task Name" />
                    </Form.Item>
                    <Form.Item
                      {...field}
                      name={[field.name, "bucketType"]}
                      fieldKey={[field.fieldKey, "bucketType"]}
                      rules={[
                        { required: true, message: "Missing bucket type" },
                      ]}
                    >
                      <Select placeholder="Select a bucket type">
                        {bucketTypes.map((bucketType) => {
                          return (
                            <Select.Option value={bucketType}>
                              {bucketType}
                            </Select.Option>
                          );
                        })}
                      </Select>
                    </Form.Item>
                    <Button onClick={() => remove(field.name)}>Delete</Button>
                  </Space>
                ))}
                <Form.Item>
                  <Button
                    type="dashed"
                    onClick={() => add()}
                    block
                    icon={<PlusOutlined />}
                  >
                    Add Task
                  </Button>
                </Form.Item>
              </>
            )}
          </Form.List>
        </Form>
      </Modal>
    </div>
  );
};

export default CreateBucketModal;
