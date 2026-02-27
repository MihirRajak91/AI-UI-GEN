import React, { useCallback, useMemo, useState } from "react";
import {
  App,
  Button,
  Card,
  ConfigProvider,
  InputNumber,
  Space,
  Table,
  Typography,
  message,
  theme as antdTheme,
} from "antd";
import type { ColumnsType } from "antd/es/table";

type BmiCategory = "Underweight" | "Normal" | "Overweight";

type Person = {
  id: number;
  heightCm: number | null;
  weightKg: number | null;
  bmi: number | null;
  category: BmiCategory | null;
};

const PRIMARY_COLOR = "#22c55e";
const FONT_FAMILY =
  "Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif";
const BORDER_RADIUS = 8;

function calculatePeopleWithBmi(people: Person[]): Person[] {
  return people.map((p) => {
    const h = ((p.heightCm || 0) as number) / 100;
    const bmi = h > 0 ? ((p.weightKg || 0) as number) / (h * h) : null;
    const b = bmi === null ? null : Math.round(bmi * 10) / 10;
    const c =
      b === null
        ? null
        : b < 18.5
          ? "Underweight"
          : b < 25
            ? "Normal"
            : "Overweight";
    return { ...p, bmi: b, category: c };
  });
}

export default function GeneratedApp() {
  const [messageApi, messageContextHolder] = message.useMessage();

  const [people, setPeople] = useState<Person[]>([
    { id: 1, heightCm: 172, weightKg: 68, bmi: null, category: null },
    { id: 2, heightCm: 158, weightKg: 54, bmi: null, category: null },
    { id: 3, heightCm: 185, weightKg: 92, bmi: null, category: null },
    { id: 4, heightCm: 166, weightKg: 74, bmi: null, category: null },
  ]);

  const peopleWithBmi = useMemo(() => {
    // derived.peopleWithBmi
    return calculatePeopleWithBmi(people);
  }, [people]);

  const onChangeHeight = useCallback((id: number, value: number | null) => {
    setPeople((prev) =>
      prev.map((p) => (p.id === id ? { ...p, heightCm: value } : p))
    );
  }, []);

  const onChangeWeight = useCallback((id: number, value: number | null) => {
    setPeople((prev) =>
      prev.map((p) => (p.id === id ? { ...p, weightKg: value } : p))
    );
  }, []);

  const event_calc_bmi = useCallback(() => {
    // behaviour_ir.events.event_calc_bmi
    setPeople((prev) => {
      const next = calculatePeopleWithBmi(prev);
      return next;
    });
  }, []);

  const action_calc_bmi = useCallback(() => {
    // behaviour_ir.actions.action_calc_bmi -> emit_event(event_calc_bmi)
    try {
      event_calc_bmi();
      messageApi.success("BMI calculated for all four people.");
    } catch {
      messageApi.error(
        "Unable to calculate BMI. Please check height and weight values."
      );
    }
  }, [event_calc_bmi, messageApi]);

  const columns: ColumnsType<Person> = useMemo(
    () => [
      {
        title: "Person",
        dataIndex: "id",
        key: "id",
        width: 90,
        render: (id: number) => `Person ${id}`,
      },
      {
        title: "Height (cm)",
        dataIndex: "heightCm",
        key: "heightCm",
        width: 220,
        render: (_: unknown, record: Person) => (
          <InputNumber
            aria-label={`Height (cm) for Person ${record.id}`}
            min={0}
            max={300}
            precision={0}
            value={record.heightCm ?? null}
            onChange={(v) => onChangeHeight(record.id, v)}
            style={{ width: 160 }}
          />
        ),
      },
      {
        title: "Weight (kg)",
        dataIndex: "weightKg",
        key: "weightKg",
        width: 220,
        render: (_: unknown, record: Person) => (
          <InputNumber
            aria-label={`Weight (kg) for Person ${record.id}`}
            min={0}
            max={500}
            precision={0}
            value={record.weightKg ?? null}
            onChange={(v) => onChangeWeight(record.id, v)}
            style={{ width: 160 }}
          />
        ),
      },
      {
        title: "BMI",
        dataIndex: "bmi",
        key: "bmi",
        width: 120,
        render: (bmi: Person["bmi"]) => (bmi == null ? "—" : bmi.toFixed(1)),
      },
      {
        title: "Category",
        dataIndex: "category",
        key: "category",
        render: (category: Person["category"]) => category ?? "—",
      },
    ],
    [onChangeHeight, onChangeWeight]
  );

  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: PRIMARY_COLOR,
          fontFamily: FONT_FAMILY,
          borderRadius: BORDER_RADIUS,
        },
        algorithm: antdTheme.defaultAlgorithm,
      }}
    >
      <App>
        {messageContextHolder}
        <div
          style={{
            minHeight: "100vh",
            padding: 24,
            backgroundColor: "#87CEEB",
            display: "flex",
            flexDirection: "column",
            gap: 12,
          }}
        >
          <Card
            title="BMI Calculator (4 People)"
            bordered
            style={{ maxWidth: 980, margin: "0 auto", width: "100%" }}
            bodyStyle={{
              display: "flex",
              flexDirection: "column",
              gap: 12,
            }}
          >
            <Typography.Text strong style={{}}>
              Enter height and weight, then calculate BMI for each person.
            </Typography.Text>

            <Typography.Text type="secondary" style={{}}>
              BMI categories: Underweight (&lt; 18.5), Normal (18.5–24.9),
              Overweight (≥ 25).
            </Typography.Text>

            <Table<Person>
              rowKey="id"
              pagination={false}
              size="middle"
              dataSource={peopleWithBmi}
              columns={columns}
            />

            <Space style={{ display: "flex", justifyContent: "flex-start" }}>
              <Button
                type="primary"
                onClick={action_calc_bmi}
                aria-label="Calculate BMI"
                style={{ width: "fit-content" }}
              >
                Calculate BMI
              </Button>
            </Space>

            <Typography.Text
              type="secondary"
              style={{ display: "block", marginTop: 8 }}
            >
              Note: BMI is a screening tool and does not directly assess body
              fat or health.
            </Typography.Text>
          </Card>
        </div>
      </App>
    </ConfigProvider>
  );
}
