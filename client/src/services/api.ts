import axios from 'axios';
import { API_URL } from '../helpers/constants';

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: false,
});

export default api;
