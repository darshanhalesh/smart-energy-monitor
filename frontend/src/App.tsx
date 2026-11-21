import { FormEvent, useEffect, useState } from "react";
import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  getAlerts,
  getDashboard,
  getDevices,
  getForecast,
  getHistory,
  isLoggedIn,
  login,
  logout,
  setRelay,
} from "./api";
import type {
  Alert,
  Dashboard,
  Device,
  ForecastItem,
  Reading,
} from "./types";


type HistoryPoint = {
  time: string;
  power: number;
};


export default function App() {
  const [loggedIn, setLoggedIn] = useState(isLoggedIn());

  function handleLogin() {
    setLoggedIn(true);
  }

  function handleLogout() {
    logout();
    setLoggedIn(false);
  }

  if (!loggedIn) {
    return <LoginPage onLogin={handleLogin} />;
  }

  return <DashboardPage onLogout={handleLogout} />;
}


function LoginPage({ onLogin }: { onLogin: () => void }) {
  const [email, setEmail] = useState("demo@smartenergy.local");
  const [password, setPassword] = useState("Demo123!");
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    try {
      await login(email, password);
      onLogin();
    } catch (error) {
      setError(getErrorMessage(error, "Login failed"));
    }
  }

  return (
    <main className="login">
      <form className="login-card" onSubmit={handleSubmit}>
        <h1>Smart Energy Monitor</h1>
        <p>Sign in to view the energy dashboard.</p>

        <input
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="Email"
        />

        <input
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          type="password"
          placeholder="Password"
        />

        <button type="submit">Login</button>

        {error && <div className="error">{error}</div>}
      </form>
    </main>
  );
}


function DashboardPage({ onLogout }: { onLogout: () => void }) {
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<number | null>(null);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [forecast, setForecast] = useState<ForecastItem[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    loadDevices();
  }, []);

  useEffect(() => {
    if (selectedDeviceId === null) {
      return;
    }

    loadDeviceData(selectedDeviceId);

    const timer = window.setInterval(() => {
      loadDeviceData(selectedDeviceId);
    }, 5000);

    return () => window.clearInterval(timer);
  }, [selectedDeviceId]);

  async function loadDevices() {
    try {
      const deviceList = await getDevices();
      setDevices(deviceList);

      if (deviceList.length > 0) {
        setSelectedDeviceId(deviceList[0].id);
      }
    } catch (error) {
      setError(getErrorMessage(error, "Could not load devices"));
    }
  }

  async function loadDeviceData(deviceId: number) {
    setError("");

    try {
      const dashboardData = await getDashboard(deviceId);
      const historyData = await getHistory(deviceId);
      const alertData = await getAlerts(deviceId);
      const forecastData = await getForecast(deviceId);

      setDashboard(dashboardData);
      setHistory(formatHistory(historyData));
      setAlerts(alertData);
      setForecast(forecastData.forecast);
    } catch (error) {
      setError(getErrorMessage(error, "Could not load data"));
    }
  }

  async function toggleRelay() {
    if (dashboard === null) {
      return;
    }

    const device = dashboard.device;
    const newRelayState = !device.relay_on;

    try {
      await setRelay(device.id, newRelayState);
      await loadDeviceData(device.id);
    } catch (error) {
      setError(getErrorMessage(error, "Could not change relay"));
    }
  }

  function handleDeviceChange(value: string) {
    setSelectedDeviceId(Number(value));
  }

  if (dashboard === null) {
    return (
      <main className="page">
        <PageHeader onLogout={onLogout} />
        {error ? <div className="error">{error}</div> : <p>Loading...</p>}
      </main>
    );
  }

  return (
    <main className="page">
      <PageHeader
        deviceName={dashboard.device.name}
        devices={devices}
        selectedDeviceId={selectedDeviceId}
        onDeviceChange={handleDeviceChange}
        onLogout={onLogout}
      />

      {error && <div className="error">{error}</div>}

      <MetricCards dashboard={dashboard} />
      <RelayControl dashboard={dashboard} onToggle={toggleRelay} />
      <PowerChart history={history} />

      <section className="two-columns">
        <AlertsPanel alerts={alerts} />
        <ForecastPanel forecast={forecast} />
      </section>
    </main>
  );
}


function PageHeader({
  deviceName,
  devices = [],
  selectedDeviceId = null,
  onDeviceChange,
  onLogout,
}: {
  deviceName?: string;
  devices?: Device[];
  selectedDeviceId?: number | null;
  onDeviceChange?: (value: string) => void;
  onLogout: () => void;
}) {
  return (
    <header>
      <div>
        <h1>Smart Energy Monitor</h1>
        {deviceName && <p>{deviceName}</p>}
      </div>

      <div className="header-actions">
        {onDeviceChange && (
          <select
            value={selectedDeviceId ?? ""}
            onChange={(event) => onDeviceChange(event.target.value)}
          >
            {devices.map((device) => (
              <option key={device.id} value={device.id}>
                {device.name}
              </option>
            ))}
          </select>
        )}

        <button className="secondary" onClick={onLogout}>
          Logout
        </button>
      </div>
    </header>
  );
}


function MetricCards({ dashboard }: { dashboard: Dashboard }) {
  return (
    <section className="cards">
      <MetricCard title="Power" value={`${Math.round(dashboard.latest.power)} W`} />
      <MetricCard title="Voltage" value={`${dashboard.latest.voltage.toFixed(1)} V`} />
      <MetricCard title="Current" value={`${dashboard.latest.current.toFixed(2)} A`} />
      <MetricCard title="Energy" value={`${dashboard.energy_kwh.toFixed(2)} kWh`} />
      <MetricCard title="Estimated cost" value={`${dashboard.estimated_cost.toFixed(2)} SAR`} />
      <MetricCard title="Power factor" value={dashboard.latest.power_factor.toFixed(2)} />
    </section>
  );
}


function MetricCard({ title, value }: { title: string; value: string }) {
  return (
    <div className="card">
      <span>{title}</span>
      <strong>{value}</strong>
    </div>
  );
}


function RelayControl({
  dashboard,
  onToggle,
}: {
  dashboard: Dashboard;
  onToggle: () => void;
}) {
  const relayOn = dashboard.device.relay_on;
  const statusText = relayOn ? "ON" : "OFF";
  const buttonText = relayOn ? "Turn OFF" : "Turn ON";
  const statusClass = relayOn ? "on" : "off";

  return (
    <section className="control">
      <div>
        <strong>Relay</strong>
        <span className={statusClass}> {statusText}</span>
      </div>

      <button onClick={onToggle}>{buttonText}</button>
    </section>
  );
}


function PowerChart({ history }: { history: HistoryPoint[] }) {
  return (
    <section className="panel">
      <h2>Power during the last 24 hours</h2>

      <div className="chart">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={history}>
            <XAxis dataKey="time" minTickGap={30} />
            <YAxis />
            <Tooltip />
            <Line
              type="monotone"
              dataKey="power"
              stroke="currentColor"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}


function AlertsPanel({ alerts }: { alerts: Alert[] }) {
  const visibleAlerts = alerts.slice(0, 5);

  return (
    <div className="panel">
      <h2>Alerts</h2>

      {visibleAlerts.length === 0 && <p>No alerts.</p>}

      {visibleAlerts.map((alert) => (
        <div className="alert" key={alert.id}>
          <strong>{alert.level}</strong>
          <span>{alert.message}</span>
        </div>
      ))}
    </div>
  );
}


function ForecastPanel({ forecast }: { forecast: ForecastItem[] }) {
  const visibleForecast = forecast.slice(0, 8);

  return (
    <div className="panel">
      <h2>Next 24 hours</h2>

      {visibleForecast.map((item) => (
        <div className="forecast" key={item.time}>
          <span>{formatHour(item.time)}</span>
          <strong>{Math.round(item.power)} W</strong>
        </div>
      ))}
    </div>
  );
}


function formatHistory(readings: Reading[]): HistoryPoint[] {
  return readings.map((reading) => {
    return {
      time: new Date(reading.timestamp).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
      power: Math.round(reading.power),
    };
  });
}


function formatHour(time: string): string {
  return new Date(time).toLocaleTimeString([], {
    hour: "2-digit",
  });
}


function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error) {
    return error.message;
  }

  return fallback;
}
