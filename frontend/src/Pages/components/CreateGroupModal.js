import React from "react";
import { Input, Modal, Form, Select, message } from "antd";
import api from "../../utils/api";

const { Option } = Select;
const CreateGroupModal = ({
    users,
    bucket,
    isModalVisible,
    setIsModalVisible,
}) => {
    const [form] = Form.useForm();
    const [bucketTasks, setBucketTasks] = React.useState([]);

    React.useEffect(() => {
        const data = {
            bucket_name: bucket,
        };
        api
            .post("/buckets/get_bucket_tasks", data)
            .then((response) => {
                setBucketTasks(response.data.data);
            })
            .catch((error) => {
                console.log("Failed to fetch bucket tasks");
            });
    }, [bucket]);

    const handleCreateGroup = (values) => {
        const groupRequestData = {
            group_name: values.group_name,
            bucket_name: bucket,
            usernames: values.usernames,  // Changed from username to usernames
            permission: values.permission,
            task_name: values.task_name,
        };
        console.log("Group REQUEST DATA", groupRequestData);
        api
            .post("/buckets/change_group_permissions", groupRequestData)
            .then((response) => {
                message.success("Group created successfully");
            })
            .catch((error) => {
                message.error("Failed to create group");
            });
    };

    const handleOk = () => {
        form
            .validateFields()
            .then((values) => {
                console.log(values);
                form.resetFields();
                handleCreateGroup(values);
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
                title="Create Group"
                visible={isModalVisible}
                onOk={handleOk}
                onCancel={handleCancel}
            >
                <Form form={form} layout="vertical" name="form_in_modal">
                    <Form.Item
                        name="group_name"
                        label="Group Name"
                        rules={[{
                            required: true,
                            message: "Please input the group name",
                        }]}
                    >
                        <Input placeholder="Enter group name" />
                    </Form.Item>
                    <Form.Item
                        name="task_name"
                        label="Task"
                        rules={[{
                            required: true,
                            message: "Please select the Task to assign the group to",
                        }]}
                    >
                        <Select
                            showSearch
                            placeholder="Select a Task"
                            optionFilterProp="children"
                            filterOption={(input, option) =>
                                option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
                            }
                        >
                            {bucketTasks.map((task) => (
                                <Option key={task.task_name} value={task.task_name}>{task.task_name}</Option>
                            ))}
                        </Select>
                    </Form.Item>
                    <Form.Item
                        name="usernames"
                        label="Users"
                        rules={[{
                            required: true,
                            message: "Please select at least one user",
                        }]}
                    >
                        <Select
                            mode="multiple"
                            showSearch
                            placeholder="Select users"
                            optionFilterProp="children"
                            filterOption={(input, option) =>
                                option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
                            }
                        >
                            {users.map((user) => (
                                <Option key={user.username} value={user.username}>{user.username}</Option>
                            ))}
                        </Select>
                    </Form.Item>
                    <Form.Item
                        name="permission"
                        label="Permission"
                        rules={[{
                            required: true,
                            message: "Please select the permission",
                        }]}
                    >
                        <Select
                            showSearch
                            placeholder="Select a permission"
                            optionFilterProp="children"
                            filterOption={(input, option) =>
                                option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
                            }
                        >
                            <Option value="READ">READ</Option>
                            <Option value="WRITE">WRITE</Option>
                        </Select>
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    );
};

export default CreateGroupModal;
