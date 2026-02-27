import { useState, useMemo } from 'react';
import { Button, Col, DatePicker, Form, Input, Row, Typography, message } from 'antd';
import type { Dayjs } from 'dayjs';

export default function GeneratedApp() {
  const [messageApi, contextHolder] = message.useMessage();

  const [firstName, setFirstName] = useState<string>('');
  const [lastName, setLastName] = useState<string>('');
  const [email, setEmail] = useState<string>('');
  const [phone, setPhone] = useState<string>('');
  const [dateOfBirth, setDateOfBirth] = useState<Dayjs | null>(null);
  const [address, setAddress] = useState<string>('');
  const [city, setCity] = useState<string>('');
  const [country, setCountry] = useState<string>('');
  const [postalCode, setPostalCode] = useState<string>('');
  const [isDraft, setIsDraft] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const isFormValid = useMemo(() => {
    return firstName.length > 0 && lastName.length > 0 && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }, [firstName, lastName, email]);

  const formCompleteness = useMemo(() => {
    const count = (firstName ? 1 : 0) + 
                  (lastName ? 1 : 0) + 
                  (email ? 1 : 0) + 
                  (phone ? 1 : 0) + 
                  (dateOfBirth ? 1 : 0) + 
                  (address ? 1 : 0) + 
                  (city ? 1 : 0) + 
                  (country ? 1 : 0) + 
                  (postalCode ? 1 : 0);
    return (count / 9) * 100;
  }, [firstName, lastName, email, phone, dateOfBirth, address, city, country, postalCode]);

  const updateFirstName = (event: React.ChangeEvent<HTMLInputElement>) => {
    setFirstName(event.target.value);
  };

  const updateLastName = (event: React.ChangeEvent<HTMLInputElement>) => {
    setLastName(event.target.value);
  };

  const updateEmail = (event: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(event.target.value);
  };

  const updatePhone = (event: React.ChangeEvent<HTMLInputElement>) => {
    setPhone(event.target.value);
  };

  const updateDateOfBirth = (date: Dayjs | null) => {
    setDateOfBirth(date);
  };

  const updateAddress = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setAddress(event.target.value);
  };

  const updateCity = (event: React.ChangeEvent<HTMLInputElement>) => {
    setCity(event.target.value);
  };

  const updateCountry = (event: React.ChangeEvent<HTMLInputElement>) => {
    setCountry(event.target.value);
  };

  const updatePostalCode = (event: React.ChangeEvent<HTMLInputElement>) => {
    setPostalCode(event.target.value);
  };

  const saveDraft = async () => {
    try {
      setIsDraft(true);
      await new Promise(resolve => setTimeout(resolve, 500));
      messageApi.success('Draft saved successfully');
    } catch {
      messageApi.error('Failed to save draft. Please try again.');
    }
  };

  const submitForm = async () => {
    if (!isFormValid) {
      messageApi.error('Failed to submit form. Please check all required fields and try again.');
      return;
    }

    setIsSubmitting(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      setIsDraft(false);
      messageApi.success('Personal details submitted successfully');
    } catch {
      messageApi.error('Failed to submit form. Please check all required fields and try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      {contextHolder}
      <div
        className="personal-details-page"
        style={{
          maxWidth: '1200px',
          margin: '0 auto',
          padding: '24px'
        }}
      >
        <Typography.Title level={1} style={{ marginBottom: '24px' }}>
          Personal Details
        </Typography.Title>
        <Form
          layout="vertical"
          size="large"
          style={{
            backgroundColor: '#ffffff',
            padding: '32px',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}
        >
          <div className="form-section" style={{ marginBottom: '32px' }}>
            <Typography.Title level={3} style={{ marginBottom: '16px' }}>
              Basic Information
            </Typography.Title>
            <Row gutter={16}>
              <Col xs={24} sm={12}>
                <Form.Item
                  label="First Name"
                  required
                  rules={[
                    {
                      required: true,
                      message: 'Please enter your first name'
                    }
                  ]}
                >
                  <Input
                    placeholder="Enter first name"
                    maxLength={50}
                    aria-label="First Name"
                    value={firstName}
                    onChange={updateFirstName}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12}>
                <Form.Item
                  label="Last Name"
                  required
                  rules={[
                    {
                      required: true,
                      message: 'Please enter your last name'
                    }
                  ]}
                >
                  <Input
                    placeholder="Enter last name"
                    maxLength={50}
                    aria-label="Last Name"
                    value={lastName}
                    onChange={updateLastName}
                  />
                </Form.Item>
              </Col>
            </Row>
            <Row gutter={16}>
              <Col xs={24} sm={12}>
                <Form.Item
                  label="Email"
                  required
                  rules={[
                    {
                      required: true,
                      message: 'Please enter your email'
                    },
                    {
                      type: 'email',
                      message: 'Please enter a valid email'
                    }
                  ]}
                >
                  <Input
                    placeholder="Enter email address"
                    type="email"
                    aria-label="Email"
                    value={email}
                    onChange={updateEmail}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12}>
                <Form.Item label="Phone" required={false}>
                  <Input
                    placeholder="Enter phone number"
                    aria-label="Phone"
                    value={phone}
                    onChange={updatePhone}
                  />
                </Form.Item>
              </Col>
            </Row>
            <Form.Item label="Date of Birth" required={false}>
              <DatePicker
                placeholder="Select date of birth"
                style={{ width: '100%' }}
                aria-label="Date of Birth"
                value={dateOfBirth}
                onChange={updateDateOfBirth}
              />
            </Form.Item>
          </div>

          <div className="form-section" style={{ marginBottom: '32px' }}>
            <Typography.Title level={3} style={{ marginBottom: '16px' }}>
              Address Information
            </Typography.Title>
            <Form.Item label="Address" required={false}>
              <Input.TextArea
                placeholder="Enter street address"
                rows={3}
                maxLength={200}
                aria-label="Address"
                value={address}
                onChange={updateAddress}
              />
            </Form.Item>
            <Row gutter={16}>
              <Col xs={24} sm={8}>
                <Form.Item label="City" required={false}>
                  <Input
                    placeholder="Enter city"
                    maxLength={100}
                    aria-label="City"
                    value={city}
                    onChange={updateCity}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} sm={8}>
                <Form.Item label="Country" required={false}>
                  <Input
                    placeholder="Enter country"
                    maxLength={100}
                    aria-label="Country"
                    value={country}
                    onChange={updateCountry}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} sm={8}>
                <Form.Item label="Postal Code" required={false}>
                  <Input
                    placeholder="Enter postal code"
                    maxLength={20}
                    aria-label="Postal Code"
                    value={postalCode}
                    onChange={updatePostalCode}
                  />
                </Form.Item>
              </Col>
            </Row>
          </div>

          <Row gutter={16} justify="end" style={{ marginTop: '32px' }}>
            <Col>
              <Button
                size="large"
                aria-label="Save Draft"
                onClick={saveDraft}
              >
                Save Draft
              </Button>
            </Col>
            <Col>
              <Button
                type="primary"
                size="large"
                disabled={!isFormValid}
                loading={isSubmitting}
                aria-label="Submit"
                onClick={submitForm}
              >
                Submit
              </Button>
            </Col>
          </Row>
        </Form>
      </div>
    </>
  );
}
