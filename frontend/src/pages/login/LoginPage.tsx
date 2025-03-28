import { LockOutlined, UserOutlined } from '@ant-design/icons';
import { Button, Card, Form, Input, message } from 'antd';
import { useEffect } from 'react';
import { type LoginFormValues, useLogin } from '@/hooks/useLogin';
import styles from './login.module.css';

const formRules = {
  username: [{ required: true, message: '账号不能为空' }],
  password: [
    { required: true, message: '密码不能为空' },
    { min: 6, message: '密码至少需要6位' },
    { max: 20, message: '密码不能超过20位' },
    {
      pattern: /^(?=.*[A-Za-z])(?=.*\d).{6,}$/,
      message: '密码必须包含字母和数字',
    },
  ],
};

export default function LoginPage() {
  const { mutate: login, error, isPending } = useLogin();
  const [form] = Form.useForm<LoginFormValues>();

  useEffect(() => {
    if (error) {
      message.error(error.message);
    }
  }, [error]);

  const onFinish = (values: LoginFormValues) => {
    login(values);
  };

  return (
    <div className={styles.loginContainer}>
      <Card className={styles.loginCard}>
        <h1 className={styles.title}>欢迎登录</h1>
        <div className={styles.formContainer}>
          <Form form={form} onFinish={onFinish} layout="vertical" initialValues={{
            username: 'admin',
            password: 'admin123'
          }}>
            <Form.Item name="username" rules={formRules.username}>
              <Input
                prefix={<UserOutlined />}
                placeholder="用户名/手机号"
                disabled={isPending}
              />
            </Form.Item>

            <Form.Item name="password" rules={formRules.password}>
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="密码"
                disabled={isPending}
              />
            </Form.Item>

            <Button
              type="primary"
              htmlType="submit"
              loading={isPending}
              block
            >
              {isPending ? '登录中...' : '立即登录'}
            </Button>
          </Form>
        </div>
      </Card>
    </div>
  );
}
