import type {
  Alert,
  Dashboard,
  Device,
  ForecastResponse,
  LoginResponse,
  Reading,
} from "./types";

const DEFAULT_API_URL = "http://localhost:8000";
const API_URL = import.meta.env.VITE_API_URL || DEFAULT_API_URL;

let token: string | null = localStorage.getItem("token");

export function isLoggedIn(): boolean {
  return token !== null;
}

export function logout(): void {
  token = null;
  localStorage.removeItem("token");
}

export async function login(email: string, password: string): Promise<void> {
  const form = new URLSearchParams();
  form.set("username", email);
  form.set("password", password);

  const response = await sendRequest("/api/auth/token", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: form,
  });

  const data = (await response.json()) as LoginResponse;
  token = data.access_token;
  localStorage.setItem("token", data.access_token);
}

export async function getDevices(): Promise<Device[]> {
  const response = await sendRequest("/api/devices");
  return (await response.json()) as Device[];
}

export async function getDashboard(deviceId: number): Promise<Dashboard> {
  const response = await sendRequest(`/api/dashboard/${deviceId}`);
  return (await response.json()) as Dashboard;
}

export async function getHistory(deviceId: number): Promise<Reading[]> {
  const path = `/api/telemetry/${deviceId}/history?hours=24`;
  const response = await sendRequest(path);
  return (await response.json()) as Reading[];
}

export async function getAlerts(deviceId: number): Promise<Alert[]> {
  const response = await sendRequest(`/api/alerts/${deviceId}`);
  return (await response.json()) as Alert[];
}

export async function getForecast(deviceId: number): Promise<ForecastResponse> {
  const response = await sendRequest(`/api/analytics/${deviceId}/forecast`);
  return (await response.json()) as ForecastResponse;
}

export async function setRelay(deviceId: number, relayOn: boolean): Promise<Device> {
  const response = await sendRequest(`/api/devices/${deviceId}/control`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ relay_on: relayOn }),
  });

  return (await response.json()) as Device;
}

async function sendRequest(
  path: string,
  options: RequestInit = {},
): Promise<Response> {
  const headers = new Headers(options.headers);

  if (token !== null) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(API_URL + path, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const message = await readErrorMessage(response);
    throw new Error(message);
  }

  return response;
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const data = await response.json();

    if (typeof data.detail === "string") {
      return data.detail;
    }
  } catch {
    return "Request failed";
  }

  return "Request failed";
}
