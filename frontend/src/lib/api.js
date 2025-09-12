import axios from "axios";

const isDev =
  typeof window !== "undefined" &&
  (location.hostname === "localhost" || location.hostname === "127.0.0.1");

const baseURL = isDev ? "http://127.0.0.1:5000" : "/api";

export const api = axios.create({
  baseURL,
  timeout: 10000
});
