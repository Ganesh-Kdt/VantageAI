import axios from "axios";

const api = axios.create({ baseURL: "" }); // uses proxy to localhost:8000

export const analyzeCompany = (company, mode = "first_look", demo = false) =>
  api.post("/analyze", { company, mode, demo });

export const headToHead = (company_a, company_b, demo = false) =>
  api.post("/head-to-head", { company_a, company_b, demo });

export const generateDigest = (companies, demo = false) =>
  api.post("/digest", { companies, demo });

export const healthCheck = () => api.get("/health");
