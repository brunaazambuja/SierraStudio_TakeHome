import axios from 'axios';

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

export const fastAPIClient = axios.create({
  baseURL: FASTAPI_URL,
  timeout: 300000,
});
