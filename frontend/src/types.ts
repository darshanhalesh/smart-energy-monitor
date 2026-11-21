export type Device = {
  id: number;
  name: string;
  tariff: number;
  relay_on: boolean;
};

export type Reading = {
  id: number;
  timestamp: string;
  voltage: number;
  current: number;
  power: number;
  energy_kwh: number;
  frequency: number;
  power_factor: number;
  relay_on: boolean;
};

export type Alert = {
  id: number;
  created_at: string;
  message: string;
  level: string;
  acknowledged: boolean;
};

export type ForecastItem = {
  time: string;
  power: number;
};

export type ForecastResponse = {
  forecast: ForecastItem[];
};

export type Dashboard = {
  device: Device;
  latest: Reading;
  energy_kwh: number;
  estimated_cost: number;
  updated_at: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
};
