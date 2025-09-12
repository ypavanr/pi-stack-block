import axios from "axios";

const baseURL =  "http://127.0.0.1:5000";

export const api = axios.create({
  baseURL,
  timeout: 10000,
  withCredentials: false
});
