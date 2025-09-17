import axios from "axios";

const isLocalDev =
  typeof window !== "undefined" &&
  (window.location.hostname === "localhost" ||
   window.location.hostname === "127.0.0.1");

const baseURL = isLocalDev
  ? "https://temporarily-injured-terrace-cab.trycloudflare.com/api" 
  : "/api"; 

export const api = axios.create({
  baseURL,
  timeout: 10000,
  withCredentials: false,
});
