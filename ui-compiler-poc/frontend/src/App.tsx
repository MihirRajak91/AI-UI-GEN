import { useState, useMemo } from 'react';
import type { CSSProperties } from 'react';
import {
  Card,
  Form,
  InputNumber,
  Button,
  Alert,
  Divider,
  Typography,
  ConfigProvider,
} from 'antd';
import { CheckCircleOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

interface FieldErrors {
  subject1?: string | null;
  subject2?: string | null;
  subject3?: string | null;
  subject4?: string | null;
  subject5?: string | null;
}

type MessageType = 'success' | 'error' | null;

export default function GeneratedApp() {
  const [subjectMarks, setSubjectMarks] = useState<number[]>([85, 90, 78, 92, 88]);
  const [isCalculating, setIsCalculating] = useState<boolean>(false);
  const [gpaResult, setGpaResult] = useState<number | null>(null);
  const [messageType, setMessageType] = useState<MessageType>(null);
  const [messageText, setMessageText] = useState<string>('');
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  const allMarksValid = useMemo(
    () => subjectMarks.every((m) => typeof m === 'number' && !isNaN(m) && m >= 0 && m <= 100),
    [subjectMarks]
  );

  const computedGPA = useMemo(
    () => subjectMarks.reduce((sum, m) => sum + m, 0) / 5,
    [subjectMarks]
  );

  const validateMark = (value: number | null | undefined): boolean => {
    if (value === null || value === undefined || isNaN(value)) return false;
    return value >= 0 && value <= 100;
  };

  const handleMarkChange = (index: number, value: number | null) => {
    const parsed = value !== null && value !== undefined ? value : NaN;
    const isValid = !isNaN(parsed) && parsed >= 0 && parsed <= 100;
    const subjectKey = `subject${index + 1}` as keyof FieldErrors;
    const subjectLabel = `Subject ${index + 1}`;

    const newMarks = [...subjectMarks];
    newMarks[index] = parsed;
    setSubjectMarks(newMarks);

    setFieldErrors((prev) => ({
      ...prev,
      [subjectKey]: isValid
        ? null
        : `${subjectLabel}: Enter a valid number between 0 and 100`,
    }));

    setGpaResult(null);
    setMessageType(null);
    setMessageText('');
  };

  const handleCalculateGPA = () => {
    const subjectLabels = ['Subject 1', 'Subject 2', 'Subject 3', 'Subject 4', 'Subject 5'];
    const newErrors: FieldErrors = {};
    const invalidMessages: string[] = [];

    subjectMarks.forEach((mark, i) => {
      const subjectKey = `subject${i + 1}` as keyof FieldErrors;
      if (!validateMark(mark)) {
        const msg = `${subjectLabels[i]}: Must be a number between 0 and 100`;
        newErrors[subjectKey] = msg;
        invalidMessages.push(msg);
      } else {
        newErrors[subjectKey] = null;
      }
    });

    setFieldErrors(newErrors);

    if (invalidMessages.length > 0) {
      setMessageType('error');
      setMessageText(invalidMessages.join('; '));
      setGpaResult(null);
      return;
    }

    setIsCalculating(true);
    setTimeout(() => {
      const result = computedGPA;
      setGpaResult(result);
      setIsCalculating(false);
      setMessageType('success');
      setMessageText('GPA calculated successfully');
    }, 300);
  };

  const pageWrapperStyle: CSSProperties = {
    minHeight: '100vh',
    width: '100%',
    backgroundColor: '#fef9c3',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '24px 16px',
    boxSizing: 'border-box',
    overflowX: 'hidden',
  };

  const cardStyle: CSSProperties = {
    width: '100%',
    maxWidth: '520px',
    backgroundColor: '#ffffff',
    borderRadius: '12px',
    boxShadow: '0 4px 24px rgba(0,0,0,0.10)',
  };

  const titleStyle: CSSProperties = {
    color: '#0369a1',
    textAlign: 'center',
    marginBottom: '8px',
    fontSize: '28px',
    fontWeight: 700,
  };

  const subtitleStyle: CSSProperties = {
    display: 'block',
    textAlign: 'center',
    marginBottom: '28px',
    color: '#64748b',
    fontSize: '14px',
  };

  const inputStyle: CSSProperties = {
    width: '100%',
    borderRadius: '8px',
    transition: 'border-color 200ms ease',
  };

  const buttonStyle: CSSProperties = {
    backgroundColor: '#22c55e',
    borderColor: '#16a34a',
    color: '#ffffff',
    height: '48px',
    fontSize: '16px',
    fontWeight: 600,
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'background-color 200ms ease, transform 150ms ease',
    width: '100%',
  };

  const feedbackContainerStyle: CSSProperties = {
    marginTop: '16px',
    minHeight: '40px',
    transition: 'opacity 200ms ease',
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  };

  const resultContainerStyle: CSSProperties = {
    marginTop: '24px',
    display: gpaResult !== null ? 'block' : 'none',
    transition: 'opacity 250ms ease',
  };

  const resultLabelStyle: CSSProperties = {
    display: 'block',
    textAlign: 'center',
    fontSize: '14px',
    color: '#64748b',
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
    marginBottom: '4px',
  };

  const resultValueStyle: CSSProperties = {
    textAlign: 'center',
    color: '#0ea5e9',
    fontSize: '56px',
    fontWeight: 800,
    margin: '0',
    lineHeight: 1.1,
  };

  const resultSubtextStyle: CSSProperties = {
    display: 'block',
    textAlign: 'center',
    fontSize: '13px',
    color: '#94a3b8',
    marginTop: '4px',
  };

  const subjectConfigs = [
    { label: 'Subject 1', id: 'subject1Input', ariaLabel: 'Subject 1 mark input label', errorKey: 'subject1' as keyof FieldErrors, index: 0 },
    { label: 'Subject 2', id: 'subject2Input', ariaLabel: 'Subject 2 mark input label', errorKey: 'subject2' as keyof FieldErrors, index: 1 },
    { label: 'Subject 3', id: 'subject3Input', ariaLabel: 'Subject 3 mark input label', errorKey: 'subject3' as keyof FieldErrors, index: 2 },
    { label: 'Subject 4', id: 'subject4Input', ariaLabel: 'Subject 4 mark input label', errorKey: 'subject4' as keyof FieldErrors, index: 3 },
    { label: 'Subject 5', id: 'subject5Input', ariaLabel: 'Subject 5 mark input label', errorKey: 'subject5' as keyof FieldErrors, index: 4 },
  ];

  const gpaDisplay =
    gpaResult !== null && !isNaN(gpaResult) ? gpaResult.toFixed(2) : null;

  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#0ea5e9',
          fontFamily: 'Inter, system-ui, sans-serif',
          borderRadius: 8,
        },
      }}
    >
      <div role="main" style={pageWrapperStyle}>
        <Card
          aria-label="GPA Calculator Form"
          style={cardStyle}
          styles={{ body: { padding: '32px' } }}
        >
          <Title level={2} style={titleStyle} aria-label="GPA Calculator">
            GPA Calculator
          </Title>

          <Text type="secondary" style={subtitleStyle}>
            Enter marks for 5 subjects (0–100) to calculate your GPA
          </Text>

          <Form layout="vertical" aria-label="GPA calculation form" style={{ width: '100%' }}>
            {subjectConfigs.map(({ label, id, ariaLabel, errorKey, index }) => {
              const errorMsg = fieldErrors[errorKey];
              const hasError = !!errorMsg;
              const markValue = subjectMarks[index];
              const safeValue = typeof markValue === 'number' && !isNaN(markValue) ? markValue : null;

              return (
                <Form.Item
                  key={id}
                  label={label}
                  htmlFor={id}
                  validateStatus={hasError ? 'error' : ''}
                  help={errorMsg || ''}
                  style={{ marginBottom: index === 4 ? '24px' : '16px' }}
                >
                  <InputNumber
                    id={id}
                    aria-label={ariaLabel}
                    placeholder="Enter mark (0-100)"
                    min={0}
                    max={100}
                    step={1}
                    value={safeValue}
                    onChange={(val) => handleMarkChange(index, val)}
                    style={inputStyle}
                  />
                </Form.Item>
              );
            })}

            <Form.Item style={{ marginBottom: 0 }}>
              <Button
                type="primary"
                htmlType="submit"
                aria-label="Calculate GPA from entered subject marks"
                loading={isCalculating}
                block
                icon={<CheckCircleOutlined />}
                style={buttonStyle}
                onClick={(e) => {
                  e.preventDefault();
                  if (!isCalculating) {
                    handleCalculateGPA();
                  }
                }}
                disabled={!allMarksValid && Object.keys(fieldErrors).length === 0 ? false : false}
              >
                Calculate GPA
              </Button>
            </Form.Item>
          </Form>

          <div
            role="alert"
            aria-live="polite"
            aria-atomic="true"
            style={feedbackContainerStyle}
          >
            {messageType === 'success' && messageText && (
              <Alert
                type="success"
                message={messageText}
                showIcon
                aria-label="Success notification"
                style={{ borderRadius: '8px' }}
              />
            )}
            {messageType === 'error' && messageText && (
              <Alert
                type="error"
                message={messageText}
                showIcon
                aria-label="Error notification"
                style={{ borderRadius: '8px' }}
              />
            )}
          </div>

          <div
            aria-label="GPA result display area"
            aria-live="polite"
            style={resultContainerStyle}
          >
            <Divider style={{ margin: '0 0 16px 0' }} />
            <Text strong style={resultLabelStyle}>
              Your GPA
            </Text>
            <Title
              level={1}
              aria-label="Calculated GPA value"
              style={resultValueStyle}
            >
              {gpaDisplay}
            </Title>
            <Text type="secondary" style={resultSubtextStyle}>
              out of 100
            </Text>
          </div>
        </Card>
      </div>
    </ConfigProvider>
  );
}
